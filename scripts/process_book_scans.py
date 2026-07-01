#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "input" / "raw scans" / "main book"
PROCESSED_DIR = ROOT / "output" / "processed-pages"
CONTACT_SHEET_DIR = PROCESSED_DIR / "contact-sheets"
TMP_PDF_DIR = ROOT / "tmp" / "pdfs"
PDF_WORK_DIR = TMP_PDF_DIR / "pages"
RENDERED_DIR = TMP_PDF_DIR / "rendered"
MANIFEST_PATH = PROCESSED_DIR / "manifest.json"
ARCHIVAL_IMAGE_ONLY_PDF = TMP_PDF_DIR / "alain-lessard-book-archival-image-only.pdf"
DISTRIBUTION_IMAGE_ONLY_PDF = TMP_PDF_DIR / "alain-lessard-book-distribution-image-only.pdf"
SEARCHABLE_PDF = ROOT / "output" / "pdf" / "alain-lessard-book-searchable.pdf"
ARCHIVAL_SEARCHABLE_PDF = ROOT / "output" / "pdf" / "alain-lessard-book-archival-searchable.pdf"

TARGET_SIZE = (2550, 3371)
DPI = 300
PDF_METADATA = {
    "title": "Alain Lessard: Our First Ancestors and A Compilation of Stories of Their Descendants",
    "author": "Alain-Lessard History Book Committee",
    "subject": "A scanned and OCRed copy of the Alain Lessard family history book, originally published in 1987.",
    "keywords": "Family history, genealogy, Alain Lessard, Lessard, Alain, Saskatchewan, 1987, archival",
}
PDF_PROFILES = {
    "distribution": {
        "image_pdf": DISTRIBUTION_IMAGE_ONLY_PDF,
        "searchable_pdf": SEARCHABLE_PDF,
        "page_quality": 82,
        "cover_quality": 90,
        "color_mode": "grayscale",
        "output_type": "pdfa",
        "ocr_optimize": "1",
        "ocr_force": True,
        "ocr_deskew": True,
        "ocr_rotate_pages": True,
    },
    "archival": {
        "image_pdf": ARCHIVAL_IMAGE_ONLY_PDF,
        "searchable_pdf": ARCHIVAL_SEARCHABLE_PDF,
        "page_quality": 95,
        "cover_quality": 95,
        "color_mode": "grayscale",
        "output_type": "pdf",
        "ocr_optimize": "0",
        "ocr_force": False,
        "ocr_deskew": False,
        "ocr_rotate_pages": False,
    },
}
DARK_THRESHOLD = 70
SCORE_THRESHOLD = 0.65
EDGE_RELEASE_SCORE = 0.18
EDGE_MARGIN = 12
TOP_IGNORE_ROWS = 80
BOTTOM_IGNORE_ROWS = 80
SMOOTHING_WINDOW = 9
SAMPLE_PAGES = (1, 2, 3, 30, 76, 102, 132, 141, 144, 153)


@dataclass(frozen=True)
class CropDecision:
    side: str
    peak_y: int | None
    top_score: float
    bottom_score: float
    crop_box: tuple[int, int, int, int]


@dataclass(frozen=True)
class PageRecord:
    page_number: int
    source_path: str
    output_path: str
    source_size: tuple[int, int]
    crop_side: str
    crop_peak_y: int | None
    top_score: float
    bottom_score: float
    crop_box: tuple[int, int, int, int]
    residual_edge_trim: tuple[int, int]
    final_crop_box: tuple[int, int, int, int]
    cropped_size: tuple[int, int]
    canvas_size: tuple[int, int]


def raw_scan_paths() -> list[Path]:
    paths = sorted(RAW_DIR.glob("*.jpg"))
    if not paths:
        raise SystemExit(f"No raw JPG scans found under {RAW_DIR}")
    return paths


def smooth_row_scores(scores: np.ndarray) -> np.ndarray:
    kernel = np.ones(SMOOTHING_WINDOW) / SMOOTHING_WINDOW
    return np.convolve(scores, kernel, mode="same")


