#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageOps


DEFAULT_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
DARK_THRESHOLD = 70
SCORE_THRESHOLD = 0.65
SMOOTHING_WINDOW = 9


def scan_paths(input_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    paths = [
        path
        for path in input_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in extensions
        and not any(part.startswith(".") for part in path.relative_to(input_dir).parts)
    ]
    return sorted(paths)


def count_key(value: Any) -> str:
    if isinstance(value, tuple):
        return "x".join(str(item) for item in value)
    if value is None:
        return "none"
    return str(value)


def counter_payload(counter: Counter[Any]) -> dict[str, int]:
    return {count_key(key): value for key, value in counter.most_common()}


def exif_payload(image: Image.Image) -> dict[str, Any]:
    exif = image.getexif()
    if not exif:
        return {}
    return {
        "make": exif.get(271),
        "model": exif.get(272),
        "orientation": exif.get(274),
        "x_resolution": str(exif.get(282)) if exif.get(282) is not None else None,
        "y_resolution": str(exif.get(283)) if exif.get(283) is not None else None,
        "resolution_unit": exif.get(296),
        "software": exif.get(305),
        "datetime": exif.get(306),
    }


def rgb_channels_identical(image: Image.Image) -> bool | None:
    if image.mode not in {"RGB", "RGBA"}:
        return None
    rgb = image.convert("RGB")
    red, green, blue = rgb.split()
    return (
        ImageChops.difference(red, green).getbbox() is None
        and ImageChops.difference(red, blue).getbbox() is None
    )


def smooth_scores(scores: np.ndarray) -> np.ndarray:
    kernel = np.ones(SMOOTHING_WINDOW) / SMOOTHING_WINDOW
    return np.convolve(scores, kernel, mode="same")


def dark_band_signal(image: Image.Image) -> dict[str, Any]:
    gray = ImageOps.exif_transpose(image).convert("L")
    arr = np.asarray(gray)
    height, width = arr.shape
    dark_fraction_by_row = (arr < DARK_THRESHOLD).mean(axis=1)
    smoothed = smooth_scores(dark_fraction_by_row)

    top_ignore = min(80, max(0, height // 10))
    bottom_ignore = min(80, max(0, height // 10))
    top_start = top_ignore
    top_end = max(top_start + 1, int(height * 0.35))
    bottom_start = min(height - 1, int(height * 0.65))
    bottom_end = max(bottom_start + 1, height - bottom_ignore)

    top_region = smoothed[top_start:top_end]
    bottom_region = smoothed[bottom_start:bottom_end]

    top_peak = int(np.argmax(top_region) + top_start) if len(top_region) else None
    bottom_peak = int(np.argmax(bottom_region) + bottom_start) if len(bottom_region) else None
    top_score = float(smoothed[top_peak]) if top_peak is not None else 0.0
    bottom_score = float(smoothed[bottom_peak]) if bottom_peak is not None else 0.0

    side = "none"
    if top_score >= SCORE_THRESHOLD and top_score >= bottom_score * 0.97:
        side = "top"
    elif bottom_score >= SCORE_THRESHOLD:
        side = "bottom"

    return {
        "side": side,
        "top_score": round(top_score, 6),
        "bottom_score": round(bottom_score, 6),
        "top_peak_y": top_peak,
        "bottom_peak_y": bottom_peak,
        "threshold": SCORE_THRESHOLD,
        "image_width": width,
        "image_height": height,
    }


def inspect_image(path: Path, input_dir: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        dpi = image.info.get("dpi")
        exif = exif_payload(image)
        channel_identical = rgb_channels_identical(image)
        band_signal = dark_band_signal(image)
        return {
            "path": path.relative_to(input_dir).as_posix(),
            "absolute_path": str(path.resolve()),
            "suffix": path.suffix.lower(),
            "bytes": path.stat().st_size,
            "mode": image.mode,
            "components": len(image.getbands()),
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "dpi": dpi,
            "exif": exif,
            "rgb_channels_identical": channel_identical,
            "dark_band_signal": band_signal,
        }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = Counter(tuple(record["size"]) for record in records)
    modes = Counter(record["mode"] for record in records)
    components = Counter(record["components"] for record in records)
    suffixes = Counter(record["suffix"] for record in records)
    dpi = Counter(tuple(record["dpi"]) if record["dpi"] else None for record in records)
    platen_sides = Counter(record["dark_band_signal"]["side"] for record in records)

    rgb_records = [record for record in records if record["rgb_channels_identical"] is not None]
    rgb_identical = [record for record in rgb_records if record["rgb_channels_identical"] is True]
    rgb_non_identical = [record for record in rgb_records if record["rgb_channels_identical"] is False]

    first = records[0] if records else None
    after_first = records[1:]
    after_first_rgb = [record for record in after_first if record["rgb_channels_identical"] is not None]
    after_first_all_identical = bool(after_first_rgb) and all(
        record["rgb_channels_identical"] is True for record in after_first_rgb
    )
    first_color_candidate = bool(first and first["rgb_channels_identical"] is False)

    byte_values = [record["bytes"] for record in records]
    recommendations: list[str] = []
    if first_color_candidate and after_first_all_identical:
        recommendations.append("Treat page 1 as a color cover and non-cover pages as grayscale source pages.")
    elif rgb_non_identical:
        recommendations.append("Review color handling page-by-page; more than one RGB image has non-identical channels.")
    elif rgb_identical:
        recommendations.append("Treat RGB images with identical channels as grayscale content unless visual review says otherwise.")
    if platen_sides.get("top") or platen_sides.get("bottom"):
        recommendations.append("Expect platen-band crop logic to need top/bottom side detection and contact-sheet review.")
    if len(dimensions) > 1:
        recommendations.append("Normalize processed pages to one target canvas before PDF assembly.")

    return {
        "count": len(records),
        "suffixes": counter_payload(suffixes),
        "dimensions": counter_payload(dimensions),
        "modes": counter_payload(modes),
        "components": counter_payload(components),
        "dpi": counter_payload(dpi),
        "platen_side_signals": counter_payload(platen_sides),
        "rgb_channel_check": {
            "checked": len(rgb_records),
            "identical": len(rgb_identical),
            "non_identical": len(rgb_non_identical),
            "non_identical_examples": [record["path"] for record in rgb_non_identical[:20]],
            "first_image_non_identical": first_color_candidate,
            "after_first_all_identical": after_first_all_identical,
        },
        "bytes": {
            "min": min(byte_values) if byte_values else 0,
            "max": max(byte_values) if byte_values else 0,
            "total": sum(byte_values),
        },
        "recommendations": recommendations,
    }


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Scan Intake Report",
        "",
        f"- Input directory: `{payload['input_dir']}`",
        f"- Generated: `{payload['generated_at']}`",
        f"- Files: `{summary['count']}`",
        "",
        "## Summary",
        "",
        f"- Extensions: `{summary['suffixes']}`",
        f"- Dimensions: `{summary['dimensions']}`",
        f"- Modes: `{summary['modes']}`",
        f"- Components: `{summary['components']}`",
        f"- DPI: `{summary['dpi']}`",
        f"- Platen side signals: `{summary['platen_side_signals']}`",
        "",
        "## RGB Channel Check",
        "",
        f"- RGB-like files checked: `{summary['rgb_channel_check']['checked']}`",
        f"- Identical channels: `{summary['rgb_channel_check']['identical']}`",
        f"- Non-identical channels: `{summary['rgb_channel_check']['non_identical']}`",
        f"- First image non-identical: `{summary['rgb_channel_check']['first_image_non_identical']}`",
        f"- After first all identical: `{summary['rgb_channel_check']['after_first_all_identical']}`",
        "",
        "## Recommendations",
        "",
    ]
    if summary["recommendations"]:
        lines.extend(f"- {recommendation}" for recommendation in summary["recommendations"])
    else:
        lines.append("- No automatic recommendations. Review records and rendered samples manually.")

    lines.extend(
        [
            "",
            "## First Records",
            "",
            "| # | Path | Mode | Size | Bytes | RGB channels identical | Platen signal |",
            "|---:|---|---|---|---:|---|---|",
        ]
    )
    for index, record in enumerate(payload["records"][:20], start=1):
        signal = record["dark_band_signal"]
        lines.append(
            "| {index} | `{path}` | `{mode}` | `{width}x{height}` | {bytes} | `{channels}` | `{side}` top={top} bottom={bottom} |".format(
                index=index,
                path=record["path"],
                mode=record["mode"],
                width=record["width"],
                height=record["height"],
                bytes=record["bytes"],
                channels=record["rgb_channels_identical"],
                side=signal["side"],
                top=signal["top_score"],
                bottom=signal["bottom_score"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a folder of book scans before building a scan-to-PDF pipeline.")
    parser.add_argument("input_dir", nargs="?", default="input/raw scans/main book")
    parser.add_argument("--output-dir", default="output/intake")
    parser.add_argument(
        "--extensions",
        default=",".join(DEFAULT_EXTENSIONS),
        help="Comma-separated file extensions to inspect. Default: .jpg,.jpeg,.png,.tif,.tiff",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir)
    extensions = tuple(extension.strip().lower() for extension in args.extensions.split(",") if extension.strip())

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")
    paths = scan_paths(input_dir, extensions)
    if not paths:
        raise SystemExit(f"No scan images found under {input_dir}")

    records = [inspect_image(path, input_dir) for path in paths]
    payload = {
        "schema_version": "book_scan_intake_report_v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input_dir": str(input_dir),
        "extensions": list(extensions),
        "summary": summarize(records),
        "records": records,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scan-intake-report.json"
    markdown_path = output_dir / "scan-intake-report.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(payload), encoding="utf-8")

    print(f"scan intake JSON: {json_path}")
    print(f"scan intake report: {markdown_path}")
    print(f"files: {payload['summary']['count']}")
    print(f"recommendations: {len(payload['summary']['recommendations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
