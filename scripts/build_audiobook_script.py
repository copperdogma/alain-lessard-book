#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_family_site import SECTIONS, load_page_texts  # noqa: E402


DEFAULT_OUTPUT_DIR = ROOT / "audiobook" / "script"
MANIFEST_PATH = ROOT / "audiobook" / "manifest.json"
README_PATH = ROOT / "audiobook" / "README.md"


def slug_title(index: int, title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{index:02d}-{slug}.md"


def normalize_for_audio(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    kept: list[str] = []
    for line in lines:
        if not line:
            kept.append("")
            continue
        if re.fullmatch(r"\d{1,3}", line):
            continue
        if line.count(".") > 8:
            continue
        digits = sum(char.isdigit() for char in line)
        letters = sum(char.isalpha() for char in line)
        if digits > 8 and letters < 18:
            continue
        if len(line.split()) <= 3 and digits >= 2:
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraphs(text: str) -> list[str]:
    text = normalize_for_audio(text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) <= 1:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        blocks = []
        current: list[str] = []
        for line in lines:
            is_heading = len(line) < 70 and sum(ch.isupper() for ch in line if ch.isalpha()) > 0.65 * max(1, sum(ch.isalpha() for ch in line))
            if is_heading and current:
                blocks.append(" ".join(current))
                current = [line.title()]
            else:
                current.append(line)
        if current:
            blocks.append(" ".join(current))
    return [re.sub(r"\s+", " ", block).strip() for block in blocks if block.strip()]


def render_script(index: int, title: str, source_pages: tuple[int, int], text: str) -> str:
    body = "\n\n".join(paragraphs(text))
    return f"""# {title}

Source pages: {source_pages[0]}-{source_pages[1]}

Narration note: This script is prepared for an Onward-style family audiobook. Dense genealogy tables, lists, indexes, and reference structures are intentionally kept out of the audio lane and remain available in the website and PDFs.

---

{body}
"""


def build(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.md"):
        old.unlink()

    page_texts = load_page_texts()
    manifest_entries: list[dict[str, object]] = []
    audio_index = 1
    for section in SECTIONS:
        if not section.audio:
            continue
        text = "\n\n".join(page_texts.get(page, "") for page in range(section.start_page, section.end_page + 1))
        filename = slug_title(audio_index, section.title)
        path = output_dir / filename
        path.write_text(
            render_script(audio_index, section.title, (section.start_page, section.end_page), text),
            encoding="utf-8",
        )
        manifest_entries.append(
            {
                "index": audio_index,
                "title": section.title,
                "script": f"script/{filename}",
                "source_pages": [section.start_page, section.end_page],
                "status": "script-ready",
                "audio_file": None,
            }
        )
        audio_index += 1

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "schema_version": "alain_lessard_audiobook_manifest_v1",
                "mode": "onward-style-narrative-audio",
                "note": "Scripts are prepared for narrative sections only; genealogy tables and indexes remain readable/searchable.",
                "entries": manifest_entries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    README_PATH.write_text(
        "# Alain Lessard Audio Companion\n\n"
        "This folder contains Onward-style narration scripts generated from the cleaned OCR text. "
        "The scripts include narrative sections and intentionally exclude genealogy tables, dense lists, and the printed index.\n\n"
        "When ElevenLabs or another narration workflow produces MP3 files, add them to a local audio folder and update `manifest.json` with public audio paths before rebuilding the site.\n",
        encoding="utf-8",
    )
    print(f"built audiobook scripts: {output_dir}")
    print(f"manifest: {MANIFEST_PATH}")


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Build Onward-style audiobook scripts for narrative sections.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    build(Path(args.output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