def detect_platen_crop(gray_image: Image.Image) -> CropDecision:
    arr = np.asarray(gray_image)
    height, width = arr.shape
    dark_fraction_by_row = (arr < DARK_THRESHOLD).mean(axis=1)
    smoothed = smooth_row_scores(dark_fraction_by_row)

    top_start = TOP_IGNORE_ROWS
    top_end = int(height * 0.35)
    bottom_start = int(height * 0.65)
    bottom_end = height - BOTTOM_IGNORE_ROWS

    top_region = smoothed[top_start:top_end]
    bottom_region = smoothed[bottom_start:bottom_end]

    top_peak = int(np.argmax(top_region) + top_start) if len(top_region) else None
    bottom_peak = int(np.argmax(bottom_region) + bottom_start) if len(bottom_region) else None
    top_score = float(smoothed[top_peak]) if top_peak is not None else 0.0
    bottom_score = float(smoothed[bottom_peak]) if bottom_peak is not None else 0.0

    side = "none"
    peak_y: int | None = None
    crop_top = 0
    crop_bottom = height

    if top_score >= SCORE_THRESHOLD and top_score >= bottom_score * 0.97:
        side = "top"
        peak_y = top_peak
        end = peak_y
        while end < height and smoothed[end] > EDGE_RELEASE_SCORE:
            end += 1
        crop_top = min(height, end + EDGE_MARGIN)
    elif bottom_score >= SCORE_THRESHOLD:
        side = "bottom"
        peak_y = bottom_peak
        start = peak_y
        while start > 0 and smoothed[start] > EDGE_RELEASE_SCORE:
            start -= 1
        crop_bottom = max(0, start - EDGE_MARGIN)

    return CropDecision(
        side=side,
        peak_y=peak_y,
        top_score=top_score,
        bottom_score=bottom_score,
        crop_box=(0, crop_top, width, crop_bottom),
    )


def detect_residual_edge_trim(image: Image.Image) -> tuple[int, int]:
    arr = np.asarray(image.convert("L"))
    height, _width = arr.shape
    dark_fraction_by_row = (arr < DARK_THRESHOLD).mean(axis=1)
    smoothed = smooth_row_scores(dark_fraction_by_row)

    top_trim = 0
    top_region = smoothed[: min(TOP_IGNORE_ROWS, height)]
    if len(top_region):
        top_peak = int(np.argmax(top_region))
        if float(smoothed[top_peak]) >= SCORE_THRESHOLD:
            end = top_peak
            while end < height and smoothed[end] > EDGE_RELEASE_SCORE:
                end += 1
            top_trim = min(height, end + EDGE_MARGIN)

    bottom_trim = 0
    bottom_start = max(0, height - BOTTOM_IGNORE_ROWS)
    bottom_region = smoothed[bottom_start:]
    if len(bottom_region):
        bottom_peak = int(np.argmax(bottom_region) + bottom_start)
        if float(smoothed[bottom_peak]) >= SCORE_THRESHOLD:
            start = bottom_peak
            while start > 0 and smoothed[start] > EDGE_RELEASE_SCORE:
                start -= 1
            bottom_cut = max(0, start - EDGE_MARGIN)
            bottom_trim = max(0, height - bottom_cut)

    if top_trim + bottom_trim >= height:
        return (0, 0)
    return (top_trim, bottom_trim)


def enhance_page(image: Image.Image, page_number: int) -> Image.Image:
    if page_number == 1:
        rgb = image.convert("RGB")
        return ImageOps.autocontrast(rgb, cutoff=0.2)

    gray = image.convert("L")
    gray = ImageOps.autocontrast(gray, cutoff=0.5)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=3))
    return gray.convert("RGB")


