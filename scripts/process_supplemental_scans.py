#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "output" / "supplemental-documents"
TMP_ROOT = ROOT / "tmp" / "pdfs" / "supplemental"
RENDERED_ROOT = TMP_ROOT / "rendered"
PDF_DIR = ROOT / "output" / "pdf"
TARGET_SIZE = (2550, 3371)
DPI = 300


@dataclass(frozen=True)
class SupplementalDocument:
    slug: str
    title: str
    raw_dir: Path
    description: str
    cleanup_profile: str


@dataclass(frozen=True)
class PageRecord:
    page_number: int
    source_path: str
    output_path: str
    source_size: tuple[int, int]
    canvas_size: tuple[int, int]
    paste_offset: tuple[int, int]
    cleanup_profile: str
    deskew_angle: float


DOCUMENTS = (
    SupplementalDocument(
        slug="alains-song",
        title="Alain's Song",
        raw_dir=ROOT / "input" / "raw scans" / "Alain's Song",
        description="A six-page song sheet found tucked into the Alain Lessard book.",
        cleanup_profile="folded-sheet",
    ),
    SupplementalDocument(
        slug="growing-up-on-the-farm",
        title="Growing Up on the Farm: A Tribute to Mom and Dad",
        raw_dir=ROOT / "input" / "raw scans" / "Growing Up on the Farm",
        description="A thirteen-page tribute poem found tucked into the Alain Lessard book.",
        cleanup_profile="typed-pages",
    ),
)


def require_binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise SystemExit(f"Missing required binary on PATH: {name}")
    return binary


def raw_scan_paths(document: SupplementalDocument) -> list[Path]:
    paths = sorted(document.raw_dir.glob("*.jpg"))
    if not paths:
        raise SystemExit(f"No JPG scans found under {document.raw_dir}")
    return paths


def document_output_dir(document: SupplementalDocument) -> Path:
    return OUTPUT_ROOT / document.slug


def processed_dir(document: SupplementalDocument) -> Path:
    return document_output_dir(document) / "processed-pages"


def work_dir(document: SupplementalDocument, profile: str) -> Path:
    return TMP_ROOT / "pages" / document.slug / profile


def image_pdf_path(document: SupplementalDocument, profile: str) -> Path:
    return TMP_ROOT / f"{document.slug}-{profile}-image-only.pdf"


def searchable_pdf_path(document: SupplementalDocument, profile: str) -> Path:
    suffix = "archival-searchable" if profile == "archival" else "searchable"
    return PDF_DIR / f"{document.slug}-{suffix}.pdf"


def text_path(document: SupplementalDocument) -> Path:
    return document_output_dir(document) / "ocr-text.txt"


def clean_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def otsu_threshold(image: Image.Image) -> int:
    array = np.asarray(image.convert("L"), dtype=np.uint8)
    histogram = np.bincount(array.ravel(), minlength=256).astype(np.float64)
    total = array.size
    total_sum = float(np.dot(np.arange(256), histogram))
    background_weight = 0.0
    background_sum = 0.0
    best_variance = -1.0
    best_threshold = 128
    for threshold in range(256):
        background_weight += histogram[threshold]
        if background_weight == 0:
            continue
        foreground_weight = total - background_weight
        if foreground_weight == 0:
            break
        background_sum += threshold * histogram[threshold]
        background_mean = background_sum / background_weight
        foreground_mean = (total_sum - background_sum) / foreground_weight
        variance = background_weight * foreground_weight * (background_mean - foreground_mean) ** 2
        if variance > best_variance:
            best_variance = variance
            best_threshold = threshold
    return int(best_threshold)


def estimate_text_angle(gray: Image.Image) -> float:
    thumbnail = gray.copy()
    thumbnail.thumbnail((700, 900), Image.Resampling.LANCZOS)
    best_angle = 0.0
    best_score = -1.0
    for tenths in range(-12, 13):
        angle = tenths / 10
        rotated = thumbnail.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=255)
        array = np.asarray(rotated, dtype=np.uint8)
        threshold = max(40, min(190, otsu_threshold(rotated)))
        mask = array < threshold
        if mask.shape[0] > 60 and mask.shape[1] > 60:
            mask[:30, :] = False
            mask[-30:, :] = False
            mask[:, :30] = False
            mask[:, -30:] = False
        if int(mask.sum()) < 200:
            continue
        row_counts = mask.sum(axis=1).astype(np.float64)
        score = float(row_counts.var() / (row_counts.mean() + 1.0))
        if score > best_score:
            best_score = score
            best_angle = angle
    return best_angle if abs(best_angle) >= 0.15 else 0.0


