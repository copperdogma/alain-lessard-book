from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from pypdf import PdfReader
import reportlab
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Image as DrawingImage, Line, Rect, String
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "outreach" / "reunion-flyer.json"
VISION_DECODER = Path(__file__).with_name("decode_qr_vision.swift")
FONT_REGULAR = "AlainFlyerVera"
FONT_BOLD = "AlainFlyerVeraBold"
EXPECTED_SCHEMA = "alain_reunion_flyer_v1"
LETTER_POINTS = (612.0, 792.0)
PRINT_PREVIEW_PIXELS = (2550, 3300)
PHONE_PIXELS = (1080, 1920)


class FlyerError(RuntimeError):
    pass


@dataclass(frozen=True)
class FlyerCatalog:
    manifest_path: Path
    root: Path
    data: dict[str, Any]

    def path(self, group: str, key: str) -> Path:
        return self.root / str(self.data[group][key])

    @property
    def canonical_url(self) -> str:
        return str(self.data["publication"]["canonical_url"])

    @property
    def display_url(self) -> str:
        return str(self.data["publication"]["display_url"])

    @property
    def cover_path(self) -> Path:
        return self.root / str(self.data["artwork"]["cover_source_path"])


@dataclass
class ValidationResult:
    errors: list[str]
    metrics: dict[str, Any]

    @property
    def ok(self) -> bool:
        return not self.errors


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FlyerError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    require(isinstance(value, dict), f"{key} must be an object")
    return value


def _required_strings(data: dict[str, Any], keys: Iterable[str], label: str) -> None:
    for key in keys:
        value = data.get(key)
        require(isinstance(value, str) and value.strip(), f"{label}.{key} must be a non-empty string")


def hex_rgb(value: str) -> tuple[int, int, int]:
    require(isinstance(value, str) and len(value) == 7 and value.startswith("#"), f"invalid hex color: {value!r}")
    try:
        return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))  # type: ignore[return-value]
    except ValueError as exc:
        raise FlyerError(f"invalid hex color: {value!r}") from exc


