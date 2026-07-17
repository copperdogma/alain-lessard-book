#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audiobook import (  # noqa: E402
    AudiobookManifestError,
    load_audiobook_catalog,
    validate_audiobook_catalog,
)

DEFAULT_BUILD_DIR = ROOT / "build" / "family-site"
ASSET_VERSION = "20260716-semantic-reader-r2"
EXPECTED_ENTRY_COUNT = 39
EXPECTED_READING_SECTION_COUNT = 57
EXPECTED_SEARCH_ROW_COUNT = 59
EXPECTED_SUPPLEMENTAL_DOCUMENT_COUNT = 2
EXPECTED_HTML_PAGE_COUNT = 102
EXPECTED_DOC_WEB_IMAGES = 155
EXPECTED_DOC_WEB_BLOCK_IDS = 1737
EXPECTED_SCAN_IMAGES = 153
EXPECTED_FIGURES = 174
EXPECTED_FIGCAPTIONS_MIN = 140
EXPECTED_TABLES = 12
EXPECTED_PERSONAL_RECORD_TABLES = 8
EXPECTED_AUDIO_SCRIPT_COUNT = 52
COMPANION_CONTEXT_NOTE = "This document was not part of the main book; it was found tucked inside it."
EXPECTED_COMPANION_DOCUMENTS = (
    ("alains-song", "companion-alains-song.html", "Alain's Song", 6),
    ("growing-up-on-the-farm", "companion-growing-up-on-the-farm.html", "Growing Up on the Farm", 13),
)
EXPECTED_GROWING_UP_SECTION_HEADINGS = (
    "Growing Up On The Farm A Tribute To Mom And Dad",
    "GROWING UP",
    "SUMMER DAYS",
    "WINTER DAYS",
    "SCHOOL AT WHITE POPLAR",
    "DAD",
    "MOM",
    "FAMILY LIFE",
)

SITE_COPY_FILES = (
    "index.html",
    "book.html",
    "archive.html",
    "audiobook.html",
    "companion-alains-song.html",
    "companion-growing-up-on-the-farm.html",
)
READER_FACING_BANNED_PHRASES = (
    "audio handoff",
    "block provenance",
    "asset roots",
    "page-level material",
    "structured reading files",
    "reading manifest",
    "doc-web",
    "build process",
)
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "caption",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


@dataclass(frozen=True)
class LinkRef:
    source: Path
    tag: str
    attr: str
    value: str


@dataclass(frozen=True)
class ImageRef:
    source: Path
    attrs: dict[str, str]


class PageParser(HTMLParser):
    def __init__(self, source: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.ids: set[str] = set()
        self.links: list[LinkRef] = []
        self.images: list[ImageRef] = []
        self.audio_count = 0
        self.text_parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        for attr in ("href", "src"):
            if attr in attr_map:
                self.links.append(LinkRef(self.source, tag, attr, attr_map[attr]))
        if tag == "img":
            self.images.append(ImageRef(self.source, attr_map))
        if tag == "audio":
            self.audio_count += 1
        if self.skip_stack or tag in {"script", "style", "noscript"}:
            self.skip_stack.append(tag)
            return
        if tag in BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_stack:
            if tag == self.skip_stack[-1]:
                self.skip_stack.pop()
            elif tag in self.skip_stack:
                self.skip_stack = self.skip_stack[: self.skip_stack.index(tag)]
            return
        if tag in BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_stack and data.strip():
            self.text_parts.append(data)

    @property
    def visible_text(self) -> str:
        lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(self.text_parts).splitlines()]
        return "\n".join(line for line in lines if line)


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.error(message)


def rel(path: Path, build_dir: Path) -> str:
    try:
        return path.relative_to(build_dir).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path, validation: Validation, label: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        validation.error(f"Missing {label}: {path}")
    except json.JSONDecodeError as exc:
        validation.error(f"Invalid JSON in {label}: {path}: {exc}")
    return {}


def parse_html_pages(build_dir: Path, validation: Validation) -> dict[Path, PageParser]:
    pages = sorted(build_dir.glob("*.html"))
    validation.require(len(pages) == EXPECTED_HTML_PAGE_COUNT, f"Expected {EXPECTED_HTML_PAGE_COUNT} top-level HTML pages, found {len(pages)}")
    parsed: dict[Path, PageParser] = {}
    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = PageParser(page)
        parser.feed(text)
        parsed[page] = parser
        if page.name.startswith(("chapter-", "page-")):
            validation.require(
                'http-equiv="refresh"' in text and 'rel="canonical"' in text,
                f"{rel(page, build_dir)} should redirect to its semantic reading section",
            )
        else:
            validation.require("<main>" in text, f"{rel(page, build_dir)} is missing the main content wrapper")
        validation.require("</html>" in text.lower(), f"{rel(page, build_dir)} does not appear to be a complete HTML document")
    return parsed


def is_external_ref(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "mailto", "tel", "data", "javascript"} or value.startswith("//")


def local_target(build_dir: Path, source: Path, value: str) -> tuple[Path, str, str] | None:
    if not value or is_external_ref(value):
        return None
    parsed = urlparse(value)
    raw_path = unquote(parsed.path)
    if not raw_path:
        target = source
    elif raw_path.startswith("/"):
        target = build_dir / raw_path.lstrip("/")
    else:
        target = source.parent / raw_path
    if target.is_dir():
        target = target / "index.html"
    return target.resolve(), parsed.fragment, parsed.query