def flatten_background(gray: Image.Image, radius: int) -> Image.Image:
    background = gray.filter(ImageFilter.GaussianBlur(radius=radius))
    source = np.asarray(gray, dtype=np.float32)
    background_array = np.asarray(background, dtype=np.float32)
    normalized = source * 248.0 / np.maximum(background_array, 1.0)
    low, high = np.percentile(normalized, (0.4, 99.7))
    if high <= low:
        high = low + 1.0
    normalized = (normalized - low) * 255.0 / (high - low)
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)
    return Image.fromarray(normalized, "L")


def clean_borders(image: Image.Image, margin: int = 18) -> Image.Image:
    if image.width <= margin * 2 or image.height <= margin * 2:
        return image
    cleaned = image.copy()
    pixels = cleaned.load()
    for x in range(cleaned.width):
        for y in range(margin):
            pixels[x, y] = 255
            pixels[x, cleaned.height - 1 - y] = 255
    for y in range(cleaned.height):
        for x in range(margin):
            pixels[x, y] = 255
            pixels[cleaned.width - 1 - x, y] = 255
    return cleaned


def cleanup_folded_sheet(gray: Image.Image) -> Image.Image:
    background = gray.filter(ImageFilter.GaussianBlur(radius=55))
    source = np.asarray(gray, dtype=np.float32)
    background_array = np.asarray(background, dtype=np.float32)
    array = source * 235.0 / np.maximum(background_array, 1.0)
    array = np.clip(array, 0, 255)
    array = np.where(array > 190, 255, array)
    array = np.where((array > 120) & (array <= 190), np.minimum(255, array + 45), array)
    array = np.where(array < 80, array * 0.78, array)
    softened = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), "L")
    softened = softened.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=5))
    return clean_borders(softened, margin=24)


def cleanup_typed_page(gray: Image.Image) -> Image.Image:
    angle = estimate_text_angle(gray)
    if angle:
        gray = gray.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=255)
    flattened = flatten_background(gray, radius=55)
    flattened = ImageOps.autocontrast(flattened, cutoff=0.2)
    denoised = flattened.filter(ImageFilter.MedianFilter(size=3))
    array = np.asarray(denoised, dtype=np.uint8)
    threshold = max(95, min(215, otsu_threshold(denoised) + 18))
    binary = np.where(array < threshold, 0, 255).astype(np.uint8)
    cleaned = Image.fromarray(binary, "L").filter(ImageFilter.MedianFilter(size=3))
    cleaned.info["deskew_angle"] = angle
    return clean_borders(cleaned, margin=18)


def enhance_page(image: Image.Image, document: SupplementalDocument) -> tuple[Image.Image, float]:
    gray = image.convert("L")
    if document.cleanup_profile == "typed-pages":
        cleaned = cleanup_typed_page(gray)
        angle = float(cleaned.info.get("deskew_angle", 0.0))
    else:
        cleaned = cleanup_folded_sheet(gray)
        angle = 0.0
    return cleaned.convert("RGB"), angle