def relative_luminance(value: str) -> float:
    channels = []
    for channel in hex_rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first: str, second: str) -> float:
    high, low = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def validate_manifest_data(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == EXPECTED_SCHEMA, f"schema_version must be {EXPECTED_SCHEMA}")
    publication = _required_mapping(data, "publication")
    copy = _required_mapping(data, "copy")
    artwork = _required_mapping(data, "artwork")
    palette = _required_mapping(data, "palette")
    typography = _required_mapping(data, "typography")
    qr = _required_mapping(data, "qr")
    surfaces = _required_mapping(data, "surfaces")
    outputs = _required_mapping(data, "outputs")
    temporary_outputs = _required_mapping(data, "temporary_outputs")
    constraints = _required_mapping(data, "constraints")

    _required_strings(publication, ("display_title", "formal_subtitle", "canonical_url", "display_url"), "publication")
    _required_strings(copy, ("eyebrow", "headline", "camera_instruction", "family_heading", "phone_offer"), "copy")
    actions = copy.get("actions")
    require(isinstance(actions, list) and len(actions) == 4, "copy.actions must contain exactly four actions")
    require(all(isinstance(value, str) and value.strip() for value in actions), "copy.actions entries must be non-empty strings")
    names = data.get("family_names")
    require(isinstance(names, list) and len(names) >= 8, "family_names must contain at least eight source-backed names")
    require(all(isinstance(value, str) and value.strip() for value in names), "family_names entries must be non-empty strings")

    _required_strings(artwork, ("cover_source_path", "cover_expected_sha256"), "artwork")
    cover_path = Path(str(artwork["cover_source_path"]))
    require(not cover_path.is_absolute() and cover_path.parts[:2] == ("input", "doc-web-html"), "artwork.cover_source_path must live under input/doc-web-html")
    cover_hash = str(artwork["cover_expected_sha256"]).lower()
    require(len(cover_hash) == 64 and all(character in "0123456789abcdef" for character in cover_hash), "artwork.cover_expected_sha256 must be a lowercase SHA-256")
    require(int(artwork.get("cover_expected_width_pixels", 0)) > 0, "artwork cover width must be positive")
    require(int(artwork.get("cover_expected_height_pixels", 0)) > 0, "artwork cover height must be positive")
    cover_height = float(artwork.get("letter_height_points", 0))
    require(180 <= cover_height <= 300, "artwork letter height must remain between 180 and 300 points")
    require(abs(cover_height - float(qr.get("print_size_points", 0))) <= 0.001, "artwork letter height must equal the print QR size")
    require(260 <= float(artwork.get("letter_row_y_points", 0)) <= 280, "artwork letter row baseline must remain between 260 and 280 points")
    require(float(artwork.get("letter_gap_to_qr_points", 0)) >= 18, "artwork gap to QR must be at least 18 points")
    require(int(artwork.get("minimum_effective_ppi", 0)) >= 300, "artwork minimum effective resolution must be at least 300 ppi")

    parsed = urlparse(str(publication["canonical_url"]))
    require(parsed.scheme == "https" and bool(parsed.netloc), "publication.canonical_url must be an HTTPS URL")
    require(parsed.path == "/" and not parsed.query and not parsed.fragment, "canonical QR destination must be the stable homepage")
    require(publication["display_url"] == parsed.netloc, "display_url must equal the canonical URL hostname")

    expected_palette = {"paper", "ink", "muted", "line", "deep", "deep_2", "accent", "accent_2", "qr"}
    require(expected_palette.issubset(palette), f"palette is missing: {sorted(expected_palette - set(palette))}")
    for key in expected_palette:
        hex_rgb(str(palette[key]))
    require(str(palette["paper"]).lower() == "#ffffff", "palette.paper must be true white #ffffff")
    require(str(palette["qr"]).lower() == "#000000", "palette.qr must be black #000000")
    for key in ("ink", "deep", "accent", "muted"):
        require(contrast_ratio(str(palette[key]), str(palette["paper"])) >= 4.5, f"palette.{key} does not meet 4.5:1 contrast on white")

    require(int(typography.get("minimum_essential_print_points", 0)) >= 18, "essential print text must be at least 18 pt")
    require(int(typography.get("minimum_action_print_points", 0)) >= 18, "action print text must be at least 18 pt")
    require(int(typography.get("minimum_display_url_print_points", 0)) >= 23, "display URL must be at least 23 pt")
    require(typography.get("regular_file") == "Vera.ttf", "regular font must be ReportLab's Vera.ttf")
    require(typography.get("bold_file") == "VeraBd.ttf", "bold font must be ReportLab's VeraBd.ttf")

    require(qr.get("error_correction") == "Q", "QR error correction must be Q")
    require(int(qr.get("quiet_zone_modules", 0)) >= 4, "QR quiet zone must be at least four modules")
    require(float(qr.get("print_size_points", 0)) >= 288, "printed QR must be at least four inches")
    require(int(qr.get("phone_size_pixels", 0)) >= 760, "phone QR must be at least 760 pixels")
    require(int(qr.get("master_box_pixels", 0)) >= 20, "QR master modules must be at least 20 pixels")

    letter = _required_mapping(surfaces, "letter")
    phone = _required_mapping(surfaces, "phone")
    require((float(letter.get("width_points", 0)), float(letter.get("height_points", 0))) == LETTER_POINTS, "letter surface must be 612 x 792 points")
    require((int(letter.get("preview_width_pixels", 0)), int(letter.get("preview_height_pixels", 0))) == PRINT_PREVIEW_PIXELS, "letter preview must be 2550 x 3300 pixels")
    require(int(letter.get("preview_dpi", 0)) == 300, "letter preview must be 300 ppi")
    require((int(phone.get("width_pixels", 0)), int(phone.get("height_pixels", 0))) == PHONE_PIXELS, "phone surface must be 1080 x 1920 pixels")

    required_outputs = {"letter_pdf", "letter_preview_png", "phone_png", "qr_png", "build_report_json"}
    require(required_outputs.issubset(outputs), f"outputs are missing: {sorted(required_outputs - set(outputs))}")
    for key in required_outputs:
        output = Path(str(outputs[key]))
        require(not output.is_absolute() and output.parts[:2] == ("output", "outreach"), f"outputs.{key} must live under output/outreach")
    phone_pdf = Path(str(temporary_outputs.get("phone_pdf", "")))
    require(not phone_pdf.is_absolute() and phone_pdf.parts[:3] == ("tmp", "pdfs", "outreach"), "temporary phone PDF must live under tmp/pdfs/outreach")

    require(constraints.get("background_must_be_white") is True, "background_must_be_white must be true")
    require(constraints.get("large_solid_color_fields_allowed") is False, "large solid color fields must remain disabled")
    require(float(constraints.get("maximum_non_white_preview_ratio", 1)) <= 0.27, "maximum non-white preview ratio must be 0.27 or lower")
    reader_text = json.dumps([publication, copy, names], ensure_ascii=False).casefold()
    for phrase in constraints.get("forbidden_phrases", []):
        require(str(phrase).casefold() not in reader_text, f"reader-facing copy contains forbidden phrase: {phrase}")