def check_local_links(build_dir: Path, parsed: dict[Path, PageParser], validation: Validation) -> set[str]:
    public_refs: set[str] = set()
    for page, parser in parsed.items():
        for link in parser.links:
            target_info = local_target(build_dir, page, link.value)
            if not target_info:
                continue
            target, fragment, query = target_info
            try:
                target.relative_to(build_dir.resolve())
            except ValueError:
                validation.error(f"{rel(page, build_dir)} links outside the build directory: {link.value}")
                continue
            display_target = rel(target, build_dir)
            public_ref = display_target + (f"?{query}" if query else "")
            public_refs.add(public_ref)
            if not target.exists():
                validation.error(f"{rel(page, build_dir)} has missing {link.attr}: {link.value}")
                continue
            if fragment and target.suffix == ".html":
                target_parser = parsed.get(target)
                if target_parser and fragment not in target_parser.ids:
                    validation.error(f"{rel(page, build_dir)} links to missing fragment #{fragment} in {display_target}")
    return public_refs


def check_required_pages(build_dir: Path, validation: Validation) -> None:
    manifest = read_json(build_dir / "data" / "structured-manifest.json", validation, "structured manifest")
    if not isinstance(manifest, dict):
        return
    entries = manifest.get("entries", [])
    reading_order = manifest.get("reading_order", [])
    validation.require(len(entries) == EXPECTED_ENTRY_COUNT, f"Expected {EXPECTED_ENTRY_COUNT} manifest entries, found {len(entries)}")
    validation.require(len(reading_order) == EXPECTED_ENTRY_COUNT, f"Expected {EXPECTED_ENTRY_COUNT} reading-order entries, found {len(reading_order)}")
    semantic = read_json(build_dir / "_internal" / "reading-sections.json", validation, "semantic reading manifest")
    semantic_sections = semantic.get("sections", []) if isinstance(semantic, dict) else []
    redirects = semantic.get("redirects", {}) if isinstance(semantic, dict) else {}
    validation.require(
        isinstance(semantic, dict) and semantic.get("schema_version") == "alain_semantic_reading_sections_v1",
        "Semantic reading manifest has the wrong schema version",
    )
    validation.require(
        len(semantic_sections) == EXPECTED_READING_SECTION_COUNT,
        f"Expected {EXPECTED_READING_SECTION_COUNT} semantic reading sections, found {len(semantic_sections)}",
    )
    source_entry_ids = {
        str(entry.get("entry_id"))
        for entry in entries
        if isinstance(entry, dict) and entry.get("entry_id")
    }
    covered_source_ids = {
        str(entry_id)
        for section in semantic_sections
        if isinstance(section, dict)
        for entry_id in section.get("source_entry_ids", [])
    }
    validation.require(
        covered_source_ids == source_entry_ids,
        "Semantic reading sections must cover every canonical doc-web source entry",
    )
    semantic_track_numbers = [
        int(number)
        for section in semantic_sections
        if isinstance(section, dict)
        for number in section.get("track_numbers", [])
    ]
    validation.require(
        semantic_track_numbers == list(range(2, 51)),
        f"Semantic reading sections should map tracks 02-50 exactly once, found {semantic_track_numbers}",
    )
    for section in semantic_sections:
        if not isinstance(section, dict):
            validation.error("Semantic reading manifest contains a non-object section")
            continue
        title = str(section.get("title") or "")
        path = str(section.get("path") or "")
        validation.require(not re.fullmatch(r"(?:Page|Image)\s+\w+", title, re.IGNORECASE), f"Semantic reading section has a print-artifact title: {title}")
        validation.require(path.startswith("read-") and path.endswith(".html"), f"Semantic reading section has an unstable path: {path}")
    built_block_ids = [
        block_id
        for section in semantic_sections
        if isinstance(section, dict) and section.get("path")
        for block_id in re.findall(
            r'\bid="(blk-[^"]+)"',
            (build_dir / str(section["path"])).read_text(encoding="utf-8")
            if (build_dir / str(section["path"])).is_file()
            else "",
        )
    ]
    validation.require(
        len(built_block_ids) == EXPECTED_DOC_WEB_BLOCK_IDS and len(set(built_block_ids)) == EXPECTED_DOC_WEB_BLOCK_IDS,
        f"Semantic reading sections should preserve {EXPECTED_DOC_WEB_BLOCK_IDS} unique doc-web block ids exactly once",
    )
    validation.require(
        isinstance(redirects, dict) and set(redirects) == source_entry_ids,
        "Every canonical doc-web entry should have a legacy-route redirect",
    )
    required = {"index.html", "book.html", "archive.html", "audiobook.html"}
    required.update(str(entry.get("path")) for entry in entries if isinstance(entry, dict) and entry.get("path"))
    required.update(str(section.get("path")) for section in semantic_sections if isinstance(section, dict) and section.get("path"))
    required.update(filename for _, filename, _, _ in EXPECTED_COMPANION_DOCUMENTS)
    for page in sorted(required):
        validation.require((build_dir / page).exists(), f"Required page is missing: {page}")


def check_search_index(build_dir: Path, validation: Validation) -> None:
    index_path = build_dir / "search-index.json"
    index = read_json(index_path, validation, "search index")
    if not isinstance(index, list):
        validation.error("Search index is not a JSON list")
        return
    validation.require(len(index) == EXPECTED_SEARCH_ROW_COUNT, f"Expected {EXPECTED_SEARCH_ROW_COUNT} search rows, found {len(index)}")
    supplemental_rows = [row for row in index if isinstance(row, dict) and str(row.get("entry_id") or "").startswith("supplemental-")]
    validation.require(len(supplemental_rows) == EXPECTED_SUPPLEMENTAL_DOCUMENT_COUNT, f"Expected {EXPECTED_SUPPLEMENTAL_DOCUMENT_COUNT} supplemental search rows, found {len(supplemental_rows)}")
    for row in supplemental_rows:
        url = str(row.get("url") or "")
        validation.require(url.startswith("companion-") and url.endswith(".html"), f"Supplemental search row should point at an HTML page, found {url}")
    for row_number, row in enumerate(index, start=1):
        if not isinstance(row, dict):
            validation.error(f"Search row {row_number} is not an object")
            continue
        url = str(row.get("url") or "")
        title = str(row.get("title") or "")
        text = str(row.get("text") or "")
        validation.require(bool(title), f"Search row {row_number} has no title")
        validation.require(bool(url), f"Search row {row_number} has no URL")
        validation.require("pages/" not in url, f"Search row {row_number} uses stale pages/ URL: {url}")
        if not str(row.get("entry_id") or "").startswith("supplemental-"):
            validation.require(url.startswith("read-"), f"Search row {row_number} should use a semantic reading route: {url}")
            validation.require(
                not re.fullmatch(r"(?:Page|Image)\s+\w+", title, re.IGNORECASE),
                f"Search row {row_number} exposes a print-artifact title: {title}",
            )
        parsed_url = urlparse(url)
        validation.require((build_dir / unquote(parsed_url.path)).exists(), f"Search row {row_number} points at missing page: {url}")
        validation.require(bool(text.strip()), f"Search row {row_number} has empty searchable text: {title or url}")