def normalize_to_canvas(image: Image.Image) -> tuple[Image.Image, tuple[int, int]]:
    target_width, target_height = TARGET_SIZE
    if image.width != target_width:
        scale = target_width / image.width
        image = image.resize((target_width, round(image.height * scale)), Image.Resampling.LANCZOS)
    if image.height > target_height:
        image = image.crop((0, 0, target_width, target_height))
    canvas = Image.new("RGB", TARGET_SIZE, "white")
    paste_x = max(0, (target_width - image.width) // 2)
    paste_y = max(0, (target_height - image.height) // 2)
    canvas.paste(image, (paste_x, paste_y))
    return canvas, (paste_x, paste_y)


def process_document(document: SupplementalDocument) -> list[PageRecord]:
    out_dir = processed_dir(document)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[PageRecord] = []
    for page_number, source in enumerate(raw_scan_paths(document), start=1):
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)
            source_size = image.size
            enhanced, angle = enhance_page(image, document)
            normalized, offset = normalize_to_canvas(enhanced)
        output_path = out_dir / f"page-{page_number:03d}.jpg"
        normalized.save(output_path, quality=95, subsampling=0, dpi=(DPI, DPI))
        records.append(
            PageRecord(
                page_number=page_number,
                source_path=source.relative_to(ROOT).as_posix(),
                output_path=output_path.relative_to(ROOT).as_posix(),
                source_size=source_size,
                canvas_size=TARGET_SIZE,
                paste_offset=offset,
                cleanup_profile=document.cleanup_profile,
                deskew_angle=round(angle, 2),
            )
        )
    write_document_manifest(document, records)
    return records


def write_document_manifest(document: SupplementalDocument, records: list[PageRecord]) -> None:
    payload = {
        "schema_version": "alain_lessard_supplemental_document_v1",
        "slug": document.slug,
        "title": document.title,
        "description": document.description,
        "source_dir": document.raw_dir.relative_to(ROOT).as_posix(),
        "processed_dir": processed_dir(document).relative_to(ROOT).as_posix(),
        "cleanup_profile": document.cleanup_profile,
        "page_count": len(records),
        "target_size": TARGET_SIZE,
        "dpi": DPI,
        "records": [asdict(record) for record in records],
    }
    document_output_dir(document).mkdir(parents=True, exist_ok=True)
    (document_output_dir(document) / "manifest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def work_page_paths(document: SupplementalDocument, profile: str) -> list[Path]:
    source_pages = sorted(processed_dir(document).glob("page-*.jpg"))
    if not source_pages:
        raise SystemExit(f"No processed pages found for {document.slug}. Run process first.")
    profile_dir = work_dir(document, profile)
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    quality = 95 if profile == "archival" else 86
    output_paths: list[Path] = []
    for source in source_pages:
        output_path = profile_dir / source.name
        with Image.open(source) as image:
            image = image.convert("L")
            image.save(output_path, quality=quality, dpi=(DPI, DPI))
        output_paths.append(output_path)
    return output_paths


def build_image_pdf(document: SupplementalDocument, profile: str) -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    pages = work_page_paths(document, profile)
    output_pdf = image_pdf_path(document, profile)
    subprocess.run(
        [
            require_binary("img2pdf"),
            "--imgsize",
            f"{DPI}dpi",
            "--output",
            str(output_pdf),
            *[str(path) for path in pages],
        ],
        check=True,
    )
    print(f"{document.slug} {profile} image-only PDF: {output_pdf.relative_to(ROOT)}")


def ocr_pdf(document: SupplementalDocument, profile: str) -> None:
    image_pdf = image_pdf_path(document, profile)
    searchable_pdf = searchable_pdf_path(document, profile)
    if not image_pdf.exists():
        raise SystemExit(f"Image-only PDF missing: {image_pdf}")
    searchable_pdf.parent.mkdir(parents=True, exist_ok=True)
    if searchable_pdf.exists():
        searchable_pdf.unlink()

    command = [
        require_binary("ocrmypdf"),
        "--output-type",
        "pdf" if profile == "archival" else "pdfa",
        "--optimize",
        "0" if profile == "archival" else "1",
        "-l",
        "eng",
        "--title",
        document.title,
        "--author",
        "Alain-Lessard Family Archive",
        "--subject",
        document.description,
        "--keywords",
        "Alain Lessard, family archive, supplemental document, genealogy",
    ]
    if profile == "distribution":
        command.extend(["--force-ocr", "--deskew"])
    command.extend([str(image_pdf), str(searchable_pdf)])
    subprocess.run(command, check=True)
    print(f"{document.slug} {profile} searchable PDF: {searchable_pdf.relative_to(ROOT)}")


def write_text(document: SupplementalDocument) -> str:
    pdf = searchable_pdf_path(document, "distribution")
    reader = PdfReader(str(pdf))
    text = "\n\n".join(clean_text(page.extract_text() or "") for page in reader.pages)
    text_path(document).write_text(text.strip() + "\n", encoding="utf-8")
    return text


def write_index_manifest() -> None:
    documents = []
    for document in DOCUMENTS:
        doc_manifest_path = document_output_dir(document) / "manifest.json"
        if not doc_manifest_path.exists():
            continue
        doc_manifest = json.loads(doc_manifest_path.read_text(encoding="utf-8"))
        documents.append(
            {
                "slug": document.slug,
                "title": document.title,
                "description": document.description,
                "source_dir": document.raw_dir.relative_to(ROOT).as_posix(),
                "page_count": doc_manifest["page_count"],
                "manifest": doc_manifest_path.relative_to(ROOT).as_posix(),
                "processed_dir": processed_dir(document).relative_to(ROOT).as_posix(),
                "text": text_path(document).relative_to(ROOT).as_posix(),
                "pdfs": {
                    "distribution": searchable_pdf_path(document, "distribution").relative_to(ROOT).as_posix(),
                    "archival": searchable_pdf_path(document, "archival").relative_to(ROOT).as_posix(),
                },
            }
        )
    payload = {
        "schema_version": "alain_lessard_supplemental_documents_v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "document_count": len(documents),
        "documents": documents,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_all() -> int:
    for document in DOCUMENTS:
        records = process_document(document)
        print(f"{document.slug}: processed {len(records)} pages")
        for profile in ("distribution", "archival"):
            build_image_pdf(document, profile)
            ocr_pdf(document, profile)
        write_text(document)
    write_index_manifest()
    return 0


def validate() -> int:
    manifest_path = OUTPUT_ROOT / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit("Supplemental manifest missing. Run `make supplemental-docs` first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("document_count") != len(DOCUMENTS):
        errors.append(f"document_count is {manifest.get('document_count')}, expected {len(DOCUMENTS)}")

    for document in DOCUMENTS:
        expected_count = len(raw_scan_paths(document))
        doc_manifest_path = document_output_dir(document) / "manifest.json"
        if not doc_manifest_path.exists():
            errors.append(f"missing document manifest for {document.slug}")
            continue
        doc_manifest = json.loads(doc_manifest_path.read_text(encoding="utf-8"))
        if doc_manifest.get("page_count") != expected_count:
            errors.append(f"{document.slug} page_count is {doc_manifest.get('page_count')}, expected {expected_count}")
        text = text_path(document).read_text(encoding="utf-8") if text_path(document).exists() else ""
        if len(text.strip()) < 100:
            errors.append(f"{document.slug} OCR text is unexpectedly short: {len(text.strip())} chars")
        for profile in ("distribution", "archival"):
            pdf = searchable_pdf_path(document, profile)
            if not pdf.exists():
                errors.append(f"missing {profile} PDF for {document.slug}: {pdf}")
                continue
            reader = PdfReader(str(pdf))
            if len(reader.pages) != expected_count:
                errors.append(f"{document.slug} {profile} PDF has {len(reader.pages)} pages, expected {expected_count}")
            metadata = reader.metadata or {}
            if metadata.get("/Title") != document.title:
                errors.append(f"{document.slug} {profile} title metadata is {metadata.get('/Title')!r}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"supplemental documents: {manifest.get('document_count')}")
    for document in DOCUMENTS:
        print(f"{document.slug}: {len(raw_scan_paths(document))} pages")
    return 0


def render_checks() -> int:
    pdftoppm = require_binary("pdftoppm")
    for document in DOCUMENTS:
        pdf = searchable_pdf_path(document, "distribution")
        if not pdf.exists():
            raise SystemExit(f"Missing searchable PDF: {pdf}")
        out_dir = RENDERED_ROOT / document.slug
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        page_count = len(raw_scan_paths(document))
        sample_pages = sorted({1, max(1, page_count // 2), page_count})
        for page_number in sample_pages:
            prefix = out_dir / f"page-{page_number:03d}"
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
                    str(pdf),
                    str(prefix),
                ],
                check=True,
            )
        print(f"{document.slug} rendered checks: {out_dir.relative_to(ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process supplemental Alain Lessard archive scans.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("all")
    subparsers.add_parser("validate")
    subparsers.add_parser("render-checks")
    args = parser.parse_args(argv)

    if args.command == "all":
        return build_all()
    if args.command == "validate":
        return validate()
    if args.command == "render-checks":
        return render_checks()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