def load_catalog(manifest_path: Path = DEFAULT_MANIFEST, root: Path | None = None) -> FlyerCatalog:
    manifest_path = manifest_path.resolve()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FlyerError(f"could not load flyer manifest {manifest_path}: {exc}") from exc
    require(isinstance(data, dict), "flyer manifest root must be an object")
    validate_manifest_data(data)
    return FlyerCatalog(manifest_path=manifest_path, root=(root or ROOT).resolve(), data=data)


def font_assets() -> dict[str, Path]:
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    assets = {
        "regular": font_dir / "Vera.ttf",
        "bold": font_dir / "VeraBd.ttf",
        "license": font_dir / "bitstream-vera-license.txt",
    }
    for label, path in assets.items():
        require(path.is_file(), f"ReportLab {label} font asset is missing: {path}")
    return assets


def register_fonts() -> dict[str, Path]:
    assets = font_assets()
    registered = set(pdfmetrics.getRegisteredFontNames())
    if FONT_REGULAR not in registered:
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(assets["regular"])))
    if FONT_BOLD not in registered:
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(assets["bold"])))
    return assets


def cover_record(catalog: FlyerCatalog) -> dict[str, Any]:
    artwork = catalog.data["artwork"]
    path = catalog.cover_path
    require(path.is_file(), f"canonical cover source is missing: {path}")
    actual_hash = sha256(path)
    require(actual_hash == artwork["cover_expected_sha256"], f"cover SHA-256 is {actual_hash}, expected {artwork['cover_expected_sha256']}")
    with Image.open(path) as image:
        pixels = (image.width, image.height)
    expected_pixels = (int(artwork["cover_expected_width_pixels"]), int(artwork["cover_expected_height_pixels"]))
    require(pixels == expected_pixels, f"cover is {pixels}, expected {expected_pixels}")
    height_points = float(artwork["letter_height_points"])
    width_points = height_points * pixels[0] / pixels[1]
    effective_ppi = pixels[1] / (height_points / 72)
    require(effective_ppi >= int(artwork["minimum_effective_ppi"]), f"cover effective resolution {effective_ppi:.1f} ppi is below the declared minimum")
    require(abs(height_points - float(catalog.data["qr"]["print_size_points"])) <= 0.001, "cover height must equal the QR row height")
    safe_width = LETTER_POINTS[0] - 2 * float(catalog.data["surfaces"]["letter"]["safe_margin_points"])
    group_width = width_points + float(artwork["letter_gap_to_qr_points"]) + float(catalog.data["qr"]["print_size_points"])
    require(group_width <= safe_width, f"cover/QR group width {group_width:.3f} exceeds safe width {safe_width:.3f}")
    return {
        "path": path.relative_to(catalog.root).as_posix() if path.is_relative_to(catalog.root) else str(path),
        "bytes": path.stat().st_size,
        "sha256": actual_hash,
        "pixels": list(pixels),
        "letter_points": [round(width_points, 3), round(height_points, 3)],
        "effective_ppi": round(effective_ppi, 1),
    }


def wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and pdfmetrics.stringWidth(candidate, font_name, font_size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fit_wrapped_text(text: str, font_name: str, preferred_size: float, minimum_size: float, max_width: float, max_lines: int) -> tuple[float, list[str]]:
    size = preferred_size
    while size >= minimum_size:
        lines = wrap_text(text, font_name, size, max_width)
        if len(lines) <= max_lines and all(pdfmetrics.stringWidth(line, font_name, size) <= max_width for line in lines):
            return size, lines
        size -= 0.5
    raise FlyerError(f"text does not fit at the minimum size: {text}")


def balanced_rows(items: Sequence[str], font_name: str, font_size: float, max_width: float, row_count: int = 3) -> list[str]:
    require(len(items) >= row_count, "not enough family names for requested rows")
    best: tuple[float, list[str]] | None = None
    separator = "  |  "
    for cuts in itertools.combinations(range(1, len(items)), row_count - 1):
        indexes = (0, *cuts, len(items))
        rows = [separator.join(items[indexes[pos] : indexes[pos + 1]]) for pos in range(row_count)]
        widths = [pdfmetrics.stringWidth(row, font_name, font_size) for row in rows]
        if any(width > max_width for width in widths):
            continue
        score = max(widths) + (max(widths) - min(widths)) * 0.3
        if best is None or score < best[0]:
            best = (score, rows)
    if best is None:
        raise FlyerError(f"family names do not fit in {row_count} rows at {font_size:g} pt")
    return best[1]


def add_text(drawing: Drawing, x: float, y: float, text: str, font: str, size: float, color: Color, anchor: str = "start") -> None:
    drawing.add(String(x, y, text, fontName=font, fontSize=size, fillColor=color, textAnchor=anchor))


def add_centered_lines(drawing: Drawing, lines: Sequence[str], center_x: float, first_baseline: float, leading: float, font: str, size: float, color: Color) -> None:
    for index, line in enumerate(lines):
        add_text(drawing, center_x, first_baseline - index * leading, line, font, size, color, "middle")


def add_qr(drawing: Drawing, x: float, y: float, size: float, value: str, level: str, border: int) -> QrCodeWidget:
    widget = QrCodeWidget(value, barLevel=level, barBorder=border)
    widget.barWidth = size
    widget.barHeight = size
    widget.x = x
    widget.y = y
    drawing.add(widget)
    return widget


def make_letter_drawing(catalog: FlyerCatalog) -> Drawing:
    register_fonts()
    data = catalog.data
    publication = data["publication"]
    copy = data["copy"]
    palette = {key: HexColor(value) for key, value in data["palette"].items()}
    qr = data["qr"]
    artwork = data["artwork"]
    cover = cover_record(catalog)
    width, height = LETTER_POINTS
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=palette["paper"], strokeColor=None))
    drawing.add(Line(36, 766, 576, 766, strokeColor=palette["accent"], strokeWidth=2.4))
    drawing.add(Line(36, 760, 576, 760, strokeColor=palette["accent_2"], strokeWidth=1.2))

    add_text(drawing, width / 2, 735, copy["eyebrow"], FONT_BOLD, 15, palette["accent"], "middle")
    add_text(drawing, width / 2, 685, publication["display_title"], FONT_BOLD, 48, palette["deep"], "middle")
    subtitle_size, subtitle_lines = fit_wrapped_text(publication["formal_subtitle"], FONT_REGULAR, 17, 16, 520, 2)
    add_centered_lines(drawing, subtitle_lines, width / 2, 650, 22, FONT_REGULAR, subtitle_size, palette["ink"])
    add_text(drawing, width / 2, 600, copy["headline"], FONT_BOLD, 21, palette["deep_2"], "middle")
    add_text(drawing, width / 2, 578, copy["camera_instruction"], FONT_REGULAR, 18, palette["ink"], "middle")

    qr_size = float(qr["print_size_points"])
    cover_width, cover_height = (float(value) for value in cover["letter_points"])
    cover_gap = float(artwork["letter_gap_to_qr_points"])
    row_y = float(artwork["letter_row_y_points"])
    group_x = (width - cover_width - cover_gap - qr_size) / 2
    cover_y = row_y + (qr_size - cover_height) / 2
    drawing.add(DrawingImage(group_x, cover_y, cover_width, cover_height, str(catalog.cover_path)))
    add_qr(drawing, group_x + cover_width + cover_gap, row_y, qr_size, catalog.canonical_url, str(qr["error_correction"]), int(qr["quiet_zone_modules"]))
    add_text(drawing, width / 2, 241, catalog.display_url, FONT_BOLD, 23, palette["accent"], "middle")

    actions = list(copy["actions"])
    positions = ((49, 200), (313, 200), (49, 171), (313, 171))
    for text, (x, y) in zip(actions, positions, strict=True):
        add_text(drawing, x, y, "•", FONT_BOLD, 18, palette["accent_2"])
        add_text(drawing, x + 15, y, text, FONT_REGULAR, 18, palette["ink"])

    add_text(drawing, width / 2, 140, copy["family_heading"], FONT_BOLD, 13, palette["muted"], "middle")
    rows = balanced_rows(data["family_names"], FONT_REGULAR, 18, 520, 3)
    add_centered_lines(drawing, rows, width / 2, 110, 28, FONT_REGULAR, 18, palette["deep"])
    drawing.add(Line(36, 27, 576, 27, strokeColor=palette["line"], strokeWidth=1))
    drawing.add(Line(238, 21, 374, 21, strokeColor=palette["accent_2"], strokeWidth=2))
    return drawing