def check_assets_and_images(build_dir: Path, parsed: dict[Path, PageParser], validation: Validation) -> None:
    doc_web_images = sorted((build_dir / "images" / "doc-web").glob("*.jpg"))
    scan_images = sorted((build_dir / "images" / "scans").glob("*.jpg"))
    validation.require(len(doc_web_images) == EXPECTED_DOC_WEB_IMAGES, f"Expected {EXPECTED_DOC_WEB_IMAGES} doc-web image crops, found {len(doc_web_images)}")
    validation.require(len(scan_images) == EXPECTED_SCAN_IMAGES, f"Expected {EXPECTED_SCAN_IMAGES} source scan images, found {len(scan_images)}")

    seen_images: set[Path] = set()
    for page, parser in parsed.items():
        for image in parser.images:
            src = image.attrs.get("src", "")
            alt = image.attrs.get("alt", "")
            validation.require(bool(src), f"{rel(page, build_dir)} has an image without src")
            validation.require(bool(alt.strip()), f"{rel(page, build_dir)} has an image without useful alt text: {src}")
            target_info = local_target(build_dir, page, src)
            if not target_info:
                continue
            target, _, _ = target_info
            if target.exists():
                seen_images.add(target)

    for image_path in sorted(seen_images):
        try:
            with Image.open(image_path) as image:
                validation.require(image.width > 0 and image.height > 0, f"Image has invalid dimensions: {rel(image_path, build_dir)}")
        except Exception as exc:  # noqa: BLE001 - validation should report any image decoding problem.
            validation.error(f"Could not open image {rel(image_path, build_dir)}: {exc}")