def normalize_to_canvas(image: Image.Image) -> Image.Image:
    target_width, target_height = TARGET_SIZE
    if image.width != target_width:
        scale = target_width / image.width
        new_height = round(image.height * scale)
        image = image.resize((target_width, new_height), Image.Resampling.LANCZOS)

    if image.height > target_height:
        image = image.crop((0, 0, target_width, target_height))

    canvas = Image.new("RGB", TARGET_SIZE, "white")
    canvas.paste(image, (0, 0))
    return canvas


def process_scan(path: Path, page_number: int) -> PageRecord:
    source_image = Image.open(path)
    source_image = ImageOps.exif_transpose(source_image)
    gray = source_image.convert("L")
    decision = detect_platen_crop(gray)
    primary_cropped = source_image.crop(decision.crop_box)
    residual_top, residual_bottom = detect_residual_edge_trim(primary_cropped)
    crop_left, crop_top, crop_right, crop_bottom = decision.crop_box
    final_crop_box = (
        crop_left,
        crop_top + residual_top,
        crop_right,
        crop_bottom - residual_bottom,
    )
    cropped = source_image.crop(final_crop_box)
    enhanced = enhance_page(cropped, page_number)
    normalized = normalize_to_canvas(enhanced)

    output_path = PROCESSED_DIR / f"page-{page_number:03d}.jpg"
    normalized.save(output_path, quality=95, subsampling=0, dpi=(DPI, DPI))

    return PageRecord(
        page_number=page_number,
        source_path=path.relative_to(ROOT).as_posix(),
        output_path=output_path.relative_to(ROOT).as_posix(),
        source_size=source_image.size,
        crop_side=decision.side,
        crop_peak_y=decision.peak_y,
        top_score=round(decision.top_score, 6),
        bottom_score=round(decision.bottom_score, 6),
        crop_box=decision.crop_box,
        residual_edge_trim=(residual_top, residual_bottom),
        final_crop_box=final_crop_box,
        cropped_size=(final_crop_box[2] - final_crop_box[0], final_crop_box[3] - final_crop_box[1]),
        canvas_size=TARGET_SIZE,
    )