def make_phone_drawing(catalog: FlyerCatalog) -> Drawing:
    register_fonts()
    data = catalog.data
    publication = data["publication"]
    copy = data["copy"]
    palette = {key: HexColor(value) for key, value in data["palette"].items()}
    qr = data["qr"]
    width, height = PHONE_PIXELS
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=palette["paper"], strokeColor=None))
    drawing.add(Line(72, 1845, 1008, 1845, strokeColor=palette["accent"], strokeWidth=8))
    drawing.add(Line(72, 1827, 1008, 1827, strokeColor=palette["accent_2"], strokeWidth=4))
    add_text(drawing, width / 2, 1750, copy["eyebrow"], FONT_BOLD, 38, palette["accent"], "middle")
    add_text(drawing, width / 2, 1625, publication["display_title"], FONT_BOLD, 92, palette["deep"], "middle")
    subtitle_size, subtitle_lines = fit_wrapped_text(publication["formal_subtitle"], FONT_REGULAR, 38, 34, 930, 2)
    add_centered_lines(drawing, subtitle_lines, width / 2, 1540, 48, FONT_REGULAR, subtitle_size, palette["ink"])
    add_text(drawing, width / 2, 1380, copy["headline"], FONT_BOLD, 43, palette["deep_2"], "middle")
    add_text(drawing, width / 2, 1310, copy["camera_instruction"], FONT_REGULAR, 32, palette["ink"], "middle")
    qr_size = int(qr["phone_size_pixels"])
    add_qr(drawing, (width - qr_size) / 2, 430, qr_size, catalog.canonical_url, str(qr["error_correction"]), int(qr["quiet_zone_modules"]))
    add_text(drawing, width / 2, 335, catalog.display_url, FONT_BOLD, 52, palette["accent"], "middle")
    add_text(drawing, width / 2, 255, copy["phone_offer"], FONT_BOLD, 29, palette["deep"], "middle")
    drawing.add(Line(72, 132, 1008, 132, strokeColor=palette["line"], strokeWidth=3))
    drawing.add(Line(420, 112, 660, 112, strokeColor=palette["accent_2"], strokeWidth=6))
    return drawing


def render_pdf(drawing: Drawing, path: Path, title: str, subject: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(drawing.width, drawing.height), pageCompression=1, invariant=1)
    pdf.setTitle(title)
    pdf.setSubject(subject)
    pdf.setAuthor("Alain Lessard family archive")
    pdf.setCreator("Story 006 reunion flyer generator")
    renderPDF.draw(drawing, pdf, 0, 0)
    pdf.showPage()
    pdf.save()


def run_pdftocairo(pdf_path: Path, png_path: Path, dpi: int) -> None:
    binary = shutil.which("pdftocairo")
    require(bool(binary), "pdftocairo is required to render flyer PNGs")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = png_path.with_suffix("")
    if png_path.exists():
        png_path.unlink()
    subprocess.run([str(binary), "-png", "-r", str(dpi), "-singlefile", str(pdf_path), str(prefix)], check=True)
    require(png_path.is_file(), f"pdftocairo did not create {png_path}")


def qr_metadata(catalog: FlyerCatalog) -> dict[str, int | str]:
    qr_config = catalog.data["qr"]
    widget = QrCodeWidget(catalog.canonical_url, barLevel=str(qr_config["error_correction"]), barBorder=int(qr_config["quiet_zone_modules"]))
    widget.qr.make()
    return {
        "version": int(widget.qr.version),
        "data_modules": int(widget.qr.moduleCount),
        "quiet_zone_modules": int(qr_config["quiet_zone_modules"]),
        "total_modules": int(widget.qr.moduleCount) + int(qr_config["quiet_zone_modules"]) * 2,
        "error_correction": str(qr_config["error_correction"]),
    }