def check_tables_figures_and_copy(build_dir: Path, parsed: dict[Path, PageParser], validation: Validation) -> None:
    html = "\n".join(path.read_text(encoding="utf-8") for path in sorted(parsed))
    table_count = html.lower().count("<table")
    table_scroll_count = html.count('class="table-scroll"')
    figure_count = html.lower().count("<figure")
    figcaption_count = html.lower().count("<figcaption")
    validation.require(table_count == EXPECTED_TABLES, f"Expected {EXPECTED_TABLES} tables, found {table_count}")
    validation.require(table_scroll_count == table_count, f"Expected every table to be wrapped for horizontal scrolling, found {table_scroll_count} wrappers for {table_count} tables")
    validation.require(figure_count == EXPECTED_FIGURES, f"Expected {EXPECTED_FIGURES} figures, found {figure_count}")
    validation.require(figcaption_count >= EXPECTED_FIGCAPTIONS_MIN, f"Expected at least {EXPECTED_FIGCAPTIONS_MIN} figcaptions, found {figcaption_count}")

    personal_records = build_dir / "read-reference-personal-records.html"
    if personal_records.exists():
        personal_text = personal_records.read_text(encoding="utf-8")
        personal_tables = personal_text.lower().count("<table")
        validation.require(
            personal_tables == EXPECTED_PERSONAL_RECORD_TABLES,
            f"Expected {EXPECTED_PERSONAL_RECORD_TABLES} personal-record tables in the Personal Records section, found {personal_tables}",
        )

    stale_patterns = ('href="pages/', 'src="pages/', '"url": "pages/')
    for path in [*sorted(parsed), build_dir / "search-index.json"]:
        text = path.read_text(encoding="utf-8")
        for pattern in stale_patterns:
            validation.require(pattern not in text, f"{rel(path, build_dir)} contains stale route pattern {pattern}")

    for filename in SITE_COPY_FILES:
        page = build_dir / filename
        parser = parsed.get(page)
        if not parser:
            validation.error(f"Missing site copy page: {filename}")
            continue
        lower_text = parser.visible_text.lower()
        for phrase in READER_FACING_BANNED_PHRASES:
            validation.require(phrase not in lower_text, f"{filename} exposes process wording to readers: {phrase}")

    for page in sorted(parsed):
        if page.name.startswith("read-"):
            text = page.read_text(encoding="utf-8")
            validation.require(
                bool(re.search(r'<section class="entry-header">.*?<h1>.*?</h1>', text, re.IGNORECASE | re.DOTALL)),
                f"{rel(page, build_dir)} is missing a semantic reader heading",
            )
    validation.require("<details" not in html, "Listening controls should not be hidden in disclosure panels")

    audiobook_text = parsed[build_dir / "audiobook.html"].visible_text.lower() if (build_dir / "audiobook.html") in parsed else ""
    validation.require("tables, indexes, and dense records stay" in audiobook_text, "Audiobook page should clearly explain why tables are not narrated")
    validation.require("page 1 page-level material" not in audiobook_text, "Audiobook page should not list raw page-level skip rows")
    script_dir = build_dir / "script"
    audio_scripts = sorted(script_dir.glob("*.md")) if script_dir.exists() else []
    validation.require(len(audio_scripts) == EXPECTED_AUDIO_SCRIPT_COUNT, f"Audiobook should publish {EXPECTED_AUDIO_SCRIPT_COUNT} scripts, found {len(audio_scripts)}")
    validation.require("preamble" in audiobook_text, "Audiobook page should link the opening preamble")
    validation.require("growing up on the farm" in audiobook_text, "Audiobook page should link the companion farm script")
    for script in audio_scripts:
        text = script.read_text(encoding="utf-8")
        validation.require(text.startswith("# "), f"{rel(script, build_dir)} should start with a Markdown H1")
        validation.require("Narration note:" not in text, f"{rel(script, build_dir)} should not include generator narration notes")
        validation.require("Source:" not in text, f"{rel(script, build_dir)} should not include source labels in the recording script")
        for marker in ("<table", "<article", "<nav", "<figure", "<img"):
            validation.require(marker not in text, f"{rel(script, build_dir)} should not expose raw HTML marker {marker}")

    audio_by_name = {script.name: script.read_text(encoding="utf-8") for script in audio_scripts}
    all_audio_text = "\n".join(audio_by_name.values())
    all_audio_lower = all_audio_text.lower()
    validation.require(
        "46-therese-lessard-macfarlane.md" in audio_by_name,
        "Audiobook should publish the restored Therese memoir as track 46",
    )
    validation.require(
        "46-paulette-mary-lessard.md" not in audio_by_name,
        "Audiobook should not publish Paulette's short reference profile as track 46",
    )
    for phrase in (
        "coat of arms",
        "riestap",
        "salted lard cake",
        "berthe and paul's family is as follows",
        "we've raised six children",
        "now here are all the children",
        "these are siméon and célinère's children",
        "information taken from *the oklee community story*",
    ):
        validation.require(phrase not in all_audio_lower, f"Audiobook should omit reference-first passage: {phrase}")
    for fragment in (
        "commu-nity",
        "crib-bage",
        "hav-ing",
        "meet-ing",
        "chil dren",
        "fol lowing",
        "jump ing",
        "stook ing",
        "throw ing",
    ):
        validation.require(fragment not in all_audio_text, f"Audiobook still contains split OCR word: {fragment}")
    validation.require("- - " not in all_audio_text, "Audiobook should not contain doubled list markers")
    validation.require(
        not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]-\n\n[a-zà-öø-ÿ]", all_audio_text),
        "Audiobook should not break hyphenated words across Markdown paragraphs",
    )
    expected_restorations = {
        "37-joseph-deride-lessard.md": "bright, breezy May afternoon",
        "39-martin-alphonse-lessard.md": "home to family and friends on Prince Street",
        "41-joseph-roland-donald-lessard.md": "both Helen and I retired in September 1981",
        "46-therese-lessard-macfarlane.md": "My full name is Marie Jeanne Therese",
    }
    for filename, phrase in expected_restorations.items():
        validation.require(
            phrase in audio_by_name.get(filename, ""),
            f"Audiobook should preserve restored page-boundary prose in {filename}: {phrase}",
        )
    validation.require(
        "Recently, I purchased a van" in audio_by_name.get("46-therese-lessard-macfarlane.md", ""),
        "Therese's restored memoir should include its closing paragraph",
    )
    for companion_script in ("script/51-alain-s-song.md", "script/52-growing-up-on-the-farm-a-tribute-to-mom-and-dad.md"):
        script_path = build_dir / companion_script
        if script_path.exists():
            validation.require(COMPANION_CONTEXT_NOTE in script_path.read_text(encoding="utf-8"), f"{companion_script} should include the companion-document context note")

    home_html = (build_dir / "index.html").read_text(encoding="utf-8")
    home_text = parsed[build_dir / "index.html"].visible_text if (build_dir / "index.html") in parsed else ""
    validation.require("Companion Documents" in home_text, "index.html should expose companion documents")
    validation.require("Alain's Song" in home_text, "index.html should link Alain's Song")
    validation.require("Growing Up on the Farm" in home_text, "index.html should link Growing Up on the Farm")
    validation.require(
        f'href="downloads/alains-song-searchable.pdf?v={ASSET_VERSION}"' in home_html,
        "index.html should link the Alain's Song reader PDF",
    )
    validation.require(
        f'href="downloads/growing-up-on-the-farm-searchable.pdf?v={ASSET_VERSION}"' in home_html,
        "index.html should link the Growing Up on the Farm reader PDF",
    )
    validation.require('href="companion-alains-song.html"' in home_html, "index.html should link the Alain's Song HTML page")
    validation.require('href="companion-growing-up-on-the-farm.html"' in home_html, "index.html should link the Growing Up on the Farm HTML page")
    start_reading_position = home_html.find("<h2>Start Reading</h2>")
    companion_position = home_html.find("<h2>Companion Documents</h2>")
    validation.require(
        start_reading_position >= 0 and companion_position >= 0 and start_reading_position < companion_position,
        "Home page should present Start Reading before the less-prominent companion documents",
    )
    start_reading_match = re.search(r"<h2>Start Reading</h2>.*?</section>", home_html, flags=re.IGNORECASE | re.DOTALL)
    if start_reading_match:
        start_reading_html = start_reading_match.group(0)
        validation.require("Printed page" not in start_reading_html, "Home Start Reading cards should not show printed-page metadata")
        validation.require("Source scan" not in start_reading_html, "Home Start Reading cards should not show source-scan metadata")
        validation.require('class="eyebrow">Page' not in start_reading_html, "Home Start Reading cards should not show generic Page labels")
    else:
        validation.error("Home page is missing the Start Reading section")

    book_path = build_dir / "book.html"
    book_html = book_path.read_text(encoding="utf-8") if book_path.exists() else ""
    book_text = parsed[book_path].visible_text if book_path in parsed else ""
    validation.require("Preface" in book_text, "book.html should expose Preface in the contents")
    validation.require("Part I - Alain Family History" in book_text, "book.html should expose Part I in the contents")
    validation.require("Part II - Alain Family Stories" in book_text, "book.html should expose Part II in the contents")
    validation.require("Henri Delphice Alain" in book_text, "book.html should expose the Henri Delphice Alain section")
    validation.require("Moise (Smokey) Alain" in book_text, "book.html should expose Moise Alain as a section")
    validation.require("Page Entries" not in book_text, "book.html should not split the contents into generic Page Entries")
    archive_text = parsed[build_dir / "archive.html"].visible_text if (build_dir / "archive.html") in parsed else ""
    archive_html = (build_dir / "archive.html").read_text(encoding="utf-8") if (build_dir / "archive.html").exists() else ""
    validation.require("Companion Documents" in archive_text, "archive.html should expose companion documents")
    validation.require("Alain's Song" in archive_text, "archive.html should list Alain's Song")
    validation.require("Growing Up on the Farm" in archive_text, "archive.html should list Growing Up on the Farm")
    validation.require('href="companion-alains-song.html"' in archive_html, "archive.html should link the Alain's Song HTML page")
    validation.require('href="companion-growing-up-on-the-farm.html"' in archive_html, "archive.html should link the Growing Up on the Farm HTML page")
    validation.require("Supplemental items can be added" not in archive_text, "archive.html should not describe companion documents as pending")
    generic_toc_links = re.findall(r'<li class="heading-level-[12]"><a href="[^"]+">((?:Page|Image) [^<]+)</a>', book_html)
    validation.require(not generic_toc_links, f"book.html TOC should not expose generic page/image labels: {generic_toc_links[:8]}")
    part_link_blocks = re.findall(r'<ol class="part-links">(.*?)</ol>', book_html, flags=re.IGNORECASE | re.DOTALL)
    validation.require(all("<span" not in block.lower() for block in part_link_blocks), "book.html TOC heading links should not include per-entry page labels")
    validation.require("scroll-padding-top: 6.5rem" in (build_dir / "assets" / "site.css").read_text(encoding="utf-8"), "site CSS should offset hash navigation for the sticky header")
    ordered_terms = (
        "Preface",
        "Part I - Alain Family History",
        "Part II - Alain Family Stories",
        "Louis and Clara (Lessard) Alain",
    )
    expanded_contents = book_text[book_text.rfind("Front Matter") :]
    if all(term in expanded_contents for term in ordered_terms):
        validation.require(
            [expanded_contents.index(term) for term in ordered_terms]
            == sorted(expanded_contents.index(term) for term in ordered_terms),
            "book.html contents order should follow front matter, Part I, Part II, then Louis and Clara",
        )