def write_manifest(records: list[PageRecord]) -> None:
    payload = {
        "schema_version": "alain_lessard_scan_processing_v1",
        "source_dir": RAW_DIR.relative_to(ROOT).as_posix(),
        "processed_dir": PROCESSED_DIR.relative_to(ROOT).as_posix(),
        "target_size": TARGET_SIZE,
        "dpi": DPI,
        "pdf_metadata": PDF_METADATA,
        "pdf_profiles": {
            name: {
                "image_pdf": values["image_pdf"].relative_to(ROOT).as_posix(),
                "searchable_pdf": values["searchable_pdf"].relative_to(ROOT).as_posix(),
                "page_quality": values["page_quality"],
                "cover_quality": values["cover_quality"],
                "color_mode": values["color_mode"],
                "output_type": values["output_type"],
                "ocr_optimize": values["ocr_optimize"],
                "ocr_force": values["ocr_force"],
                "ocr_deskew": values["ocr_deskew"],
                "ocr_rotate_pages": values["ocr_rotate_pages"],
            }
            for name, values in PDF_PROFILES.items()
        },
        "page_count": len(records),
        "records": [asdict(record) for record in records],
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def create_contact_sheets(page_paths: list[Path]) -> None:
    CONTACT_SHEET_DIR.mkdir(parents=True, exist_ok=True)
    thumbnails: list[Image.Image] = []
    thumb_width = 255
    thumb_height = 337
    for path in page_paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        thumb = Image.new("RGB", (thumb_width, thumb_height), "white")
        thumb.paste(image, ((thumb_width - image.width) // 2, (thumb_height - image.height) // 2))
        thumbnails.append(thumb)

    columns = 9
    rows_per_sheet = 4
    pages_per_sheet = columns * rows_per_sheet
    for sheet_index in range(0, len(thumbnails), pages_per_sheet):
        batch = thumbnails[sheet_index : sheet_index + pages_per_sheet]
        rows = (len(batch) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * thumb_width, rows * thumb_height), "white")
        for index, thumb in enumerate(batch):
            x = (index % columns) * thumb_width
            y = (index // columns) * thumb_height
            sheet.paste(thumb, (x, y))
        start_page = sheet_index + 1
        end_page = sheet_index + len(batch)
        sheet.save(CONTACT_SHEET_DIR / f"pages-{start_page:03d}-{end_page:03d}.jpg", quality=92)


def process_scans() -> int:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for old_page in PROCESSED_DIR.glob("page-*.jpg"):
        old_page.unlink()
    if CONTACT_SHEET_DIR.exists():
        shutil.rmtree(CONTACT_SHEET_DIR)

    records: list[PageRecord] = []
    for page_number, path in enumerate(raw_scan_paths(), start=1):
        records.append(process_scan(path, page_number))
        if page_number % 25 == 0:
            print(f"processed {page_number} pages")

    write_manifest(records)
    create_contact_sheets([ROOT / record.output_path for record in records])
    print(f"processed {len(records)} scans")
    print(f"manifest: {MANIFEST_PATH.relative_to(ROOT)}")
    return 0


def require_binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise SystemExit(f"Missing required binary on PATH: {name}")
    return binary


def work_page_paths(profile: str) -> list[Path]:
    page_paths = sorted(PROCESSED_DIR.glob("page-*.jpg"))
    if not page_paths:
        raise SystemExit("No processed pages found. Run `make process-scans` first.")
    if profile not in PDF_PROFILES:
        raise SystemExit(f"Unknown PDF profile: {profile}")

    profile_dir = PDF_WORK_DIR / profile
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    profile_config = PDF_PROFILES[profile]
    output_paths: list[Path] = []
    for index, page_path in enumerate(page_paths, start=1):
        image = Image.open(page_path)
        output_path = profile_dir / page_path.name
        if index != 1 and profile_config["color_mode"] == "grayscale":
            image = image.convert("L")
            image.save(output_path, quality=profile_config["page_quality"], dpi=(DPI, DPI))
        else:
            image = image.convert("RGB")
            quality = profile_config["cover_quality"] if index == 1 else profile_config["page_quality"]
            image.save(output_path, quality=quality, subsampling=0, dpi=(DPI, DPI))
        output_paths.append(output_path)
    return output_paths


def build_image_pdf(profile: str) -> int:
    TMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
    profile_config = PDF_PROFILES[profile]
    page_paths = work_page_paths(profile)
    image_pdf = profile_config["image_pdf"]

    command = [
        require_binary("img2pdf"),
        "--imgsize",
        f"{DPI}dpi",
        "--output",
        str(image_pdf),
        *[str(path) for path in page_paths],
    ]
    subprocess.run(command, check=True)
    print(f"{profile} image-only PDF: {image_pdf.relative_to(ROOT)}")
    return 0


def ocr_pdf(profile: str) -> int:
    profile_config = PDF_PROFILES[profile]
    image_pdf = profile_config["image_pdf"]
    searchable_pdf = profile_config["searchable_pdf"]
    if not image_pdf.exists():
        raise SystemExit(f"{profile} image-only PDF missing. Run `make build-image-pdf PROFILE={profile}` first.")
    searchable_pdf.parent.mkdir(parents=True, exist_ok=True)
    if searchable_pdf.exists():
        searchable_pdf.unlink()
    command = [require_binary("ocrmypdf")]
    if profile_config["ocr_force"]:
        command.append("--force-ocr")
    if profile_config["ocr_rotate_pages"]:
        command.append("--rotate-pages")
    if profile_config["ocr_deskew"]:
        command.append("--deskew")
    command.extend(
        [
            "--output-type",
            profile_config["output_type"],
            "--optimize",
            profile_config["ocr_optimize"],
            "-l",
            "eng",
            "--title",
            PDF_METADATA["title"],
            "--author",
            PDF_METADATA["author"],
            "--subject",
            PDF_METADATA["subject"],
            "--keywords",
            PDF_METADATA["keywords"],
            str(image_pdf),
            str(searchable_pdf),
        ]
    )
    subprocess.run(command, check=True)
    print(f"{profile} searchable PDF: {searchable_pdf.relative_to(ROOT)}")
    return 0


def render_pdf_checks() -> int:
    if not SEARCHABLE_PDF.exists():
        raise SystemExit("Searchable PDF missing. Run `make scan-pdf-all` first.")
    RENDERED_DIR.mkdir(parents=True, exist_ok=True)
    for old_png in RENDERED_DIR.glob("*.png"):
        old_png.unlink()

    pdftoppm = require_binary("pdftoppm")
    for page_number in SAMPLE_PAGES:
        prefix = RENDERED_DIR / f"page-{page_number:03d}"
        subprocess.run(
            [
                pdftoppm,
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                "-png",
                "-r",
                "120",
                str(SEARCHABLE_PDF),
                str(prefix),
            ],
            check=True,
        )
    print(f"rendered checks: {RENDERED_DIR.relative_to(ROOT)}")
    return 0


def validate_pdf() -> int:
    if not MANIFEST_PATH.exists():
        raise SystemExit("Processing manifest missing.")
    if not SEARCHABLE_PDF.exists():
        raise SystemExit("Searchable PDF missing.")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    readers = {
        "distribution": PdfReader(str(SEARCHABLE_PDF)),
    }
    if ARCHIVAL_SEARCHABLE_PDF.exists():
        readers["archival"] = PdfReader(str(ARCHIVAL_SEARCHABLE_PDF))
    errors: list[str] = []
    if manifest.get("page_count") != 153:
        errors.append(f"manifest page_count is {manifest.get('page_count')}, expected 153")

    text_samples: dict[str, dict[int, int]] = {}
    for profile, reader in readers.items():
        page_count = len(reader.pages)
        if page_count != 153:
            errors.append(f"{profile} PDF page count is {page_count}, expected 153")
        metadata = reader.metadata or {}
        for key, value in (
            ("/Title", PDF_METADATA["title"]),
            ("/Author", PDF_METADATA["author"]),
            ("/Subject", PDF_METADATA["subject"]),
            ("/Keywords", PDF_METADATA["keywords"]),
        ):
            if metadata.get(key) != value:
                errors.append(f"{profile} metadata {key} is {metadata.get(key)!r}, expected {value!r}")
        profile_samples: dict[int, int] = {}
        for page_number in (2, 30, 76, 144, 153):
            text = reader.pages[page_number - 1].extract_text() or ""
            profile_samples[page_number] = len(text.strip())
            if page_number != 2 and len(text.strip()) < 200:
                errors.append(
                    f"{profile} page {page_number} OCR text is unexpectedly short: {len(text.strip())} chars"
                )
        text_samples[profile] = profile_samples

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"manifest pages: {manifest.get('page_count')}")
    print(f"pdf pages: { {profile: len(reader.pages) for profile, reader in readers.items()} }")
    print(f"ocr sample chars: {text_samples}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process Alain Lessard book scans into a searchable PDF.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("process")
    build_parser = subparsers.add_parser("build-image-pdf")
    build_parser.add_argument("--profile", choices=sorted(PDF_PROFILES), default="distribution")
    ocr_parser = subparsers.add_parser("ocr")
    ocr_parser.add_argument("--profile", choices=sorted(PDF_PROFILES), default="distribution")
    subparsers.add_parser("render-checks")
    subparsers.add_parser("validate-pdf")
    args = parser.parse_args(argv)

    if args.command == "process":
        return process_scans()
    if args.command == "build-image-pdf":
        return build_image_pdf(args.profile)
    if args.command == "ocr":
        return ocr_pdf(args.profile)
    if args.command == "render-checks":
        return render_pdf_checks()
    if args.command == "validate-pdf":
        return validate_pdf()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