def render_qr_png(catalog: FlyerCatalog, path: Path) -> dict[str, int | str]:
    qr_config = catalog.data["qr"]
    widget = QrCodeWidget(catalog.canonical_url, barLevel=str(qr_config["error_correction"]), barBorder=int(qr_config["quiet_zone_modules"]))
    widget.qr.make()
    border = int(qr_config["quiet_zone_modules"])
    box = int(qr_config["master_box_pixels"])
    module_count = int(widget.qr.moduleCount)
    total = module_count + border * 2
    image = Image.new("RGB", (total * box, total * box), "white")
    draw = ImageDraw.Draw(image)
    for row, values in enumerate(widget.qr.modules):
        for column, dark in enumerate(values):
            if dark:
                left = (column + border) * box
                top = (row + border) * box
                draw.rectangle((left, top, left + box - 1, top + box - 1), fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
    return {
        "version": int(widget.qr.version),
        "data_modules": module_count,
        "quiet_zone_modules": border,
        "total_modules": total,
        "box_pixels": box,
        "pixel_size": total * box,
        "error_correction": str(qr_config["error_correction"]),
    }


def tool_version(command: Sequence[str]) -> str:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    text = (result.stdout or result.stderr).strip()
    return text.splitlines()[0] if text else "unknown"


def artifact_record(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
    if path.suffix.lower() == ".png":
        with Image.open(path) as image:
            record["pixels"] = [image.width, image.height]
            record["mode"] = image.mode
    elif path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        page = reader.pages[0]
        record["pages"] = len(reader.pages)
        record["page_points"] = [float(page.mediabox.width), float(page.mediabox.height)]
    return record


def write_build_report(catalog: FlyerCatalog, qr_record: dict[str, int | str]) -> Path:
    assets = font_assets()
    output_keys = ("letter_pdf", "letter_preview_png", "phone_png", "qr_png")
    report = {
        "schema_version": "alain_reunion_flyer_build_report_v1",
        "source_manifest": catalog.manifest_path.relative_to(catalog.root).as_posix() if catalog.manifest_path.is_relative_to(catalog.root) else str(catalog.manifest_path),
        "canonical_url": catalog.canonical_url,
        "toolchain": {
            "python": sys.version.split()[0],
            "reportlab": reportlab.Version,
            "pillow": Image.__version__,
            "pdftocairo": tool_version([str(shutil.which("pdftocairo") or "pdftocairo"), "-v"]),
        },
        "fonts": {
            label: {"file": path.name, "sha256": sha256(path)} for label, path in assets.items()
        },
        "cover_source": cover_record(catalog),
        "qr": qr_record,
        "artifacts": {key: artifact_record(catalog.path("outputs", key)) for key in output_keys},
    }
    path = catalog.path("outputs", "build_report_json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def build_outputs(catalog: FlyerCatalog) -> dict[str, Path]:
    letter_pdf = catalog.path("outputs", "letter_pdf")
    letter_png = catalog.path("outputs", "letter_preview_png")
    phone_png = catalog.path("outputs", "phone_png")
    qr_png = catalog.path("outputs", "qr_png")
    phone_pdf = catalog.path("temporary_outputs", "phone_pdf")

    render_pdf(make_letter_drawing(catalog), letter_pdf, "Alain Lessard - Free Family History", "Letter-size reunion flyer for the free Alain Lessard digital family archive")
    run_pdftocairo(letter_pdf, letter_png, int(catalog.data["surfaces"]["letter"]["preview_dpi"]))
    render_pdf(make_phone_drawing(catalog), phone_pdf, "Alain Lessard - Phone QR Card", "Phone-display QR card for the free Alain Lessard digital family archive")
    run_pdftocairo(phone_pdf, phone_png, 72)
    qr_record = render_qr_png(catalog, qr_png)
    report = write_build_report(catalog, qr_record)
    return {"letter_pdf": letter_pdf, "letter_preview_png": letter_png, "phone_png": phone_png, "qr_png": qr_png, "build_report_json": report}


def flattened_pixels(image: Image.Image):
    """Return pixel values across the Pillow versions used by this project."""
    getter = getattr(image, "get_flattened_data", None)
    if getter is not None:
        return getter()
    return image.getdata()


def non_white_ratio(path: Path) -> float:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        pixels = flattened_pixels(rgb)
        non_white = sum(1 for red, green, blue in pixels if min(red, green, blue) < 248)
        return non_white / (rgb.width * rgb.height)


def build_stress_variants(catalog: FlyerCatalog, letter_path: Path, phone_path: Path) -> dict[str, Path]:
    """Create disposable camera/display proxies used by independent QR decode."""
    output_dir = catalog.root / "tmp" / "pdfs" / "outreach" / "stress"
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "letter_50_percent": output_dir / "letter-50-percent.png",
        "letter_25_percent": output_dir / "letter-25-percent.png",
        "letter_25_percent_grayscale": output_dir / "letter-25-percent-grayscale.png",
        "letter_camera_proxy": output_dir / "letter-camera-proxy.jpg",
        "phone_80_percent_brightness": output_dir / "phone-80-percent-brightness.png",
        "phone_65_percent_brightness": output_dir / "phone-65-percent-brightness.png",
    }

    with Image.open(letter_path) as source:
        letter = source.convert("RGB")
        half = letter.resize((1275, 1650), Image.Resampling.LANCZOS)
        quarter = letter.resize((638, 825), Image.Resampling.LANCZOS)
        half.save(paths["letter_50_percent"])
        quarter.save(paths["letter_25_percent"])
        quarter.convert("L").save(paths["letter_25_percent_grayscale"])
        half.filter(ImageFilter.GaussianBlur(radius=0.8)).save(
            paths["letter_camera_proxy"], format="JPEG", quality=55, subsampling=2
        )

    with Image.open(phone_path) as source:
        phone = source.convert("RGB")
        ImageEnhance.Brightness(phone).enhance(0.8).save(paths["phone_80_percent_brightness"])
        ImageEnhance.Brightness(phone).enhance(0.65).save(paths["phone_65_percent_brightness"])

    return paths


def decode_qr_with_vision(path: Path) -> list[str]:
    swift = shutil.which("swift")
    require(bool(swift), "Swift is required for independent QR decoding with macOS Vision")
    require(VISION_DECODER.is_file(), f"Vision decoder script is missing: {VISION_DECODER}")
    cache = Path("/tmp/alain-lessard-qr-swift-cache")
    cache.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(swift), "-module-cache-path", str(cache), str(VISION_DECODER), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def validate_outputs(catalog: FlyerCatalog, decode_qr: bool = True) -> ValidationResult:
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    paths = {key: catalog.path("outputs", key) for key in ("letter_pdf", "letter_preview_png", "phone_png", "qr_png", "build_report_json")}
    for key, path in paths.items():
        if not path.is_file() or path.stat().st_size <= 0:
            errors.append(f"missing or empty {key}: {path}")
    if errors:
        return ValidationResult(errors, metrics)

    try:
        reader = PdfReader(str(paths["letter_pdf"]))
        if len(reader.pages) != 1:
            errors.append(f"letter PDF has {len(reader.pages)} pages, expected 1")
        page = reader.pages[0]
        page_points = (float(page.mediabox.width), float(page.mediabox.height))
        metrics["letter_page_points"] = list(page_points)
        if page_points != LETTER_POINTS:
            errors.append(f"letter PDF page is {page_points}, expected {LETTER_POINTS}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for wanted in (catalog.data["publication"]["display_title"], catalog.display_url, *catalog.data["copy"]["actions"]):
            if wanted not in text:
                errors.append(f"letter PDF selectable text is missing {wanted!r}")
        for phrase in catalog.data["constraints"]["forbidden_phrases"]:
            if str(phrase).casefold() in text.casefold():
                errors.append(f"letter PDF contains forbidden phrase {phrase!r}")
        cover = cover_record(catalog)
        embedded_images = list(page.images)
        metrics["letter_embedded_images"] = [
            {"name": image.name, "pixels": list(image.image.size)} for image in embedded_images
        ]
        if len(embedded_images) != 1:
            errors.append(f"letter PDF has {len(embedded_images)} embedded images, expected one canonical cover")
        elif list(embedded_images[0].image.size) != cover["pixels"]:
            errors.append(f"embedded cover is {embedded_images[0].image.size}, expected {tuple(cover['pixels'])}")
        metrics["cover_source"] = cover
    except Exception as exc:  # noqa: BLE001
        errors.append(f"could not inspect letter PDF: {exc}")

    pdffonts = shutil.which("pdffonts")
    if not pdffonts:
        errors.append("pdffonts is required to verify embedded flyer fonts")
    else:
        result = subprocess.run([pdffonts, str(paths["letter_pdf"])], capture_output=True, text=True, check=True)
        metrics["pdffonts"] = result.stdout.splitlines()[2:]
        for family in ("BitstreamVeraSans", "BitstreamVeraSans-Bold"):
            matching = [line for line in result.stdout.splitlines() if family in line]
            if not matching or not all(" yes " in f" {line} " for line in matching):
                errors.append(f"embedded font proof missing for {family}")

    expected_pixels = {"letter_preview_png": PRINT_PREVIEW_PIXELS, "phone_png": PHONE_PIXELS}
    for key, expected in expected_pixels.items():
        with Image.open(paths[key]) as image:
            metrics[f"{key}_pixels"] = [image.width, image.height]
            if image.size != expected:
                errors.append(f"{key} is {image.size}, expected {expected}")
            rgb = image.convert("RGB")
            corners = (rgb.getpixel((0, 0)), rgb.getpixel((rgb.width - 1, 0)), rgb.getpixel((0, rgb.height - 1)), rgb.getpixel((rgb.width - 1, rgb.height - 1)))
            if any(sum(color) < 750 for color in corners):
                errors.append(f"{key} does not retain white outer corners")

    preview_ratio = non_white_ratio(paths["letter_preview_png"])
    phone_ratio = non_white_ratio(paths["phone_png"])
    metrics["letter_non_white_ratio"] = round(preview_ratio, 6)
    metrics["phone_non_white_ratio"] = round(phone_ratio, 6)
    if preview_ratio > float(catalog.data["constraints"]["maximum_non_white_preview_ratio"]):
        errors.append(f"letter preview non-white ratio {preview_ratio:.3f} exceeds the toner limit")
    if phone_ratio > 0.28:
        errors.append(f"phone image non-white ratio {phone_ratio:.3f} is unexpectedly high")

    with Image.open(paths["qr_png"]) as qr_image:
        rgb = qr_image.convert("RGB")
        colors = set(flattened_pixels(rgb))
        metrics["qr_pixels"] = [rgb.width, rgb.height]
        metrics["qr_color_count"] = len(colors)
        if colors != {(0, 0, 0), (255, 255, 255)}:
            errors.append(f"QR master must contain only pure black and white, found {len(colors)} colors")
        qr_info = qr_metadata(catalog)
        expected_size = int(qr_info["total_modules"]) * int(catalog.data["qr"]["master_box_pixels"])
        if rgb.size != (expected_size, expected_size):
            errors.append(f"QR master is {rgb.size}, expected {(expected_size, expected_size)}")
        border_pixels = int(catalog.data["qr"]["quiet_zone_modules"]) * int(catalog.data["qr"]["master_box_pixels"])
        samples = (rgb.crop((0, 0, rgb.width, border_pixels)), rgb.crop((0, rgb.height - border_pixels, rgb.width, rgb.height)), rgb.crop((0, 0, border_pixels, rgb.height)), rgb.crop((rgb.width - border_pixels, 0, rgb.width, rgb.height)))
        if any(set(flattened_pixels(sample)) != {(255, 255, 255)} for sample in samples):
            errors.append("QR master quiet zone is not four pure-white modules on every side")

    info = qr_metadata(catalog)
    metrics["qr"] = info
    if int(info["version"]) != int(catalog.data["qr"]["expected_version"]):
        errors.append(f"QR version is {info['version']}, expected {catalog.data['qr']['expected_version']}")
    if int(info["data_modules"]) != int(catalog.data["qr"]["expected_data_modules"]):
        errors.append(f"QR data module count is {info['data_modules']}, expected {catalog.data['qr']['expected_data_modules']}")

    stress_paths = build_stress_variants(catalog, paths["letter_preview_png"], paths["phone_png"])
    stress_metrics: dict[str, dict[str, Any]] = {}
    for key, path in stress_paths.items():
        with Image.open(path) as image:
            stress_metrics[key] = {
                "path": path.relative_to(catalog.root).as_posix(),
                "pixels": [image.width, image.height],
                "mode": image.mode,
            }
    metrics["stress_variants"] = stress_metrics

    if decode_qr:
        decoded: dict[str, list[str]] = {}
        decode_targets = {key: paths[key] for key in ("letter_preview_png", "phone_png", "qr_png")}
        decode_targets.update(stress_paths)
        for key, path in decode_targets.items():
            try:
                payloads = decode_qr_with_vision(path)
                decoded[key] = payloads
                if catalog.canonical_url not in payloads:
                    errors.append(f"{key} decoded to {payloads}, expected {catalog.canonical_url}")
            except (FlyerError, subprocess.CalledProcessError) as exc:
                errors.append(f"independent QR decode failed for {key}: {exc}")
        metrics["decoded_qr"] = decoded

    report = json.loads(paths["build_report_json"].read_text(encoding="utf-8"))
    if report.get("canonical_url") != catalog.canonical_url:
        errors.append("build report canonical URL does not match the manifest")
    if report.get("cover_source") != cover_record(catalog):
        errors.append("build report cover source does not match the canonical cover contract")
    return ValidationResult(errors, metrics)


def print_result(result: ValidationResult) -> None:
    print(json.dumps({"ok": result.ok, "errors": result.errors, "metrics": result.metrics}, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate the Alain Lessard reunion flyer and phone QR card.")
    parser.add_argument("command", choices=("build", "validate", "all"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skip-vision", action="store_true", help="Skip independent QR decoding; intended only for narrow fixture tests.")
    args = parser.parse_args()
    try:
        catalog = load_catalog(args.manifest)
        if args.command in {"build", "all"}:
            outputs = build_outputs(catalog)
            for label, path in outputs.items():
                print(f"{label}: {path.relative_to(ROOT)}")
        if args.command in {"validate", "all"}:
            result = validate_outputs(catalog, decode_qr=not args.skip_vision)
            print_result(result)
            return 0 if result.ok else 1
    except (FlyerError, OSError, subprocess.CalledProcessError) as exc:
        print(f"reunion flyer error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