def check_asset_version(build_dir: Path, validation: Validation) -> None:
    book_html = (build_dir / "book.html").read_text(encoding="utf-8")
    search_js = (build_dir / "assets" / "search.js").read_text(encoding="utf-8")
    validation.require(f"assets/search.js?v={ASSET_VERSION}" in book_html, "book.html does not reference the current search.js asset version")
    validation.require(f"search-index.json?v={ASSET_VERSION}" in search_js, "search.js does not fetch the current search-index asset version")


def check_supplemental_downloads(build_dir: Path, validation: Validation) -> None:
    downloads = build_dir / "downloads"
    expected = (
        "alains-song-searchable.pdf",
        "alains-song-archival-searchable.pdf",
        "growing-up-on-the-farm-searchable.pdf",
        "growing-up-on-the-farm-archival-searchable.pdf",
    )
    for filename in expected:
        path = downloads / filename
        validation.require(path.exists(), f"Missing supplemental download: downloads/{filename}")
        if path.exists():
            validation.require(path.stat().st_size > 100_000, f"Supplemental download is unexpectedly small: downloads/{filename}")


def check_companion_document_pages(build_dir: Path, parsed: dict[Path, PageParser], validation: Validation) -> None:
    for slug, filename, title, page_count in EXPECTED_COMPANION_DOCUMENTS:
        page = build_dir / filename
        parser = parsed.get(page)
        validation.require(page.exists(), f"Missing companion document HTML page: {filename}")
        if not parser:
            continue
        html = page.read_text(encoding="utf-8")
        text = parser.visible_text
        validation.require(title in text, f"{filename} should expose the companion document title")
        validation.require(COMPANION_CONTEXT_NOTE in text, f"{filename} should explain that the document was tucked into the main book")
        validation.require("Readable Text" not in text, f"{filename} should not expose the old generic readable text label")
        validation.require("Source Pages" in text, f"{filename} should expose source page images")
        validation.require("Reader PDF" in text and "Archival PDF" in text, f"{filename} should keep PDF download links")
        if slug == "growing-up-on-the-farm":
            validation.require('class="companion-story-section"' in html, f"{filename} should render story-heading sections from accepted doc-web HTML")
        else:
            validation.require('class="doc-web-entry"' in html, f"{filename} should render accepted doc-web entry HTML")
            validation.require('class="companion-toc"' not in html, f"{filename} should not add a TOC to a short companion document")
        validation.require("<pre>" not in html, f"{filename} should not fall back to the old raw OCR transcript renderer")
        validation.require(
            f'href="downloads/{slug}-searchable.pdf?v={ASSET_VERSION}"' in html,
            f"{filename} should link the reader PDF with the current asset version",
        )
        validation.require(
            f'href="downloads/{slug}-archival-searchable.pdf?v={ASSET_VERSION}"' in html,
            f"{filename} should link the archival PDF with the current asset version",
        )
        image_refs = re.findall(rf'src="images/companion/{re.escape(slug)}/page-\d{{3}}\.jpg"', html)
        validation.require(len(image_refs) == page_count, f"{filename} should include {page_count} companion page images, found {len(image_refs)}")
        if slug == "alains-song":
            refrain_blocks = []
            unbold_refrains = []
            for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", html, flags=re.IGNORECASE | re.DOTALL):
                plain = re.sub(r"<br\s*/?>", " ", paragraph, flags=re.IGNORECASE)
                plain = re.sub(r"<[^>]+>", " ", plain)
                if not re.match(r"^\s*REFRAIN:?\b", plain, flags=re.IGNORECASE):
                    continue
                refrain_blocks.append(paragraph)
                stripped = paragraph.strip()
                if not (re.match(r"^<strong\b[^>]*>", stripped, flags=re.IGNORECASE) and re.search(r"</strong>\s*$", stripped, flags=re.IGNORECASE)):
                    unbold_refrains.append(stripped[:80])
            validation.require(len(refrain_blocks) == 10, f"{filename} should include 10 refrain stanzas, found {len(refrain_blocks)}")
            validation.require(not unbold_refrains, f"{filename} has unbolded refrain stanzas: {unbold_refrains[:3]}")
        if slug == "growing-up-on-the-farm":
            story_sections = re.findall(r'<section class="companion-story-section">(.*?)</section>', html, flags=re.IGNORECASE | re.DOTALL)
            section_headings = []
            for section in story_sections:
                match = re.search(r"<h[12]\b[^>]*>(.*?)</h[12]>", section, flags=re.IGNORECASE | re.DOTALL)
                if match:
                    section_headings.append(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(1))).strip())
            validation.require(len(story_sections) == len(EXPECTED_GROWING_UP_SECTION_HEADINGS), f"{filename} should render story-heading sections, found {len(story_sections)}")
            validation.require(tuple(section_headings) == EXPECTED_GROWING_UP_SECTION_HEADINGS, f"{filename} has unexpected story section headings: {section_headings}")
            validation.require('class="doc-web-entry"' not in html, f"{filename} should not expose page-break doc-web entry sections")
            toc_match = re.search(r'<nav\b[^>]*class="companion-toc"[^>]*>(.*?)</nav>', html, flags=re.IGNORECASE | re.DOTALL)
            validation.require(toc_match is not None, f"{filename} should expose a companion document TOC")
            if toc_match:
                toc_links = re.findall(r'<a href="#([^"]+)">(.*?)</a>', toc_match.group(1), flags=re.IGNORECASE | re.DOTALL)
                toc_headings = tuple(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip() for _, text in toc_links)
                validation.require(toc_headings == EXPECTED_GROWING_UP_SECTION_HEADINGS, f"{filename} has unexpected TOC headings: {toc_headings}")
                validation.require(all(anchor.startswith("blk-") for anchor, _ in toc_links), f"{filename} TOC should link to doc-web heading anchors")


