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

from scripts.build_family_site import (  # noqa: E402
    Entry,
    entry_meta_label,
    html_to_text,
    load_bundle,
    ordered_entries,
    read_article_html,
)


DEFAULT_OUTPUT_DIR = ROOT / "audiobook" / "script"
MANIFEST_PATH = ROOT / "audiobook" / "manifest.json"
README_PATH = ROOT / "audiobook" / "README.md"
SKIP_AUDIO_TAGS = {"figure", "table", "nav", "script", "style"}
VOICE = {
    "provider": "ElevenLabs",
    "name": "Matilda",
    "voice_id": "XrExE9yKIg1WjnnlVkGX",
}


def slug_title(index: int, title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{index:02d}-{slug or 'chapter'}.md"


def normalized_audio_blocks(article_html: str) -> list[str]:
    text = html_to_text(article_html, skip_tags=SKIP_AUDIO_TAGS)
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    kept: list[str] = []
    for block in blocks:
        if is_reference_block(block):
            continue
        kept.append(block)
    return kept


def is_reference_block(block: str) -> bool:
    words = block.split()
    digits = sum(char.isdigit() for char in block)
    letters = sum(char.isalpha() for char in block)
    if len(words) <= 3 and digits >= 2:
        return True
    if digits > 12 and letters < 40:
        return True
    if block.count(".") > 12 and len(words) < 90:
        return True
    if re.fullmatch(r"[\d\s.,:;()/-]+", block):
        return True
    return False


def skip_reason(entry: Entry, article_html: str, blocks: list[str]) -> str | None:
    title = entry.title.lower()
    word_count = sum(len(block.split()) for block in blocks)
    table_count = article_html.lower().count("<table")
    if entry.kind != "chapter":
        return "page-level material"
    if "personal records" in title:
        return "personal records tables"
    if "bibliography" in title:
        return "bibliography"
    if entry.source_pages and set(entry.source_pages).issubset({1, 2}):
        return "cover and title pages"
    if table_count >= 3 and word_count < 1200:
        return "table-heavy reference section"
    if word_count < 180:
        return "too short for narration"
    return None


def render_script(index: int, entry: Entry, blocks: list[str]) -> str:
    body = "\n\n".join(blocks)
    source_label = entry_meta_label(entry)
    return f"""# {index:02d}. {entry.title}

Source: {source_label or entry.entry_id}

Narration note: This script is prepared for an Onward-style family audiobook. Dense genealogy tables, indexes, source lists, and personal-record forms are intentionally kept out of the audio lane and remain available in the website and PDFs.

---

{body}
"""


def build(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.md"):
        old.unlink()

    bundle = load_bundle()
    entries = ordered_entries(bundle)
    manifest_entries: list[dict[str, object]] = []
    skipped_entries: list[dict[str, object]] = []
    audio_index = 1

    for entry in entries:
        article_html = read_article_html(bundle, entry)
        blocks = normalized_audio_blocks(article_html)
        reason = skip_reason(entry, article_html, blocks)
        if reason:
            skipped_entries.append(
                {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "reason": reason,
                    "source_label": entry_meta_label(entry),
                    "table_count": article_html.lower().count("<table"),
                }
            )
            continue

        filename = slug_title(audio_index, entry.title)
        path = output_dir / filename
        path.write_text(render_script(audio_index, entry, blocks), encoding="utf-8")
        manifest_entries.append(
            {
                "index": audio_index,
                "entry_id": entry.entry_id,
                "title": entry.title,
                "script": f"script/{filename}",
                "source_label": entry_meta_label(entry),
                "status": "script-ready",
                "audio_file": None,
            }
        )
        audio_index += 1

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "schema_version": "alain_lessard_audiobook_manifest_v2",
                "mode": "onward-style-narrative-audio",
                "preferred_voice": VOICE,
                "note": "Scripts are prepared for narrative entries only; genealogy tables, personal records, bibliography, and page-level reference material remain readable/searchable.",
                "entries": manifest_entries,
                "skipped_entries": skipped_entries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    README_PATH.write_text(
        "# Alain Lessard Audio Companion\n\n"
        "The audio is generated by ElevenLabs using the voice \"Matilda\" "
        "(voiceId: XrExE9yKIg1WjnnlVkGX).\n\n"
        "This folder contains Onward-style narration scripts generated from the structured book HTML. "
        "The scripts include narrative sections and intentionally exclude genealogy tables, dense lists, personal-record forms, source lists, and page-level reference entries.\n\n"
        "When reviewed MP3 files are ready, add their public paths to `manifest.json` and rebuild the site.\n",
        encoding="utf-8",
    )
    print(f"built audiobook scripts: {output_dir}")
    print(f"scripts: {len(manifest_entries)}")
    print(f"skipped reference entries: {len(skipped_entries)}")
    print(f"manifest: {MANIFEST_PATH}")


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Build Onward-style audiobook scripts from the active doc-web HTML bundle.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    build(Path(args.output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