def check_audiobook_surface(
    build_dir: Path,
    parsed: dict[Path, PageParser],
    validation: Validation,
    *,
    require_complete_audio: bool,
) -> list[str]:
    try:
        catalog = load_audiobook_catalog(ROOT / "audiobook" / "manifest.json")
    except AudiobookManifestError as exc:
        validation.error(f"Could not load canonical audiobook manifest: {exc}")
        return []

    if require_complete_audio:
        audio_validation = validate_audiobook_catalog(catalog, release=True, decode=False)
        for error in audio_validation.errors:
            validation.error(f"Release audiobook validation failed: {error}")

    script_mp3s = sorted((build_dir / "script").glob("*.mp3"))
    validation.require(not script_mp3s, f"MP3 files must not be published under script/: {[path.name for path in script_mp3s[:5]]}")
    internal_manifest = build_dir / "_internal" / "audiobook" / "manifest.json"
    validation.require(internal_manifest.is_file(), "Built site is missing its internal audiobook manifest snapshot")

    audiobook_page = build_dir / "audiobook.html"
    audiobook_html = audiobook_page.read_text(encoding="utf-8") if audiobook_page.is_file() else ""
    audiobook_parser = parsed.get(audiobook_page)
    available_tracks = [track for track in catalog.tracks if track.is_available]
    expected_player_count = len(available_tracks) + (1 if catalog.full_audiobook.is_available else 0)
    if audiobook_parser:
        validation.require(
            audiobook_parser.audio_count == expected_player_count,
            f"Audiobook page has {audiobook_parser.audio_count} players, expected {expected_player_count}",
        )
    validation.require(
        audiobook_html.count('class="audio-track-card"') == len(catalog.tracks),
        f"Audiobook page should render {len(catalog.tracks)} track cards",
    )
    validation.require("No app or account is needed" in audiobook_html, "Audiobook page should explain that no app or account is needed")
    validation.require("ElevenLabs Multilingual v2" in audiobook_html, "Audiobook page should identify the narration model")
    home_html = (build_dir / "index.html").read_text(encoding="utf-8") if (build_dir / "index.html").is_file() else ""
    validation.require('href="audiobook.html">Listen to the audiobook</a>' in home_html, "Homepage should provide a clear audiobook entry point")

    public_paths: list[str] = []
    for track in catalog.tracks:
        built_audio = build_dir / track.public_audio_path
        if track.is_available:
            validation.require(built_audio.is_file(), f"Built site is missing track {track.track_number:02d}: {track.public_audio_path}")
            if built_audio.is_file():
                validation.require(
                    built_audio.stat().st_size == track.audio_source_path.stat().st_size,
                    f"Built track {track.track_number:02d} size differs from its reviewed source",
                )
                public_paths.append(track.public_audio_path)
        if require_complete_audio:
            validation.require(built_audio.is_file(), f"Release build requires track {track.track_number:02d}: {track.public_audio_path}")

    full = catalog.full_audiobook
    built_full = build_dir / full.public_audio_path
    if full.is_available:
        validation.require(built_full.is_file(), f"Built site is missing the complete audiobook: {full.public_audio_path}")
        if built_full.is_file():
            validation.require(
                built_full.stat().st_size == full.audio_source_path.stat().st_size,
                "Built complete audiobook size differs from its generated source",
            )
            public_paths.append(full.public_audio_path)
    if require_complete_audio:
        validation.require(full.is_available, "Release build requires the generated complete audiobook source")
        validation.require(built_full.is_file(), "Release build requires the published complete audiobook")
        validation.require("Download complete audiobook" in audiobook_html, "Release audiobook page is missing its complete-book download")
        validation.require('id="full-audiobook"' in audiobook_html, "Release audiobook page is missing its complete-book section")

    semantic = read_json(build_dir / "_internal" / "reading-sections.json", validation, "semantic reading manifest")
    reading_paths_by_track: dict[int, str] = {}
    for section in semantic.get("sections", []) if isinstance(semantic, dict) else []:
        if not isinstance(section, dict):
            continue
        path = str(section.get("path") or "")
        for number in section.get("track_numbers", []):
            track_number = int(number)
            validation.require(track_number not in reading_paths_by_track, f"Track {track_number:02d} has multiple semantic reading targets")
            reading_paths_by_track[track_number] = path
    companion_paths = {
        f"companion:{slug}": filename
        for slug, filename, _title, _page_count in EXPECTED_COMPANION_DOCUMENTS
    }
    for track in catalog.tracks:
        companion_target = next((target for target in track.target_entry_ids if target.startswith("companion:")), None)
        target_path = reading_paths_by_track.get(track.track_number) or companion_paths.get(companion_target or "")
        card_match = re.search(
            rf'<article class="audio-track-card" id="track-{track.track_number:02d}">(.*?)</article>',
            audiobook_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        validation.require(card_match is not None, f"Audiobook page is missing track card {track.track_number:02d}")
        card_html = card_match.group(1) if card_match else ""
        read_links = re.findall(r'<a class="button" href="([^"]+)">Read</a>', card_html)
        if target_path:
            validation.require(read_links == [target_path], f"Track {track.track_number:02d} should expose exactly one Read link to {target_path}, found {read_links}")
            page_path = build_dir / target_path
            page_html = page_path.read_text(encoding="utf-8") if page_path.is_file() else ""
            validation.require(
                f'data-audio-key="{track.public_audio_path}"' in page_html,
                f"{target_path} is missing track {track.track_number:02d}",
            )
            validation.require(
                page_html.count('class="listen-bar"') == 1,
                f"{target_path} should expose one compact listening bar",
            )
            validation.require("<details" not in page_html, f"{target_path} should not hide audio in a disclosure")
            validation.require('class="listen-icon-mark"' in page_html, f"{target_path} should identify audio with the headphones icon")
            validation.require("&#9654;" not in page_html, f"{target_path} should not render a decorative play-button lookalike")
        else:
            validation.require(not read_links, f"Track {track.track_number:02d} should not expose a Read link")

    total_listen_bars = sum(
        path.read_text(encoding="utf-8").count('class="listen-bar"')
        for path in parsed
    )
    validation.require(total_listen_bars == 51, f"Expected 51 compact section listening bars, found {total_listen_bars}")

    audio_js = (build_dir / "assets" / "audio.js").read_text(encoding="utf-8") if (build_dir / "assets" / "audio.js").is_file() else ""
    for marker in ("localStorage", 'addEventListener("play"', "other.pause()", 'addEventListener("ended"'):
        validation.require(marker in audio_js, f"Audio playback enhancement is missing marker: {marker}")

    summary = read_json(build_dir / "_internal" / "build-summary.json", validation, "build summary")
    if isinstance(summary, dict):
        expected_published = len(available_tracks) + (1 if full.is_available else 0)
        validation.require(summary.get("audiobook_track_count") == len(catalog.tracks), "Build summary has the wrong audiobook track count")
        validation.require(summary.get("reading_section_count") == EXPECTED_READING_SECTION_COUNT, "Build summary has the wrong semantic reading-section count")
        validation.require(summary.get("published_audio_file_count") == expected_published, "Build summary has the wrong published audio count")
        validation.require(summary.get("complete_audiobook_published") is full.is_available, "Build summary has the wrong complete-audiobook state")

    if require_complete_audio:
        built_mp3s = sorted((build_dir / "audiobook").rglob("*.mp3"))
        validation.require(
            len(built_mp3s) == len(catalog.tracks) + 1,
            f"Release bundle should contain {len(catalog.tracks) + 1} audiobook MP3s, found {len(built_mp3s)}",
        )
    return public_paths


def fetch_public_audio(url: str, timeout: float) -> tuple[str, list[str]]:
    errors: list[str] = []
    headers = {"User-Agent": "alain-family-site-validator/1.0"}
    try:
        with urlopen(Request(url, headers=headers, method="HEAD"), timeout=timeout) as response:
            if response.getcode() != 200:
                errors.append(f"HEAD returned HTTP {response.getcode()}")
            content_type = response.headers.get_content_type()
            if content_type != "audio/mpeg":
                errors.append(f"Content-Type is {content_type!r}, expected 'audio/mpeg'")
            try:
                content_length = int(response.headers.get("Content-Length") or 0)
            except ValueError:
                content_length = 0
            if content_length <= 0:
                errors.append("Content-Length is missing or zero")
    except Exception as exc:  # noqa: BLE001 - public verification should retain exact network evidence.
        errors.append(f"HEAD failed: {exc}")
        return url, errors
    range_headers = dict(headers)
    range_headers["Range"] = "bytes=0-1023"
    try:
        with urlopen(Request(url, headers=range_headers, method="GET"), timeout=timeout) as response:
            if response.getcode() != 206:
                errors.append(f"Range request returned HTTP {response.getcode()}, expected 206")
            if not str(response.headers.get("Content-Range") or "").startswith("bytes 0-"):
                errors.append("Range response is missing a valid Content-Range header")
            response.read(1024)
    except Exception as exc:  # noqa: BLE001 - public verification should retain exact network evidence.
        errors.append(f"Range request failed: {exc}")
    return url, errors


def check_public_audio_assets(
    public_base: str,
    public_paths: Iterable[str],
    validation: Validation,
    timeout: float,
) -> None:
    urls = [public_url(public_base, path) for path in public_paths]
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_public_audio, url, timeout) for url in urls]
        for future in as_completed(futures):
            url, errors = future.result()
            for error in errors:
                validation.error(f"Public audiobook check failed for {url}: {error}")
    validation.note(f"Checked {len(urls)} public audiobook assets for MIME, length, and byte-range support.")


def public_url(base: str, ref: str) -> str:
    parsed = urlparse(ref)
    quoted_path = quote(parsed.path, safe="/._-~")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{base.rstrip('/')}/{quoted_path}{query}"


def fetch_public(url: str, timeout: float) -> tuple[str, str | None]:
    headers = {"User-Agent": "alain-family-site-validator/1.0"}
    last_error: str | None = None
    for method in ("HEAD", "GET"):
        method_headers = dict(headers)
        if method == "GET":
            method_headers["Range"] = "bytes=0-0"
        request = Request(url, headers=method_headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                if status < 400:
                    return url, None
                last_error = f"HTTP {status}"
        except HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            continue
        except URLError as exc:
            last_error = str(exc.reason)
            continue
        except TimeoutError:
            last_error = "timeout"
            continue
    return url, last_error or "unknown public fetch failure"


def check_public_site(build_dir: Path, public_base: str, refs: Iterable[str], validation: Validation, timeout: float) -> None:
    public_refs = set(refs)
    public_refs.update(path.name for path in build_dir.glob("*.html"))
    public_refs.add("search-index.json")
    public_refs.add(f"search-index.json?v={ASSET_VERSION}")

    base_urls = [public_base.rstrip("/") + "/", public_base.rstrip("/") + "/index.html"]
    all_urls = base_urls + [public_url(public_base, ref) for ref in sorted(public_refs) if not ref.startswith("_internal/")]
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_public, url, timeout) for url in all_urls]
        for future in as_completed(futures):
            url, error = future.result()
            if error:
                failures.append(f"{url}: {error}")
    for failure in sorted(failures):
        validation.error(f"Public URL check failed: {failure}")

    try:
        search_request = Request(
            public_base.rstrip("/") + f"/search-index.json?v={ASSET_VERSION}",
            headers={"User-Agent": "alain-family-site-validator/1.0"},
        )
        with urlopen(search_request, timeout=timeout) as response:
            public_index = json.loads(response.read().decode("utf-8"))
        validation.require(len(public_index) == EXPECTED_SEARCH_ROW_COUNT, f"Public search index has {len(public_index)} rows, expected {EXPECTED_SEARCH_ROW_COUNT}")
        stale_urls = [row.get("url") for row in public_index if isinstance(row, dict) and "pages/" in str(row.get("url") or "")]
        validation.require(not stale_urls, f"Public search index has stale pages/ URLs: {stale_urls[:5]}")
    except Exception as exc:  # noqa: BLE001 - public verification should surface the exact failure.
        validation.error(f"Could not verify public search index: {exc}")


def run_validation(
    build_dir: Path,
    public_base: str | None,
    timeout: float,
    *,
    require_complete_audio: bool = False,
) -> Validation:
    validation = Validation()
    validation.require(build_dir.exists(), f"Build directory does not exist: {build_dir}")
    if not build_dir.exists():
        return validation

    parsed = parse_html_pages(build_dir, validation)
    check_required_pages(build_dir, validation)
    public_refs = check_local_links(build_dir, parsed, validation)
    check_search_index(build_dir, validation)
    check_assets_and_images(build_dir, parsed, validation)
    check_tables_figures_and_copy(build_dir, parsed, validation)
    check_supplemental_downloads(build_dir, validation)
    check_companion_document_pages(build_dir, parsed, validation)
    public_audio_paths = check_audiobook_surface(
        build_dir,
        parsed,
        validation,
        require_complete_audio=require_complete_audio,
    )
    check_asset_version(build_dir, validation)
    validation.note(f"Checked {len(parsed)} HTML pages, {len(public_refs)} local references, and {EXPECTED_SEARCH_ROW_COUNT} search rows.")

    if public_base:
        check_public_site(build_dir, public_base, public_refs, validation, timeout)
        if require_complete_audio:
            check_public_audio_assets(public_base, public_audio_paths, validation, timeout)
        validation.note(f"Checked public host: {public_base.rstrip('/')}")
    return validation


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Validate the built Alain Lessard family site.")
    parser.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR), help="Built site directory to validate.")
    parser.add_argument("--public-base", default="", help="Optional public base URL to verify with HTTP requests.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout for public HTTP checks.")
    parser.add_argument(
        "--require-complete-audio",
        action="store_true",
        help="Require all 52 track MP3s plus the generated complete audiobook and release UI.",
    )
    args = parser.parse_args()

    build_dir = Path(args.build_dir).resolve()
    validation = run_validation(
        build_dir,
        args.public_base.strip() or None,
        args.timeout,
        require_complete_audio=args.require_complete_audio,
    )

    for note in validation.notes:
        print(f"NOTE: {note}")
    for warning in validation.warnings:
        print(f"WARNING: {warning}")
    if validation.errors:
        print(f"FAILED: {len(validation.errors)} issue(s)")
        for error in validation.errors:
            print(f"- {error}")
        return 1
    print("PASS: family site validation is clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
