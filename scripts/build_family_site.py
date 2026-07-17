#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audiobook import (  # noqa: E402
    AudiobookCatalog,
    AudiobookManifestError,
    AudiobookTrack,
    format_audio_duration,
    format_file_size,
    load_audiobook_catalog,
    tracks_by_target_entry_id,
    validate_audiobook_catalog,
)
from scripts.reading_sections import (  # noqa: E402
    ReadingCatalog,
    ReadingSection,
    ReadingSource,
    build_reading_catalog,
)
from scripts.portable_editions import (  # noqa: E402
    PortableCatalog,
    PortableEditionError,
    copy_portable_artifacts,
    load_portable_catalog,
    validate_epub,
)
from scripts.build_m4b import validate_m4b  # noqa: E402

ACTIVE_BUNDLE_PATH = ROOT / "input" / "doc-web-html" / "active-bundle.json"
PROCESSED_DIR = ROOT / "output" / "processed-pages"
PDF_DIR = ROOT / "output" / "pdf"
DISTRIBUTION_PDF = PDF_DIR / "alain-lessard-book-searchable.pdf"
ARCHIVAL_PDF = PDF_DIR / "alain-lessard-book-archival-searchable.pdf"
SUPPLEMENTAL_MANIFEST_PATH = ROOT / "output" / "supplemental-documents" / "manifest.json"
COMPANION_DOC_WEB_MANIFEST_PATH = ROOT / "input" / "doc-web-html" / "companion-documents" / "manifest.json"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "family-site"
AUDIOBOOK_MANIFEST_PATH = ROOT / "audiobook" / "manifest.json"
PORTABLE_MANIFEST_PATH = ROOT / "portable" / "manifest.json"

SITE_TITLE = "Alain Lessard"
SITE_SUBTITLE = "Our First Ancestors and A Compilation of Stories of Their Descendants"
PUBLIC_HOST = "https://alain-lessard.copper-dog.com"
BOOK_YEAR = "1987"
SITE_ASSET_VERSION = "20260717-portable-editions-r1"
COMPANION_CONTEXT_NOTE = "This document was not part of the main book; it was found tucked inside it."
AUDIOBOOK_ICON_SVG = (
    '<svg class="listen-icon-mark" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 4.5a6.75 6.75 0 0 0-6.75 6.75v4.5A2.25 2.25 0 0 0 7.5 18h.75a.75.75 0 0 0 .75-.75v-4.5a.75.75 0 0 0-.75-.75H6.75v-.75a5.25 5.25 0 1 1 10.5 0V12h-1.5a.75.75 0 0 0-.75.75v4.5a.75.75 0 0 0 .75.75h.75a2.25 2.25 0 0 0 2.25-2.25v-4.5A6.75 6.75 0 0 0 12 4.5Z" fill="currentColor"/>'
    '<path d="M9.75 18.75a.75.75 0 0 0 0 1.5h4.5a.75.75 0 0 0 0-1.5h-4.5Z" fill="currentColor"/>'
    "</svg>"
)

ARTICLE_RE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.IGNORECASE | re.DOTALL)
IMAGE_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=")images/', re.IGNORECASE)
GENERIC_TOC_HEADING_RE = re.compile(r"^(?:Page\s+(?:\d+|[ivxlcdm]+)|Image\s+\d+)$", re.IGNORECASE)
IMG_TAG_RE = re.compile(r"<img\b(?![^>]*\bloading=)", re.IGNORECASE)
DECORATIVE_FIGURE_RE = re.compile(
    r'<figure\b[^>]*>\s*<img\b(?![^>]*\bsrc=)[^>]*alt="Decorative line break"[^>]*/?>\s*</figure>',
    re.IGNORECASE,
)
NO_SRC_IMG_RE = re.compile(r"<img\b(?![^>]*\bsrc=)[^>]*>", re.IGNORECASE)
TABLE_RE = re.compile(r"(<table\b.*?</table>)", re.IGNORECASE | re.DOTALL)
P_TAG_RE = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", re.IGNORECASE | re.DOTALL)
SECTION_HEADING_RE = re.compile(r"(<h[12]\b[^>]*>.*?</h[12]>)", re.IGNORECASE | re.DOTALL)
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
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
class Bundle:
    root: Path
    manifest_path: Path
    provenance_path: Path | None
    manifest: dict
    active: dict


@dataclass(frozen=True)
class Entry:
    entry_id: str
    kind: str
    title: str
    path: str
    order: int
    source_pages: tuple[int, ...]
    printed_pages: tuple[int, ...]
    printed_page_start: int | None
    printed_page_end: int | None

    @classmethod
    def from_record(cls, record: dict) -> "Entry":
        return cls(
            entry_id=str(record["entry_id"]),
            kind=str(record.get("kind") or "entry"),
            title=str(record.get("title") or record["entry_id"]),
            path=str(record.get("path") or f"{record['entry_id']}.html"),
            order=int(record.get("order") or 0),
            source_pages=tuple(int(page) for page in record.get("source_pages") or []),
            printed_pages=tuple(int(page) for page in record.get("printed_pages") or [] if page is not None),
            printed_page_start=int(record["printed_page_start"]) if record.get("printed_page_start") is not None else None,
            printed_page_end=int(record["printed_page_end"]) if record.get("printed_page_end") is not None else None,
        )


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    heading_id: str | None


@dataclass(frozen=True)
class HeadingMeta:
    printed_page: int | None
    printed_label: str
    source_page: int | None


@dataclass(frozen=True)
class BookPart:
    part_id: str
    title: str
    links: tuple[str, ...]


@dataclass(frozen=True)
class SupplementalSiteDocument:
    slug: str
    title: str
    description: str
    page_count: int
    text_path: Path
    processed_dir: Path
    doc_web_bundle_root: Path
    doc_web_manifest_path: Path
    doc_web_provenance_path: Path
    doc_web_image_count: int
    distribution_pdf: Path
    archival_pdf: Path


class TextExtractor(HTMLParser):
    def __init__(self, skip_tags: Iterable[str] = ()) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_tags = {tag.lower() for tag in skip_tags}
        self.skip_stack: list[str] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.skip_stack or tag in self.skip_tags:
            self.skip_stack.append(tag)
            return
        if tag in BLOCK_TAGS or tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_stack:
            if tag == self.skip_stack[-1]:
                self.skip_stack.pop()
            elif tag in self.skip_stack:
                self.skip_stack = self.skip_stack[: self.skip_stack.index(tag)]
            return
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_stack and data.strip():
            self.parts.append(data)


class HeadingExtractor(HTMLParser):
    def __init__(self, levels: set[int]) -> None:
        super().__init__(convert_charrefs=True)
        self.levels = levels
        self.active_level: int | None = None
        self.active_id: str | None = None
        self.active_parts: list[str] = []
        self.headings: list[Heading] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        match = re.fullmatch(r"h([1-6])", tag.lower())
        if not match:
            return
        level = int(match.group(1))
        if level not in self.levels:
            return
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        self.active_level = level
        self.active_id = attrs_map.get("id") or None
        self.active_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self.active_level is None or tag.lower() != f"h{self.active_level}":
            return
        text = re.sub(r"\s+", " ", "".join(self.active_parts)).strip()
        if text:
            self.headings.append(Heading(self.active_level, text, self.active_id))
        self.active_level = None
        self.active_id = None
        self.active_parts = []

    def handle_data(self, data: str) -> None:
        if self.active_level is not None:
            self.active_parts.append(data)


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def load_bundle() -> Bundle:
    require_file(ACTIVE_BUNDLE_PATH, "active doc-web bundle marker")
    active = json.loads(ACTIVE_BUNDLE_PATH.read_text(encoding="utf-8"))
    bundle_root = (ROOT / active["bundleRoot"]).resolve()
    manifest_path = (ROOT / active["manifestPath"]).resolve()
    provenance_raw = active.get("provenancePath")
    provenance_path = (ROOT / provenance_raw).resolve() if provenance_raw else None
    require_file(bundle_root, "active doc-web bundle")
    require_file(manifest_path, "doc-web bundle manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return Bundle(
        root=bundle_root,
        manifest_path=manifest_path,
        provenance_path=provenance_path if provenance_path and provenance_path.exists() else None,
        manifest=manifest,
        active=active,
    )


def load_companion_doc_web_records() -> dict[str, dict]:
    require_file(COMPANION_DOC_WEB_MANIFEST_PATH, "companion doc-web manifest")
    manifest = json.loads(COMPANION_DOC_WEB_MANIFEST_PATH.read_text(encoding="utf-8"))
    records = manifest.get("documents") or []
    by_slug: dict[str, dict] = {}
    for record in records:
        slug = str(record.get("slug") or "")
        if slug:
            by_slug[slug] = record
    return by_slug


def load_supplemental_documents() -> list[SupplementalSiteDocument]:
    if not SUPPLEMENTAL_MANIFEST_PATH.exists():
        return []
    manifest = json.loads(SUPPLEMENTAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    companion_records = load_companion_doc_web_records()
    documents: list[SupplementalSiteDocument] = []
    for record in manifest.get("documents", []):
        slug = str(record["slug"])
        companion_record = companion_records.get(slug)
        if not companion_record:
            raise SystemExit(f"Missing companion doc-web bundle record for {slug}")
        pdfs = record.get("pdfs") or {}
        distribution_pdf = ROOT / str(pdfs.get("distribution") or "")
        archival_pdf = ROOT / str(pdfs.get("archival") or "")
        text_path = ROOT / str(record.get("text") or "")
        processed_dir = ROOT / str(record.get("processed_dir") or "")
        doc_web_bundle_root = ROOT / str(companion_record.get("bundle_root") or "")
        doc_web_manifest_path = ROOT / str(companion_record.get("manifest") or "")
        doc_web_provenance_path = ROOT / str(companion_record.get("provenance") or "")
        require_file(distribution_pdf, f"supplemental distribution PDF for {record.get('slug')}")
        require_file(archival_pdf, f"supplemental archival PDF for {record.get('slug')}")
        require_file(text_path, f"supplemental OCR text for {record.get('slug')}")
        require_file(processed_dir, f"supplemental processed pages for {record.get('slug')}")
        require_file(doc_web_bundle_root, f"companion doc-web bundle for {slug}")
        require_file(doc_web_manifest_path, f"companion doc-web manifest for {slug}")
        require_file(doc_web_provenance_path, f"companion doc-web provenance for {slug}")
        documents.append(
            SupplementalSiteDocument(
                slug=slug,
                title=str(record["title"]),
                description=str(record.get("description") or ""),
                page_count=int(record.get("page_count") or 0),
                text_path=text_path,
                processed_dir=processed_dir,
                doc_web_bundle_root=doc_web_bundle_root,
                doc_web_manifest_path=doc_web_manifest_path,
                doc_web_provenance_path=doc_web_provenance_path,
                doc_web_image_count=int(companion_record.get("image_count") or 0),
                distribution_pdf=distribution_pdf,
                archival_pdf=archival_pdf,
            )
        )
    return documents


def ordered_entries(bundle: Bundle) -> list[Entry]:
    entries = [Entry.from_record(record) for record in bundle.manifest.get("entries", [])]
    # The imported manifest is accepted source data, but this book's early
    # front matter landed out of physical order. Website reading order follows
    # source-scan order so page vi precedes printed page 1.
    return sorted(entries, key=lambda entry: (min(entry.source_pages) if entry.source_pages else 9999, entry.order, entry.entry_id))


def read_article_html(bundle: Bundle, entry: Entry) -> str:
    source = bundle.root / entry.path
    require_file(source, f"doc-web entry {entry.entry_id}")
    return read_doc_web_article(source, image_prefix="images/doc-web")


def read_doc_web_article(source: Path, *, image_prefix: str) -> str:
    html = source.read_text(encoding="utf-8")
    match = ARTICLE_RE.search(html)
    if not match:
        raise SystemExit(f"Could not find article body in {source}")
    article = match.group(1).strip()
    article = IMAGE_SRC_RE.sub(lambda match: f"{match.group(1)}{image_prefix}/", article)
    article = IMG_TAG_RE.sub('<img loading="lazy" decoding="async"', article)
    article = DECORATIVE_FIGURE_RE.sub('<hr class="decorative-break">', article)
    article = NO_SRC_IMG_RE.sub("", article)
    article = TABLE_RE.sub(r'<div class="table-scroll">\1</div>', article)
    return article


def normalize_alains_song_refrains(article: str) -> str:
    def replace_paragraph(match: re.Match[str]) -> str:
        opening, content, closing = match.groups()
        plain_content = re.sub(r"<br\s*/?>", " ", content, flags=re.IGNORECASE)
        plain_content = re.sub(r"</?strong>", "", plain_content, flags=re.IGNORECASE)
        plain_content = re.sub(r"<[^>]+>", " ", plain_content)
        if not re.match(r"^\s*REFRAIN:?\b", plain_content, flags=re.IGNORECASE):
            return match.group(0)
        normalized_content = re.sub(r"</?strong>", "", content, flags=re.IGNORECASE).strip()
        return f"{opening}<strong>{normalized_content}</strong>{closing}"

    return P_TAG_RE.sub(replace_paragraph, article)


def sectionize_article_by_headings(article: str, *, section_class: str) -> str:
    sections: list[str] = []
    current: list[str] = []
    cursor = 0
    for match in SECTION_HEADING_RE.finditer(article):
        leading = article[cursor:match.start()]
        if current:
            current.append(leading)
            section_body = "".join(current).strip()
            if section_body:
                sections.append(f'<section class="{section_class}">{section_body}</section>')
        elif leading.strip():
            sections.append(f'<section class="{section_class}">{leading.strip()}</section>')
        current = [match.group(1)]
        cursor = match.end()

    if current:
        current.append(article[cursor:])
        section_body = "".join(current).strip()
        if section_body:
            sections.append(f'<section class="{section_class}">{section_body}</section>')
    elif article.strip():
        sections.append(f'<section class="{section_class}">{article.strip()}</section>')
    return "\n".join(sections)


def html_to_text(html: str, skip_tags: Iterable[str] = ()) -> str:
    parser = TextExtractor(skip_tags=skip_tags)
    parser.feed(html)
    raw = "".join(parser.parts)
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(" ".join(current).strip())
    return "\n\n".join(block for block in blocks if block)


def heading_records(html: str, levels: set[int] | None = None) -> list[Heading]:
    parser = HeadingExtractor(levels or {1, 2})
    parser.feed(html)
    return parser.headings


def is_toc_heading(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip()
    return bool(normalized) and not GENERIC_TOC_HEADING_RE.fullmatch(normalized)


def first_heading_title(article: str, fallback: str) -> str:
    headings = heading_records(article, {1})
    if not headings:
        headings = heading_records(article, {2})
    return headings[0].text if headings else fallback


def display_title(bundle: Bundle, entry: Entry) -> str:
    return first_heading_title(read_article_html(bundle, entry), entry.title)


def load_heading_meta(bundle: Bundle) -> dict[str, HeadingMeta]:
    if not bundle.provenance_path:
        return {}
    rows: dict[str, HeadingMeta] = {}
    with bundle.provenance_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("block_kind") != "heading" or not record.get("block_id"):
                continue
            printed_raw = record.get("source_printed_page_number")
            printed_page = int(printed_raw) if isinstance(printed_raw, int) and 0 < printed_raw < 400 else None
            source_raw = record.get("source_page_number")
            rows[str(record["block_id"])] = HeadingMeta(
                printed_page=printed_page,
                printed_label=str(record.get("source_printed_page_label") or ""),
                source_page=int(source_raw) if isinstance(source_raw, int) else None,
            )
    return rows


PART_ORDER = (
    ("front", "Front Matter"),
    ("part-i", "Part I - Alain Family History"),
    ("part-ii", "Part II - Alain Family Stories"),
    ("part-iii", "Part III - Lessard Family History"),
    ("part-iv", "Part IV - Lessard Family Stories"),
    ("part-v", "Part V - Veillardville"),
    ("part-vi", "Part VI - Memories"),
    ("part-vii", "Part VII - Personal Records"),
    ("back", "Bibliography and Index"),
)


def book_part_for(entry: Entry, meta: HeadingMeta | None) -> str:
    source_page = meta.source_page if meta and meta.source_page is not None else (min(entry.source_pages) if entry.source_pages else None)
    printed_page = meta.printed_page if meta else entry.printed_page_start
    if source_page is not None and source_page <= 7:
        return "front"
    if printed_page is None:
        return "front"
    if 1 <= printed_page <= 6:
        return "part-i"
    if 7 <= printed_page <= 80:
        return "part-ii"
    if 81 <= printed_page <= 88:
        return "part-iii"
    if 89 <= printed_page <= 128:
        return "part-iv"
    if 129 <= printed_page <= 135:
        return "part-v"
    if 136 <= printed_page <= 142:
        return "part-vi"
    if 143 <= printed_page <= 144:
        return "part-vii"
    return "back"


def excerpt_from_html(html: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", html_to_text(html)).strip()
    if not text:
        return "This entry is represented by source images and structured reading data."
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "."


def compact_ranges(values: Iterable[int]) -> str:
    ordered = sorted({int(value) for value in values})
    if not ordered:
        return ""
    ranges: list[str] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = value
    ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def page_label(prefix: str, values: Iterable[int]) -> str:
    text = compact_ranges(values)
    if not text:
        return ""
    return f"{prefix} {text}"


def printable_page_values(entry: Entry) -> tuple[int, ...]:
    values = entry.printed_pages
    if not values and entry.printed_page_start is not None:
        end = entry.printed_page_end or entry.printed_page_start
        values = tuple(range(entry.printed_page_start, end + 1))
    # Some cover/title entries carry a year where a printed page number would be.
    return tuple(value for value in values if 0 < value < 400)


def entry_meta_label(entry: Entry) -> str:
    printed = page_label("Printed page" if len(printable_page_values(entry)) == 1 else "Printed pages", printable_page_values(entry))
    source = page_label("Source scan" if len(entry.source_pages) == 1 else "Source scans", entry.source_pages)
    return " | ".join(part for part in (printed, source) if part)


def scan_url(page_number: int) -> str:
    return f"images/scans/page-{page_number:03d}.jpg"


def source_scan_links_for_pages(source_pages: Iterable[int]) -> str:
    pages = sorted({int(page) for page in source_pages})
    if not pages:
        return "<p>No source scans are attached to this entry.</p>"
    if len(pages) <= 10:
        links = pages
    else:
        links = pages[:4] + pages[-4:]
    rendered = []
    seen_gap = False
    for page in links:
        if len(pages) > 10 and not seen_gap and page == pages[-4]:
            rendered.append('<span class="scan-gap">...</span>')
            seen_gap = True
        rendered.append(f'<a href="{scan_url(page)}">Scan {page:03d}</a>')
    return f'<div class="scan-links">{"".join(rendered)}</div>'


def source_scan_links(entry: Entry) -> str:
    return source_scan_links_for_pages(entry.source_pages)


def html_page(title: str, body: str, current: str = "") -> str:
    nav = [
        ("index.html", "Home"),
        ("book.html", "Read"),
        ("audiobook.html", "Audio"),
        ("archive.html", "Archive"),
    ]
    links = "\n".join(
        f'<a class="nav-link{" is-active" if label == current else ""}" href="{href}">{label}</a>'
        for href, label in nav
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - {escape(SITE_TITLE)}</title>
  <meta name="description" content="A digital family archive edition of the Alain Lessard book.">
  <link rel="canonical" href="{PUBLIC_HOST}/">
  <link rel="stylesheet" href="assets/site.css?v={SITE_ASSET_VERSION}">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="index.html" aria-label="Alain Lessard home">
      <span class="brand-mark">AL</span>
      <span><strong>{escape(SITE_TITLE)}</strong><small>{escape(SITE_SUBTITLE)}</small></span>
    </a>
    <nav class="site-nav" aria-label="Primary navigation">{links}</nav>
  </header>
  <main>
{body}
  </main>
  <footer class="site-footer">
    <p>Digitized from the {BOOK_YEAR} family history book for reading, searching, listening, and family reference.</p>
  </footer>
  <script defer src="assets/audio.js?v={SITE_ASSET_VERSION}"></script>
</body>
</html>
"""


def render_chapter_card(bundle: Bundle, entry: Entry) -> str:
    article = read_article_html(bundle, entry)
    title = display_title(bundle, entry)
    return f"""<article class="entry-card">
  <h3><a href="{escape(entry.path)}">{escape(title)}</a></h3>
  <p>{escape(excerpt_from_html(article))}</p>
</article>"""


def render_reading_card(section: ReadingSection) -> str:
    return f"""<article class="entry-card">
  <h3><a href="{escape(section.path)}">{escape(section.title)}</a></h3>
  <p>{escape(excerpt_from_html(section.article_html))}</p>
</article>"""


def supplemental_download_href(pdf: Path) -> str:
    return f"downloads/{pdf.name}?v={SITE_ASSET_VERSION}"


def supplemental_html_filename(document: SupplementalSiteDocument) -> str:
    return f"companion-{document.slug}.html"


def supplemental_html_href(document: SupplementalSiteDocument) -> str:
    return supplemental_html_filename(document)


def supplemental_page_paths(document: SupplementalSiteDocument) -> list[Path]:
    pages = sorted(document.processed_dir.glob("page-*.jpg"))
    if not pages:
        raise SystemExit(f"No processed companion pages found for {document.slug}: {document.processed_dir}")
    if document.page_count and len(pages) != document.page_count:
        raise SystemExit(f"{document.slug} has {len(pages)} processed companion pages, expected {document.page_count}")
    return pages


def supplemental_page_image_href(document: SupplementalSiteDocument, page: Path) -> str:
    return f"images/companion/{document.slug}/{page.name}"


def render_supplemental_cards(supplemental_documents: list[SupplementalSiteDocument]) -> str:
    cards = []
    for document in supplemental_documents:
        distribution_size = document.distribution_pdf.stat().st_size / 1024 / 1024
        archival_size = document.archival_pdf.stat().st_size / 1024 / 1024
        page_label = "1 page" if document.page_count == 1 else f"{document.page_count} pages"
        html_href = supplemental_html_href(document)
        distribution_href = supplemental_download_href(document.distribution_pdf)
        archival_href = supplemental_download_href(document.archival_pdf)
        cards.append(
            f"""<article class="entry-card">
  <p class="eyebrow">{escape(page_label)}</p>
  <h3><a href="{html_href}">{escape(document.title)}</a></h3>
  <p>{escape(document.description)}</p>
  <div class="card-actions">
    <a class="button primary" href="{html_href}">Read HTML</a>
    <a class="button" href="{distribution_href}">Reader PDF</a>
    <a class="button" href="{archival_href}">Archival PDF</a>
  </div>
  <p>{distribution_size:.1f} MiB reader PDF; {archival_size:.1f} MiB archival PDF.</p>
</article>"""
        )
    return "".join(cards)


def home_feature_sections(reading_catalog: ReadingCatalog) -> list[ReadingSection]:
    return [section for section in reading_catalog.sections if section.kind == "narrative"][:6]


def portable_artifact_action(
    artifact,
    label: str,
    *,
    primary: bool = False,
) -> str:
    if not artifact.is_available:
        return f'<span class="button disabled">{escape(label)} unavailable in this preview</span>'
    size = format_file_size(artifact.output_path.stat().st_size)
    classes = "button primary" if primary else "button"
    return (
        f'<a class="{classes}" href="{escape(artifact.public_path)}" download>'
        f'{escape(label)} <span class="button-meta">{escape(size)}</span></a>'
    )


def require_portable_artifacts(catalog: PortableCatalog) -> None:
    missing = [
        artifact.output_path
        for artifact in (catalog.epub, catalog.m4b)
        if not artifact.is_available
    ]
    if missing:
        raise SystemExit(
            "Release-ready family-site build requires portable editions:\n"
            + "\n".join(f"- {path}" for path in missing)
        )


def render_portable_handoff(catalog: PortableCatalog, *, compact: bool = False) -> str:
    heading = "Take the book with you" if compact else "Read or listen in another app"
    return f"""<section class="portable-handoff{' compact' if compact else ''}">
  <div class="portable-copy">
    <p class="eyebrow">For eReaders, phones, and tablets</p>
    <h2>{heading}</h2>
    <p>Use the EPUB in an eReader or the chaptered M4B in a compatible audiobook app. Your device will ask where to save or open the file.</p>
  </div>
  <div class="portable-actions">
    {portable_artifact_action(catalog.epub, "Download eReader edition (EPUB)", primary=True)}
    {portable_artifact_action(catalog.m4b, "Download chaptered audiobook (M4B)")}
    <a class="button" href="reading-apps.html">Help for my device</a>
  </div>
</section>"""


def render_reading_apps(
    portable_catalog: PortableCatalog,
    audiobook_catalog: AudiobookCatalog,
) -> str:
    full = audiobook_catalog.full_audiobook
    mp3_action = (
        f'<a class="button" href="{escape(full.public_audio_path)}" download>Download audiobook as MP3</a>'
        if full.is_available
        else '<span class="button disabled">MP3 unavailable in this preview</span>'
    )
    body = f"""
    <section class="page-title device-help-title">
      <p class="eyebrow">Use the reader or listener you already know</p>
      <h1>Read or listen on your device</h1>
      <p>There is no single button that can place a family file into every app. Download the book first, then follow the short instructions for your device. The website remains available if you prefer not to install anything.</p>
    </section>
    {render_portable_handoff(portable_catalog)}
    <section class="device-help-grid">
      <article id="apple-books">
        <h2>Apple Books</h2>
        <ol><li>Download the EPUB.</li><li>Choose <strong>Open in Books</strong>, or use the Share button and choose Books.</li></ol>
        <p>For the audiobook, download the M4B and open it in a compatible audiobook app. On a Mac, Books can also import audiobook files.</p>
      </article>
      <article id="kindle">
        <h2>Kindle</h2>
        <ol><li>Download the EPUB.</li><li>Open Amazon's <a href="https://www.amazon.com/sendtokindle" rel="external">Send to Kindle</a> page or app and choose the downloaded file.</li><li>Amazon will deliver its Kindle copy to your library.</li></ol>
      </article>
      <article id="kobo">
        <h2>Kobo</h2>
        <ol><li>Download the EPUB to a computer.</li><li>Connect the Kobo with its USB cable.</li><li>Copy the EPUB onto the Kobo, then safely eject it.</li></ol>
        <p>Some newer Kobo models can also import EPUB files from Google Drive or Dropbox.</p>
      </article>
      <article id="google-play-books">
        <h2>Google Play Books</h2>
        <ol><li>Download the EPUB.</li><li>On Android, open the downloaded file with Play Books. On a computer, upload it to your Play Books library.</li><li>It will then be available on devices signed into that Google account.</li></ol>
      </article>
      <article id="audiobook-apps">
        <h2>Other audiobook apps</h2>
        <p>The M4B is one book with 52 named chapters and is the best choice for compatible audiobook apps. If your app does not accept M4B, use the complete MP3 instead.</p>
        <div class="card-actions">{portable_artifact_action(portable_catalog.m4b, "Download M4B", primary=True)}{mp3_action}</div>
      </article>
      <article id="website-option">
        <h2>No download needed</h2>
        <p>You can always <a href="book.html">read on this website</a> or <a href="audiobook.html">listen in the browser</a>. No app or account is required.</p>
      </article>
    </section>
"""
    return html_page("Read or listen on your device", body)


def render_home(
    bundle: Bundle,
    entries: list[Entry],
    reading_catalog: ReadingCatalog,
    supplemental_documents: list[SupplementalSiteDocument],
    audiobook_catalog: AudiobookCatalog,
    portable_catalog: PortableCatalog,
) -> str:
    feature_cards = "\n".join(render_reading_card(section) for section in home_feature_sections(reading_catalog))
    supplemental_cards = render_supplemental_cards(supplemental_documents)
    table_count = sum(read_article_html(bundle, entry).lower().count("<table") for entry in entries)
    figure_count = sum(read_article_html(bundle, entry).lower().count("<figure") for entry in entries)
    supplemental_section = ""
    if supplemental_cards:
        supplemental_section = f"""
    <section class="section-list companion-home">
      <div class="section-heading">
        <h2>Companion Documents</h2>
        <p>The two documents found tucked into the book are available as readable HTML pages and searchable PDFs.</p>
      </div>
      <div class="cards">{supplemental_cards}</div>
    </section>
"""
    body = f"""
    <section class="hero">
      <div class="hero-inner">
        <p class="eyebrow">Family history edition</p>
        <h1>{escape(SITE_TITLE)}</h1>
        <p>{escape(SITE_SUBTITLE)}</p>
        <div class="hero-actions">
          <a class="button primary" href="book.html">Read the book</a>
          <a class="button" href="downloads/{DISTRIBUTION_PDF.name}">Download PDF</a>
        </div>
      </div>
    </section>

    <section class="intro-grid">
      <article>
        <h2>A family reading edition</h2>
        <p>The scanned book is available as connected web chapters, with photographs, captions, and tables kept in the flow of the text.</p>
      </article>
      <article>
        <h2>Search and companion documents</h2>
        <p>Names, places, stories, and the companion documents found inside the book can be searched from one place.</p>
      </article>
      <article>
        <h2>Audio companion</h2>
        <p>Listen to {len(audiobook_catalog.tracks)} family-history recordings in your browser or download the complete audiobook. No app or account is needed.</p>
        <div class="card-actions"><a class="button primary" href="audiobook.html">Listen to the audiobook</a></div>
      </article>
    </section>

    <section class="stat-band" aria-label="Edition summary">
      <div><strong>{len(reading_catalog.sections)}</strong><span>reading sections</span></div>
      <div><strong>{figure_count}</strong><span>figures and captions</span></div>
      <div><strong>{table_count}</strong><span>structured tables</span></div>
      <div><strong>{len(supplemental_documents)}</strong><span>companion documents</span></div>
    </section>

    <section class="section-list">
      <div class="section-heading">
        <h2>Start Reading</h2>
        <p>Begin with the introductory and early family-history sections, or use the complete contents on the reading page.</p>
      </div>
      <div class="cards">{feature_cards}</div>
    </section>

    {render_portable_handoff(portable_catalog, compact=True)}

    {supplemental_section}
"""
    return html_page("Home", body, "Home")


def render_toc(parts: list[BookPart]) -> str:
    lines = []
    for part in parts:
        count = len(part.links)
        label = "1 section" if count == 1 else f"{count} sections"
        lines.append(f'<li><a href="#{escape(part.part_id)}">{escape(part.title)}</a><span>{label}</span></li>')
    return "\n".join(lines)


def build_book_parts(bundle: Bundle, entries: list[Entry]) -> list[BookPart]:
    metadata = load_heading_meta(bundle)
    links_by_part: dict[str, list[str]] = {part_id: [] for part_id, _ in PART_ORDER}
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        article = read_article_html(bundle, entry)
        headings = [heading for heading in heading_records(article, {1, 2}) if is_toc_heading(heading.text)]
        if not headings:
            title = display_title(bundle, entry)
            if not is_toc_heading(title):
                continue
            part_id = book_part_for(entry, None)
            href = entry.path
            key = (part_id, href, title)
            if key not in seen:
                seen.add(key)
                links_by_part[part_id].append(
                    f'<li class="heading-level-1"><a href="{escape(href)}">{escape(title)}</a></li>'
                )
            continue
        for heading in headings:
            meta = metadata.get(heading.heading_id or "")
            part_id = book_part_for(entry, meta)
            href = f"{entry.path}#{heading.heading_id}" if heading.heading_id else entry.path
            key = (part_id, href, heading.text)
            if key in seen:
                continue
            seen.add(key)
            links_by_part.setdefault(part_id, []).append(
                f'<li class="heading-level-{heading.level}"><a href="{escape(href)}">{escape(heading.text)}</a></li>'
            )
    parts: list[BookPart] = []
    for part_id, title in PART_ORDER:
        links = tuple(links_by_part.get(part_id) or ())
        if links:
            parts.append(BookPart(part_id, title, links))
    return parts


def render_part_sections(parts: list[BookPart]) -> str:
    rendered = []
    for part in parts:
        count = len(part.links)
        label = "1 section" if count == 1 else f"{count} sections"
        rendered.append(
            f"""<section class="part-section" id="{escape(part.part_id)}">
  <div class="part-heading">
    <h2>{escape(part.title)}</h2>
    <p>{label}</p>
  </div>
  <ol class="part-links">{''.join(part.links)}</ol>
</section>"""
        )
    return "\n".join(rendered)


def build_semantic_book_parts(reading_catalog: ReadingCatalog) -> list[BookPart]:
    sections_by_part: dict[str, list[ReadingSection]] = {part_id: [] for part_id, _title in PART_ORDER}
    for section in reading_catalog.sections:
        sections_by_part.setdefault(section.part_id, []).append(section)
    parts: list[BookPart] = []
    for part_id, title in PART_ORDER:
        sections = sections_by_part.get(part_id, [])
        if not sections:
            continue
        links = tuple(
            f'<li class="heading-level-1 semantic-section-link"><a href="{escape(section.path)}">{escape(section.title)}</a></li>'
            for section in sections
        )
        parts.append(BookPart(part_id, title, links))
    return parts


def render_book(reading_catalog: ReadingCatalog, portable_catalog: PortableCatalog) -> str:
    parts = build_semantic_book_parts(reading_catalog)
    body = f"""
    <section class="page-title">
      <h1>Read the Book</h1>
      <p>Search the text or browse the book by family-history section. Photographs, captions, tables, and reference material remain with the stories they belong to.</p>
    </section>
    {render_portable_handoff(portable_catalog, compact=True)}
    <section class="book-tools">
      <label class="search-label" for="site-search">Search the book</label>
      <input id="site-search" class="search-input" type="search" placeholder="Search names, places, stories">
      <div id="search-results" class="search-results" aria-live="polite"></div>
    </section>
    <section class="book-layout">
      <aside class="toc-panel">
        <h2>Contents</h2>
        <ol>{render_toc(parts)}</ol>
      </aside>
      <div class="entry-list">
        {render_part_sections(parts)}
      </div>
    </section>
    <script src="assets/search.js?v={SITE_ASSET_VERSION}"></script>
"""
    return html_page("Read", body, "Read")


def entry_nav(entries: list[Entry], index: int) -> str:
    previous_entry = entries[index - 1] if index > 0 else None
    next_entry = entries[index + 1] if index < len(entries) - 1 else None
    previous_link = (
        f'<a class="button" href="{escape(previous_entry.path)}">Previous</a>' if previous_entry else '<span class="button disabled">Previous</span>'
    )
    next_link = f'<a class="button" href="{escape(next_entry.path)}">Next</a>' if next_entry else '<span class="button disabled">Next</span>'
    return f"""<nav class="reader-nav" aria-label="Reading navigation">
  {previous_link}
  <a class="button" href="book.html">Contents</a>
  {next_link}
</nav>"""


def render_entry_page(
    bundle: Bundle,
    entries: list[Entry],
    index: int,
    audio_tracks: Iterable[AudiobookTrack] = (),
) -> str:
    entry = entries[index]
    article = read_article_html(bundle, entry)
    label = entry_meta_label(entry)
    title = display_title(bundle, entry)
    body = f"""
    <section class="entry-header">
      <p class="eyebrow">{escape(entry.kind.title())}{f" | {escape(label)}" if label else ""}</p>
      <h1>{escape(title)}</h1>
    </section>
    {entry_nav(entries, index)}
    {render_entry_audio_section(audio_tracks)}
    <section class="reader-shell">
      <aside class="source-panel">
        <h2>Source Pages</h2>
        <p>{escape(label or "Source scans attached to the book entry.")}</p>
        {source_scan_links(entry)}
      </aside>
      <article class="book-article">
        {article}
      </article>
    </section>
    {entry_nav(entries, index)}
"""
    return html_page(title, body, "Read")


def render_reading_section_page(
    reading_catalog: ReadingCatalog,
    index: int,
    audio_tracks: Iterable[AudiobookTrack] = (),
) -> str:
    section = reading_catalog.sections[index]
    scan_count = len(section.source_pages)
    scan_label = "1 source scan" if scan_count == 1 else f"{scan_count} source scans"
    kind_label = "Story section" if section.kind == "narrative" else "Reference section"
    body = f"""
    <section class="entry-header">
      <p class="eyebrow">{escape(kind_label)}</p>
      <h1>{escape(section.title)}</h1>
    </section>
    {entry_nav(list(reading_catalog.sections), index)}
    {render_entry_audio_section(audio_tracks)}
    <section class="reader-shell">
      <aside class="source-panel">
        <h2>Source Material</h2>
        <p>{escape(scan_label)} preserve this section in the scanned edition.</p>
        {source_scan_links_for_pages(section.source_pages)}
      </aside>
      <article class="book-article">
        {section.article_html}
      </article>
    </section>
    {entry_nav(list(reading_catalog.sections), index)}
"""
    return html_page(section.title, body, "Read")


def render_companion_source_figures(document: SupplementalSiteDocument) -> str:
    figures = []
    for index, page in enumerate(supplemental_page_paths(document), start=1):
        href = supplemental_page_image_href(document, page)
        figures.append(
            f"""<figure class="companion-page">
  <a href="{href}"><img loading="lazy" decoding="async" src="{href}" alt="{escape(document.title)} source page {index}"></a>
  <figcaption>Source page {index}</figcaption>
</figure>"""
        )
    return "\n".join(figures)


def companion_doc_web_article_html(document: SupplementalSiteDocument) -> str:
    manifest = json.loads(document.doc_web_manifest_path.read_text(encoding="utf-8"))
    entries = {
        str(entry.get("entry_id")): entry
        for entry in manifest.get("entries") or []
        if isinstance(entry, dict) and entry.get("entry_id")
    }
    reading_order = [str(entry_id) for entry_id in manifest.get("reading_order") or []]
    if not reading_order:
        reading_order = sorted(entries, key=lambda entry_id: int(entries[entry_id].get("order") or 0))
    if not reading_order:
        raise SystemExit(f"Companion doc-web bundle has no readable entries: {document.doc_web_manifest_path}")

    image_prefix = f"images/companion-doc-web/{document.slug}"
    article_parts = []
    for entry_id in reading_order:
        entry = entries.get(entry_id)
        if not entry:
            raise SystemExit(f"Companion doc-web reading order references missing entry {entry_id}: {document.doc_web_manifest_path}")
        source = document.doc_web_bundle_root / str(entry.get("path") or "")
        require_file(source, f"companion doc-web entry {document.slug}/{entry_id}")
        article = read_doc_web_article(source, image_prefix=image_prefix)
        if document.slug == "alains-song":
            article = normalize_alains_song_refrains(article)
        article_parts.append(article)

    note = f'<p class="companion-context-note">{escape(COMPANION_CONTEXT_NOTE)}</p>'
    if document.slug == "growing-up-on-the-farm":
        article = sectionize_article_by_headings("\n".join(article_parts), section_class="companion-story-section")
        return f"{note}\n{article}"
    return "\n".join([note] + [f'<section class="doc-web-entry">{article}</section>' for article in article_parts])


def companion_document_toc_html(document: SupplementalSiteDocument, article: str) -> str:
    if document.slug != "growing-up-on-the-farm":
        return ""
    links = []
    for heading in heading_records(article, {1, 2}):
        if not heading.heading_id or not is_toc_heading(heading.text):
            continue
        links.append(
            f'<li class="heading-level-{heading.level}"><a href="#{escape(heading.heading_id)}">{escape(heading.text)}</a></li>'
        )
    if not links:
        return ""
    return f"""
        <nav class="companion-toc" aria-label="{escape(document.title)} contents">
          <h2>Contents</h2>
          <ol>
            {"".join(links)}
          </ol>
        </nav>"""


def render_companion_document(
    document: SupplementalSiteDocument,
    audio_tracks: Iterable[AudiobookTrack] = (),
) -> str:
    page_label = "1 source page" if document.page_count == 1 else f"{document.page_count} source pages"
    article = companion_doc_web_article_html(document)
    companion_toc = companion_document_toc_html(document, article)
    distribution_href = supplemental_download_href(document.distribution_pdf)
    archival_href = supplemental_download_href(document.archival_pdf)
    body = f"""
    <section class="entry-header companion-header">
      <p class="eyebrow">Companion document | {escape(page_label)}</p>
      <h1>{escape(document.title)}</h1>
      <p>{escape(document.description)}</p>
      <div class="card-actions">
        <a class="button" href="archive.html">Archive</a>
        <a class="button" href="{distribution_href}">Reader PDF</a>
        <a class="button" href="{archival_href}">Archival PDF</a>
      </div>
    </section>
    {render_entry_audio_section(audio_tracks)}
    <section class="reader-shell companion-shell">
      <aside class="source-panel">
        <h2>Document Files</h2>
        <p>{escape(page_label)} preserved from the sheets found inside the book.</p>
        <div class="card-actions">
          <a class="button" href="{distribution_href}">Reader PDF</a>
          <a class="button" href="{archival_href}">Archival PDF</a>
        </div>
        {companion_toc}
      </aside>
      <article class="book-article companion-document">
        {article}
      </article>
    </section>
    <section class="section-list companion-sources">
      <div class="section-heading">
        <h2>Source Pages</h2>
        <p>The cleaned page images are included here for side-by-side review against the readable text.</p>
      </div>
      <div class="companion-source-grid">{render_companion_source_figures(document)}</div>
    </section>
"""
    return html_page(document.title, body, "Archive")


def render_archive(bundle: Bundle, entries: list[Entry], supplemental_documents: list[SupplementalSiteDocument]) -> str:
    pdf_cards = []
    for label, title, pdf in (
        ("Reader PDF", "Main book reader PDF", DISTRIBUTION_PDF),
        ("Archival PDF", "Main book archival PDF", ARCHIVAL_PDF),
    ):
        if pdf.exists():
            size_mb = pdf.stat().st_size / 1024 / 1024
            pdf_cards.append(
                f"""<article class="entry-card">
  <p class="eyebrow">{label}</p>
  <h3><a href="downloads/{pdf.name}">{title}</a></h3>
  <p>{size_mb:.1f} MiB. Searchable PDF download.</p>
</article>"""
            )
    supplemental_cards = render_supplemental_cards(supplemental_documents)
    doc_web_image_count = len(list((bundle.root / "images").glob("*")))
    provenance_link = '<li><a href="data/block-provenance.jsonl">Source trace data</a></li>' if bundle.provenance_path else ""
    supplemental_section = ""
    if supplemental_cards:
        supplemental_section = f"""
    <section class="section-list">
      <div class="section-heading">
        <h2>Companion Documents</h2>
        <p>The two documents found inside the book are included as readable HTML pages and searchable PDFs alongside the main book.</p>
      </div>
      <div class="cards">{supplemental_cards}</div>
    </section>
"""
    body = f"""
    <section class="page-title">
      <h1>Archive</h1>
      <p>Download the PDFs and review the source records that keep the family book traceable.</p>
    </section>
    <section class="cards archive-downloads">{''.join(pdf_cards)}</section>
    {supplemental_section}
    <section class="archive-grid">
      <article>
        <h2>Book Data</h2>
        <ul>
          <li><a href="data/structured-manifest.json">Reading inventory</a></li>
          {provenance_link}
          <li>{len(entries)} reading entries</li>
          <li>{doc_web_image_count} photograph and illustration crops</li>
        </ul>
      </article>
      <article>
        <h2>Source Scans</h2>
        <p>Each chapter and page entry links back to the scans that produced it. The companion documents are preserved as separate PDFs because they were found tucked into the book rather than printed as part of it.</p>
      </article>
    </section>
"""
    return html_page("Archive", body, "Archive")


def friendly_skip_group(reason: str, count: int) -> str:
    labels = {
        "page-level material": "Opening pages and page-by-page material stay in the reading edition.",
        "personal records tables": "Personal records remain readable as tables.",
        "bibliography": "The bibliography remains in the archive.",
        "cover and title pages": "Cover and title pages remain in the archive.",
    }
    fallback = f"{reason.title()} stays in the readable archive."
    noun = "entry" if count == 1 else "entries"
    return f"{labels.get(reason, fallback)} <span>{count} {noun}</span>"


def audio_player(audio_path: str, title: str) -> str:
    return f"""<audio class="audio-player" controls preload="none" data-audio-key="{escape(audio_path)}" aria-label="{escape(title)}">
  <source src="{escape(audio_path)}" type="audio/mpeg">
  <a href="{escape(audio_path)}" download>Download MP3</a>
</audio>"""


def audio_runtime(duration_seconds: float | None) -> str:
    if duration_seconds is None:
        return ""
    return f'<p class="audio-runtime">Run time {escape(format_audio_duration(duration_seconds))}</p>'


def audio_reading_links(
    reading_catalog: ReadingCatalog,
    supplemental_documents: list[SupplementalSiteDocument],
    audiobook_catalog: AudiobookCatalog,
) -> dict[int, tuple[str, str]]:
    links: dict[int, tuple[str, str]] = {
        track_number: (section.path, section.title)
        for section in reading_catalog.sections
        for track_number in section.track_numbers
    }
    documents_by_target = {
        f"companion:{document.slug}": document
        for document in supplemental_documents
    }
    for track in audiobook_catalog.tracks:
        companion_target = next(
            (target for target in track.target_entry_ids if target.startswith("companion:")),
            None,
        )
        document = documents_by_target.get(companion_target or "")
        if document:
            links[track.track_number] = (supplemental_html_href(document), document.title)
    return links


def track_read_actions(
    track: AudiobookTrack,
    reading_links: dict[int, tuple[str, str]],
) -> str:
    target = reading_links.get(track.track_number)
    if not target:
        return ""
    href, _title = target
    return f'<a class="button" href="{escape(href)}">Read</a>'


def render_listen_bar(track: AudiobookTrack) -> str:
    duration = format_audio_duration(track.duration_seconds) if track.duration_seconds is not None else ""
    player = audio_player(track.public_audio_path, track.title) if track.is_available else ""
    download = (
        f'<a class="listen-download" href="{escape(track.public_audio_path)}" download>Download</a>'
        if track.is_available
        else '<span class="audio-unavailable">Audio unavailable</span>'
    )
    return f"""<section class="listen-bar" aria-label="Listen to {escape(track.title)}">
  <div class="listen-bar-copy">
    <span class="listen-icon" aria-hidden="true">{AUDIOBOOK_ICON_SVG}</span>
    <span class="listen-bar-title"><small>Track {track.track_number:02d}</small><strong>{escape(track.title)}</strong></span>
    {f'<span class="listen-bar-time">{escape(duration)}</span>' if duration else ''}
  </div>
  {player}
  {download}
</section>"""


def render_track_player(track: AudiobookTrack, *, compact: bool = False) -> str:
    player = audio_player(track.public_audio_path, track.title) if track.is_available else ""
    unavailable = (
        "" if track.is_available else '<p class="audio-unavailable">Audio is unavailable in this local preview.</p>'
    )
    download = (
        f'<a class="button" href="{escape(track.public_audio_path)}" download>Download MP3</a>'
        if track.is_available
        else ""
    )
    runtime = audio_runtime(track.duration_seconds)
    if compact:
        return render_listen_bar(track)
    return f"""<article class="audio-track-card" id="track-{track.track_number:02d}">
  <div class="audio-track-copy">
    <p class="eyebrow">Track {track.track_number:02d}</p>
    <h2>{escape(track.title)}</h2>
    {runtime}
  </div>
  {player}
  <div class="card-actions">{download}</div>
  {unavailable}
</article>"""


def render_entry_audio_section(tracks: Iterable[AudiobookTrack]) -> str:
    ordered = tuple(tracks)
    if not ordered:
        return ""
    bars = "\n".join(render_track_player(track, compact=True) for track in ordered)
    return f"""<section class="entry-audio-section compact-listening" aria-label="Listen to this section">
  {bars}
</section>"""


def render_audiobook(
    catalog: AudiobookCatalog,
    reading_links: dict[int, tuple[str, str]],
    portable_catalog: PortableCatalog | None = None,
) -> str:
    track_rows = []
    for track in catalog.tracks:
        row = render_track_player(track)
        read_actions = track_read_actions(track, reading_links)
        if read_actions:
            row = row.replace(
                '<div class="card-actions">',
                f'<div class="card-actions">{read_actions}',
                1,
            )
        track_rows.append(row)
    full = catalog.full_audiobook
    full_player = audio_player(full.public_audio_path, full.title) if full.is_available else ""
    full_download = (
        f'<a class="button primary" href="{escape(full.public_audio_path)}" download>Download complete audiobook</a>'
        if full.is_available
        else ""
    )
    chaptered_download = (
        portable_artifact_action(portable_catalog.m4b, "Download with chapters (M4B)")
        if portable_catalog
        else ""
    )
    portable_handoff = render_portable_handoff(portable_catalog, compact=True) if portable_catalog else ""
    full_size = format_file_size(full.probe.size_bytes) if full.probe else ""
    full_meta = " · ".join(
        value
        for value in (
            format_audio_duration(full.duration_seconds) if full.duration_seconds is not None else "",
            full_size,
            "MP3" if full.is_available else "",
        )
        if value
    )
    full_unavailable = (
        ""
        if full.is_available
        else '<p class="audio-unavailable">The complete audiobook has not been assembled for this local preview.</p>'
    )
    full_section = f"""<section class="audio-feature-card" id="full-audiobook">
  <p class="eyebrow">Complete audiobook</p>
  <h2>{escape(full.title)}</h2>
  <p>Listen from beginning to end in one file, or download it for later.</p>
  {f'<p class="audio-runtime">{escape(full_meta)}</p>' if full_meta else ''}
  {full_player}
  <div class="card-actions">{full_download}{chaptered_download}<a class="button" href="reading-apps.html">Help choosing a format</a></div>
  {full_unavailable}
</section>"""
    skipped_counts: dict[str, int] = {}
    for item in catalog.skipped_entries:
        reason = str(item.get("reason") or "reference material")
        skipped_counts[reason] = skipped_counts.get(reason, 0) + 1
    skipped_rows = "\n".join(
        f"<li>{friendly_skip_group(escape(reason), count)}</li>" for reason, count in sorted(skipped_counts.items())
    )
    body = f"""
    <section class="page-title">
      <h1>Audiobook</h1>
      <p>Listen to the complete family audiobook or choose any individual story below. No app or account is needed.</p>
      <p class="audio-attribution">Narrated with the Matilda AI voice using ElevenLabs Multilingual v2. Tables, indexes, and dense records stay in the readable archive.</p>
    </section>
    {full_section}
    {portable_handoff}
    <section class="section-list audio-track-list">
      <div class="section-heading">
        <h2>Individual recordings</h2>
        <p>{len(catalog.tracks)} tracks in listening order.</p>
      </div>
      <div class="audio-track-grid">{''.join(track_rows)}</div>
    </section>
    <section class="archive-grid">
      <article>
        <h2>Reference Material</h2>
        <ul>{skipped_rows or '<li>No skipped reference entries recorded.</li>'}</ul>
      </article>
    </section>
"""
    return html_page("Audiobook", body, "Audio")


def write_site_assets(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "site.css").write_text(SITE_CSS, encoding="utf-8")
    (assets_dir / "search.js").write_text(SEARCH_JS, encoding="utf-8")
    (assets_dir / "audio.js").write_text(AUDIO_JS, encoding="utf-8")
    (output_dir / ".htaccess").write_text(
        "AddType application/epub+zip .epub\n"
        "AddType audio/mp4 .m4b\n",
        encoding="utf-8",
    )


def write_scan_images(output_dir: Path) -> None:
    require_file(PROCESSED_DIR, "processed page images")
    scans_dir = output_dir / "images" / "scans"
    scans_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(PROCESSED_DIR.glob("page-*.jpg")):
        destination = scans_dir / source.name
        with Image.open(source) as image:
            image = image.convert("RGB")
            max_width = 1400
            if image.width > max_width:
                ratio = max_width / image.width
                image = image.resize((max_width, round(image.height * ratio)), Image.Resampling.LANCZOS)
            image.save(destination, quality=86, optimize=True, progressive=True)


def copy_doc_web_images(bundle: Bundle, output_dir: Path) -> None:
    source = bundle.root / "images"
    require_file(source, "doc-web image crops")
    destination = output_dir / "images" / "doc-web"
    shutil.copytree(source, destination, dirs_exist_ok=True)


def copy_supplemental_images(output_dir: Path, supplemental_documents: list[SupplementalSiteDocument]) -> None:
    root = output_dir / "images" / "companion"
    for document in supplemental_documents:
        destination = root / document.slug
        destination.mkdir(parents=True, exist_ok=True)
        for source in supplemental_page_paths(document):
            target = destination / source.name
            with Image.open(source) as image:
                image = image.convert("RGB")
                max_width = 1400
                if image.width > max_width:
                    ratio = max_width / image.width
                    image = image.resize((max_width, round(image.height * ratio)), Image.Resampling.LANCZOS)
                image.save(target, quality=86, optimize=True, progressive=True)


def copy_companion_doc_web_images(output_dir: Path, supplemental_documents: list[SupplementalSiteDocument]) -> None:
    root = output_dir / "images" / "companion-doc-web"
    for document in supplemental_documents:
        source = document.doc_web_bundle_root / "images"
        if not source.exists():
            continue
        destination = root / document.slug
        shutil.copytree(source, destination, dirs_exist_ok=True)


def copy_downloads(output_dir: Path, supplemental_documents: list[SupplementalSiteDocument]) -> None:
    downloads_dir = output_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    for source in (DISTRIBUTION_PDF, ARCHIVAL_PDF):
        if source.exists():
            shutil.copy2(source, downloads_dir / source.name)
    for document in supplemental_documents:
        for source in (document.distribution_pdf, document.archival_pdf):
            shutil.copy2(source, downloads_dir / source.name)


def copy_structured_data(bundle: Bundle, output_dir: Path) -> None:
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundle.manifest_path, data_dir / "structured-manifest.json")
    if bundle.provenance_path:
        shutil.copy2(bundle.provenance_path, data_dir / "block-provenance.jsonl")


def write_audio_scripts(output_dir: Path) -> None:
    source = ROOT / "audiobook" / "script"
    if not source.exists():
        return
    destination = output_dir / "script"
    destination.mkdir(parents=True, exist_ok=True)
    for script in sorted(source.glob("*.md")):
        shutil.copy2(script, destination / script.name)


def derive_site_reading_catalog(
    bundle: Bundle,
    entries: list[Entry],
    audiobook_catalog: AudiobookCatalog,
) -> ReadingCatalog:
    sources = [
        ReadingSource(
            entry_id=entry.entry_id,
            title=display_title(bundle, entry),
            kind=entry.kind,
            order=index,
            source_pages=entry.source_pages,
            printed_pages=printable_page_values(entry),
            article_html=read_article_html(bundle, entry),
        )
        for index, entry in enumerate(entries)
    ]
    reading_catalog = build_reading_catalog(sources, audiobook_catalog.tracks)
    if reading_catalog.unassigned_source_entry_ids:
        raise SystemExit(
            "Semantic reading sections left source entries unassigned: "
            + ", ".join(reading_catalog.unassigned_source_entry_ids)
        )
    if reading_catalog.unassigned_track_numbers:
        raise SystemExit(
            "Semantic reading sections left narrative tracks without a Read target: "
            + ", ".join(f"{number:02d}" for number in reading_catalog.unassigned_track_numbers)
        )
    block_ids = lambda html: re.findall(r'\bid="([^"]+)"', html)  # noqa: E731 - compact invariant helper.
    source_blocks = Counter(
        block_id
        for source in sources
        for block_id in block_ids(source.article_html)
    )
    section_blocks = Counter(
        block_id
        for section in reading_catalog.sections
        for block_id in block_ids(section.article_html)
    )
    if source_blocks != section_blocks:
        missing = sorted((source_blocks - section_blocks).elements())[:10]
        duplicated = sorted((section_blocks - source_blocks).elements())[:10]
        raise SystemExit(
            "Semantic reading sections changed canonical doc-web block coverage; "
            f"missing={missing}, duplicated={duplicated}"
        )
    return reading_catalog


def render_legacy_reading_redirect(target_path: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escape(target_path)}">
  <link rel="canonical" href="{escape(target_path)}">
  <title>Reading section moved | {escape(SITE_TITLE)}</title>
</head>
<body>
  <p>This material is now part of a complete reading section. <a href="{escape(target_path)}">Continue reading</a>.</p>
</body>
</html>
"""


def write_reading_catalog(
    output_dir: Path,
    reading_catalog: ReadingCatalog,
) -> None:
    payload = {
        "schema_version": "alain_semantic_reading_sections_v1",
        "section_count": len(reading_catalog.sections),
        "sections": [
            {
                "section_id": section.section_id,
                "title": section.title,
                "path": section.path,
                "kind": section.kind,
                "part_id": section.part_id,
                "source_entry_ids": list(section.source_entry_ids),
                "source_pages": list(section.source_pages),
                "track_numbers": list(section.track_numbers),
            }
            for section in reading_catalog.sections
        ],
        "redirects": reading_catalog.redirects,
    }
    internal = output_dir / "_internal"
    internal.mkdir(parents=True, exist_ok=True)
    (internal / "reading-sections.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def copy_audiobook_assets(catalog: AudiobookCatalog, output_dir: Path) -> tuple[int, int]:
    copied_count = 0
    copied_bytes = 0
    for track in catalog.tracks:
        if not track.is_available:
            continue
        destination = output_dir / track.public_audio_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(track.audio_source_path, destination)
        copied_count += 1
        copied_bytes += track.audio_source_path.stat().st_size
    full = catalog.full_audiobook
    if full.is_available:
        destination = output_dir / full.public_audio_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full.audio_source_path, destination)
        copied_count += 1
        copied_bytes += full.audio_source_path.stat().st_size
    internal = output_dir / "_internal" / "audiobook"
    internal.mkdir(parents=True, exist_ok=True)
    shutil.copy2(catalog.manifest_path, internal / "manifest.json")
    return copied_count, copied_bytes


def write_search_index(
    output_dir: Path,
    reading_catalog: ReadingCatalog,
    supplemental_documents: list[SupplementalSiteDocument],
) -> None:
    rows = []
    for section in reading_catalog.sections:
        scan_count = len(section.source_pages)
        rows.append(
            {
                "entry_id": section.section_id,
                "kind": section.kind,
                "title": section.title,
                "url": section.path,
                "source_label": "1 source scan" if scan_count == 1 else f"{scan_count} source scans",
                "text": re.sub(r"\s+", " ", html_to_text(section.article_html)).strip(),
            }
        )
    for document in supplemental_documents:
        article = companion_doc_web_article_html(document)
        rows.append(
            {
                "entry_id": f"supplemental-{document.slug}",
                "kind": "companion document",
                "title": document.title,
                "url": supplemental_html_href(document),
                "source_label": "1 page" if document.page_count == 1 else f"{document.page_count} pages",
                "text": re.sub(r"\s+", " ", f"{document.title} {document.description} {html_to_text(article)}").strip(),
            }
        )
    (output_dir / "search-index.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_build_summary(
    output_dir: Path,
    bundle: Bundle,
    entries: list[Entry],
    reading_catalog: ReadingCatalog,
    supplemental_documents: list[SupplementalSiteDocument],
    audiobook_catalog: AudiobookCatalog,
    published_audio_count: int,
    published_audio_bytes: int,
    published_portable_count: int,
    published_portable_bytes: int,
) -> None:
    summary = {
        "schema_version": "alain_family_site_build_summary_v1",
        "bundle_snapshot_id": bundle.active.get("snapshotId"),
        "bundle_root": bundle.active.get("bundleRoot"),
        "entry_count": len(entries),
        "reading_section_count": len(reading_catalog.sections),
        "chapter_count": sum(1 for entry in entries if entry.kind == "chapter"),
        "page_entry_count": sum(1 for entry in entries if entry.kind == "page"),
        "supplemental_document_count": len(supplemental_documents),
        "supplemental_html_count": len(supplemental_documents),
        "supplemental_doc_web_entry_count": sum(
            len(json.loads(document.doc_web_manifest_path.read_text(encoding="utf-8")).get("entries") or [])
            for document in supplemental_documents
        ),
        "supplemental_doc_web_image_count": sum(document.doc_web_image_count for document in supplemental_documents),
        "figure_count": sum(read_article_html(bundle, entry).lower().count("<figure") for entry in entries),
        "table_count": sum(read_article_html(bundle, entry).lower().count("<table") for entry in entries),
        "audiobook_track_count": len(audiobook_catalog.tracks),
        "published_audio_file_count": published_audio_count,
        "published_audio_bytes": published_audio_bytes,
        "complete_audiobook_published": audiobook_catalog.full_audiobook.is_available,
        "published_portable_file_count": published_portable_count,
        "published_portable_bytes": published_portable_bytes,
        "public_host": PUBLIC_HOST,
    }
    internal_dir = output_dir / "_internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    (internal_dir / "build-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build(output_dir: Path, *, require_complete_audio: bool = False) -> None:
    bundle = load_bundle()
    entries = ordered_entries(bundle)
    supplemental_documents = load_supplemental_documents()
    try:
        audiobook_catalog = load_audiobook_catalog(AUDIOBOOK_MANIFEST_PATH)
        portable_catalog = load_portable_catalog(PORTABLE_MANIFEST_PATH)
    except (AudiobookManifestError, PortableEditionError) as exc:
        raise SystemExit(f"Invalid publication manifest: {exc}") from exc
    if require_complete_audio:
        validation = validate_audiobook_catalog(audiobook_catalog, release=True, decode=False)
        if validation.errors:
            raise SystemExit(
                "Release-ready family-site build requires complete audiobook media:\n"
                + "\n".join(f"- {error}" for error in validation.errors)
            )
        require_portable_artifacts(portable_catalog)
        epub_validation = validate_epub(
            portable_catalog.epub.output_path,
            maximum_bytes=int(portable_catalog.epub.settings.get("maximum_bytes") or 0),
        )
        m4b_validation = validate_m4b(portable_catalog.m4b.output_path, audiobook_catalog, portable_catalog)
        portable_errors = epub_validation.errors + m4b_validation.errors
        if portable_errors:
            raise SystemExit(
                "Release-ready family-site build requires valid portable editions:\n"
                + "\n".join(f"- {error}" for error in portable_errors)
            )
    reading_catalog = derive_site_reading_catalog(bundle, entries, audiobook_catalog)
    reading_links = audio_reading_links(reading_catalog, supplemental_documents, audiobook_catalog)
    audio_by_entry_id = tracks_by_target_entry_id(audiobook_catalog)
    expected_read_tracks = {
        track.track_number
        for track in audiobook_catalog.tracks
        if track.target_entry_ids
    }
    missing_read_tracks = sorted(expected_read_tracks - set(reading_links))
    if missing_read_tracks:
        raise SystemExit(
            "Audiobook tracks do not match rendered semantic reading sections: "
            + ", ".join(f"{number:02d}" for number in missing_read_tracks)
        )
    clean_dir(output_dir)
    write_site_assets(output_dir)
    write_scan_images(output_dir)
    copy_doc_web_images(bundle, output_dir)
    copy_supplemental_images(output_dir, supplemental_documents)
    copy_companion_doc_web_images(output_dir, supplemental_documents)
    copy_downloads(output_dir, supplemental_documents)
    published_portable_count, published_portable_bytes = copy_portable_artifacts(portable_catalog, output_dir)
    copy_structured_data(bundle, output_dir)
    write_audio_scripts(output_dir)
    published_audio_count, published_audio_bytes = copy_audiobook_assets(audiobook_catalog, output_dir)
    write_reading_catalog(output_dir, reading_catalog)

    (output_dir / "index.html").write_text(
        render_home(bundle, entries, reading_catalog, supplemental_documents, audiobook_catalog, portable_catalog),
        encoding="utf-8",
    )
    (output_dir / "book.html").write_text(render_book(reading_catalog, portable_catalog), encoding="utf-8")
    (output_dir / "archive.html").write_text(render_archive(bundle, entries, supplemental_documents), encoding="utf-8")
    (output_dir / "audiobook.html").write_text(
        render_audiobook(audiobook_catalog, reading_links, portable_catalog),
        encoding="utf-8",
    )
    (output_dir / "reading-apps.html").write_text(
        render_reading_apps(portable_catalog, audiobook_catalog),
        encoding="utf-8",
    )
    for document in supplemental_documents:
        target_id = f"companion:{document.slug}"
        (output_dir / supplemental_html_filename(document)).write_text(
            render_companion_document(document, audio_by_entry_id.get(target_id, ())),
            encoding="utf-8",
        )
    tracks_by_number = {track.track_number: track for track in audiobook_catalog.tracks}
    for index, section in enumerate(reading_catalog.sections):
        section_tracks = tuple(
            tracks_by_number[number]
            for number in section.track_numbers
            if number in tracks_by_number
        )
        (output_dir / section.path).write_text(
            render_reading_section_page(reading_catalog, index, section_tracks),
            encoding="utf-8",
        )
    for entry in entries:
        target_path = reading_catalog.redirects.get(entry.entry_id, "book.html")
        (output_dir / entry.path).write_text(
            render_legacy_reading_redirect(target_path),
            encoding="utf-8",
        )
    write_search_index(output_dir, reading_catalog, supplemental_documents)
    write_build_summary(
        output_dir,
        bundle,
        entries,
        reading_catalog,
        supplemental_documents,
        audiobook_catalog,
        published_audio_count,
        published_audio_bytes,
        published_portable_count,
        published_portable_bytes,
    )
    print(f"built family site: {output_dir}")
    print(f"source entries: {len(entries)}")
    print(f"reading sections: {len(reading_catalog.sections)}")
    print(f"supplemental documents: {len(supplemental_documents)}")
    print(f"published audio files: {published_audio_count}")
    print(f"published portable files: {published_portable_count}")


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Build the Alain Lessard family archive website from the active doc-web bundle.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--require-complete-audio",
        action="store_true",
        help="Fail unless all reviewed audio and portable EPUB/M4B release artifacts are present and valid.",
    )
    args = parser.parse_args()
    build(Path(args.output).resolve(), require_complete_audio=args.require_complete_audio)
    return 0


SITE_CSS = """
:root {
  color-scheme: light;
  --bg: #f7f8f6;
  --paper: #ffffff;
  --ink: #22231f;
  --muted: #626861;
  --line: #d8ddd5;
  --deep: #143d3b;
  --deep-2: #1f5b55;
  --accent: #8d2f23;
  --accent-2: #c1912f;
  --shadow: 0 18px 38px rgba(20, 34, 30, 0.12);
  --radius: 8px;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  font-size: 100%;
  scroll-padding-top: 6.5rem;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.55;
  color: var(--ink);
  background: var(--bg);
}

a {
  color: var(--deep-2);
  text-underline-offset: 0.16em;
}

img {
  max-width: 100%;
  height: auto;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 1.4rem;
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(12px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 16rem;
  color: var(--ink);
  text-decoration: none;
}

.brand-mark {
  display: inline-grid;
  place-items: center;
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  color: #fff;
  background: var(--deep);
  font-weight: 700;
}

.brand strong,
.brand small {
  display: block;
}

.brand small {
  max-width: 32rem;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.25;
}

.site-nav {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  flex-wrap: wrap;
}

.nav-link {
  padding: 0.45rem 0.7rem;
  color: var(--ink);
  text-decoration: none;
  border-radius: var(--radius);
}

.nav-link:hover,
.nav-link.is-active {
  color: #fff;
  background: var(--deep);
}

.hero {
  min-height: 58vh;
  display: flex;
  align-items: flex-end;
  color: #fff;
  background-image: linear-gradient(90deg, rgba(10, 25, 24, 0.9), rgba(10, 25, 24, 0.58), rgba(10, 25, 24, 0.2)), url("../images/scans/page-001.jpg");
  background-size: cover;
  background-position: center;
}

.hero-inner {
  width: min(72rem, 100%);
  padding: 5rem 1.4rem 4.6rem;
  margin: 0 auto;
}

.hero h1 {
  max-width: 46rem;
  margin: 0;
  font-size: 4rem;
  line-height: 1.02;
  letter-spacing: 0;
}

.hero p {
  max-width: 40rem;
  margin: 1rem 0 0;
  font-size: 1.2rem;
}

.eyebrow {
  margin: 0 0 0.45rem;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.hero .eyebrow {
  color: #f4cf72;
}

.hero-actions,
.card-actions,
.reader-nav {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 1.3rem;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.55rem;
  padding: 0.55rem 0.9rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  color: var(--deep);
  background: #fff;
  font-weight: 700;
  text-decoration: none;
}

.button.primary {
  color: #fff;
  border-color: var(--accent);
  background: var(--accent);
}

.button.disabled {
  color: var(--muted);
  background: #eef0ec;
}

.intro-grid,
.archive-grid,
.section-list,
.page-title,
.book-tools,
.book-layout,
.entry-header,
.reader-shell,
.reader-nav,
.stat-band {
  width: min(72rem, calc(100% - 2.8rem));
  margin-left: auto;
  margin-right: auto;
}

.intro-grid,
.archive-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  padding: 2.2rem 0;
}

.archive-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.intro-grid article,
.archive-grid article,
.entry-card,
.source-panel,
.book-tools,
.toc-panel,
.compact-entry,
.part-section {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.entry-list,
.toc-panel,
.cards,
.entry-card,
.compact-entry,
.part-section,
.part-links {
  min-width: 0;
}

.entry-card,
.compact-entry,
.toc-panel,
.part-links {
  overflow-wrap: anywhere;
}

.intro-grid article,
.archive-grid article,
.entry-card,
.source-panel,
.book-tools,
.toc-panel,
.part-section {
  padding: 1rem;
}

.intro-grid h2,
.archive-grid h2,
.section-heading h2,
.page-title h1,
.entry-header h1,
.entry-list h2,
.part-heading h2,
.source-panel h2 {
  margin: 0 0 0.55rem;
  line-height: 1.15;
  letter-spacing: 0;
}

.stat-band {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.8rem;
  padding: 1.1rem 0 0.5rem;
}

.stat-band div {
  padding: 1rem;
  background: var(--deep);
  color: #fff;
  border-radius: var(--radius);
}

.stat-band strong {
  display: block;
  font-size: 2rem;
  line-height: 1;
}

.stat-band span {
  display: block;
  margin-top: 0.35rem;
}

.section-list {
  padding: 2.2rem 0 3rem;
}

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.section-heading p {
  max-width: 34rem;
  margin: 0;
  color: var(--muted);
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.archive-downloads {
  width: min(72rem, calc(100% - 2.8rem));
  margin-left: auto;
  margin-right: auto;
}

.entry-card h3 {
  margin: 0 0 0.55rem;
  font-size: 1.08rem;
  line-height: 1.25;
  letter-spacing: 0;
}

.entry-card a {
  overflow-wrap: anywhere;
}

.entry-card p:last-child {
  margin-bottom: 0;
  color: var(--muted);
}

.page-title,
.entry-header {
  padding: 2.2rem 0 1rem;
}

.page-title h1 {
  font-size: 2.2rem;
}

.entry-header h1 {
  max-width: 54rem;
  font-size: 2.2rem;
  overflow-wrap: anywhere;
}

.page-title p {
  max-width: 46rem;
  margin: 0.4rem 0 0;
  color: var(--muted);
}

.book-tools {
  margin-top: 0.8rem;
  padding: 1rem;
}

.search-label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 700;
}

.search-input {
  width: 100%;
  min-height: 2.8rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  font: inherit;
}

.search-results {
  display: grid;
  gap: 0.55rem;
  margin-top: 0.8rem;
}

.search-result {
  padding: 0.75rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fbfcfa;
}

.search-result h3,
.search-result p {
  margin: 0;
}

.search-result p {
  color: var(--muted);
}

.book-layout {
  display: grid;
  grid-template-columns: 18rem minmax(0, 1fr);
  gap: 1.2rem;
  padding: 1.4rem 0 3rem;
}

.toc-panel {
  position: sticky;
  top: 5.2rem;
  max-height: calc(100vh - 6.5rem);
  overflow: auto;
}

.toc-panel ol {
  margin: 0;
  padding-left: 1.25rem;
}

.toc-panel li {
  margin: 0 0 0.7rem;
}

.toc-panel span,
.compact-entry span {
  display: block;
  color: var(--muted);
  font-size: 0.86rem;
}

.entry-list h2 {
  margin-top: 1.8rem;
}

.entry-list h2:first-child {
  margin-top: 0;
}

.part-section {
  margin-bottom: 1rem;
  scroll-margin-top: 6.5rem;
}

.part-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--line);
}

.part-heading p {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
}

.part-links {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.1rem 1rem;
  margin: 0.75rem 0 0;
  padding: 0;
  list-style: none;
}

.part-links li {
  padding: 0.35rem 0;
  border-bottom: 1px solid #edf0eb;
}

.part-links li.heading-level-2 {
  padding-left: 0.9rem;
}

.part-links li.heading-level-2 a::before {
  content: "";
  display: inline-block;
  width: 0.45rem;
  height: 0.45rem;
  margin-right: 0.4rem;
  border-left: 1px solid var(--muted);
  border-bottom: 1px solid var(--muted);
  transform: translateY(-0.12rem);
}

.compact-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.6rem;
}

.compact-entry {
  padding: 0.7rem;
}

.reader-nav {
  justify-content: space-between;
  padding: 0.2rem 0 1rem;
}

.reader-shell {
  display: grid;
  grid-template-columns: 15rem minmax(0, 54rem);
  gap: 1.4rem;
  align-items: start;
  padding: 0.4rem 0 2.2rem;
}

.source-panel {
  position: sticky;
  top: 5.2rem;
}

.source-panel p {
  color: var(--muted);
}

.scan-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.scan-links a,
.scan-gap {
  padding: 0.35rem 0.45rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fbfcfa;
  font-size: 0.85rem;
  text-decoration: none;
}

.book-article {
  min-width: 0;
  overflow: hidden;
  padding: 2.2rem;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.05rem;
}

.book-article h1,
.book-article h2,
.book-article h3,
.book-article h4,
.book-article h5,
.book-article h6 {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.25;
  letter-spacing: 0;
  scroll-margin-top: 6.5rem;
}

.book-article [id] {
  scroll-margin-top: 6.5rem;
}

.book-article h1 {
  margin-top: 0;
  font-size: 2rem;
}

.book-article p {
  margin: 0 0 0.85rem;
}

.book-article figure {
  margin: 1.45rem 0;
  text-align: center;
}

.book-article .decorative-break {
  width: 7rem;
  margin: 1.8rem auto;
  border: 0;
  border-top: 2px solid var(--accent-2);
}

.book-article figure img {
  display: inline-block;
  max-height: 34rem;
  object-fit: contain;
  border-radius: 4px;
}

.book-article figcaption {
  max-width: 42rem;
  margin: 0.5rem auto 0;
  color: var(--muted);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 0.9rem;
  font-style: italic;
}

.book-article .table-scroll {
  width: 100%;
  max-width: 100%;
  margin: 1.2rem 0;
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 4px;
}

.book-article table {
  width: 100%;
  min-width: 38rem;
  margin: 0;
  border-collapse: collapse;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 0.92rem;
}

.book-article th,
.book-article td {
  padding: 0.45rem 0.55rem;
  border: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
}

.book-article th {
  background: #eef4ef;
}

.book-article tr:nth-child(even) td {
  background: #fbfcfa;
}

.book-article ul,
.book-article ol {
  padding-left: 1.5rem;
}

.companion-document .doc-web-entry + .doc-web-entry {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--line);
}

.companion-document .companion-story-section + .companion-story-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--line);
}

.companion-document .doc-web-entry > :first-child {
  margin-top: 0;
}

.companion-document .companion-story-section > :first-child {
  margin-top: 0;
}

.companion-context-note {
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--line);
  color: var(--muted);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.companion-toc {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line);
}

.companion-toc h2 {
  margin-top: 0;
}

.companion-toc ol {
  margin: 0;
  padding-left: 1.25rem;
}

.companion-toc li {
  margin: 0 0 0.5rem;
}

.companion-toc a {
  overflow-wrap: anywhere;
}

.companion-source-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.companion-page {
  margin: 0;
  padding: 0.75rem;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.companion-page img {
  display: block;
  width: 100%;
  border-radius: 4px;
}

.companion-page figcaption {
  margin-top: 0.45rem;
  color: var(--muted);
  font-size: 0.9rem;
  text-align: center;
}

.audio-feature-card,
.audio-track-card,
.listen-bar {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.audio-feature-card {
  margin: 0 auto 2rem;
  padding: 1.5rem;
  max-width: 72rem;
}

.audio-feature-card h2,
.audio-track-card h2 {
  margin-top: 0;
}

.audio-track-list,
.entry-audio-section {
  margin: 0 auto 2rem;
  max-width: 72rem;
}

.audio-track-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.audio-track-card {
  padding: 1.2rem;
  min-width: 0;
}

.audio-track-copy {
  min-width: 0;
}

.audio-player {
  display: block;
  width: 100%;
  margin: 0.85rem 0;
}

.audio-runtime,
.audio-attribution,
.audio-unavailable {
  color: var(--muted);
}

.compact-listening {
  margin-bottom: 1rem;
}

.listen-bar {
  display: grid;
  grid-template-columns: minmax(15rem, 1fr) minmax(18rem, 1.4fr) auto;
  gap: 0.85rem;
  align-items: center;
  padding: 0.65rem 0.8rem;
  min-width: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.listen-bar-copy {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.7rem;
  align-items: center;
  min-width: 0;
}

.listen-icon {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  color: var(--accent);
  background: rgba(141, 47, 35, 0.1);
  border: 1px solid rgba(141, 47, 35, 0.14);
  border-radius: 0.55rem;
}

.listen-icon-mark {
  display: block;
  width: 1.25rem;
  height: 1.25rem;
}

.listen-bar-title {
  display: grid;
  gap: 0.08rem;
  min-width: 0;
}

.listen-bar-title small,
.listen-bar-time {
  color: var(--muted);
}

.listen-bar-title strong {
  overflow-wrap: anywhere;
}

.listen-bar .audio-player {
  margin: 0;
  min-width: 0;
}

.listen-download {
  color: var(--accent-strong);
  font-weight: 700;
  white-space: nowrap;
}

.portable-handoff,
.device-help-grid {
  width: min(72rem, calc(100% - 2.8rem));
  margin-left: auto;
  margin-right: auto;
}

.portable-handoff {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(18rem, 1fr);
  align-items: center;
  gap: 1.4rem;
  margin-top: 1rem;
  margin-bottom: 2rem;
  padding: 1.4rem;
  color: #fff;
  background: var(--deep);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.portable-handoff.compact {
  margin-top: 0;
  margin-bottom: 2.2rem;
}

.portable-handoff .eyebrow {
  color: #f4cf72;
}

.portable-handoff h2,
.portable-handoff p {
  margin-top: 0;
}

.portable-handoff p:last-child {
  margin-bottom: 0;
  color: #eef4ef;
}

.portable-actions {
  display: grid;
  gap: 0.65rem;
}

.portable-actions .button {
  width: 100%;
  justify-content: space-between;
  gap: 1rem;
  text-align: left;
}

.button-meta {
  font-size: 0.78rem;
  font-weight: 500;
  white-space: nowrap;
}

.device-help-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  padding: 0 0 3rem;
}

.device-help-grid article {
  padding: 1.2rem;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.device-help-grid h2 {
  margin-top: 0;
}

.device-help-grid li + li {
  margin-top: 0.45rem;
}

.site-footer {
  padding: 2rem 1.4rem;
  color: var(--muted);
  background: #fff;
  border-top: 1px solid var(--line);
  text-align: center;
}

@media (max-width: 880px) {
  .site-header,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .brand {
    min-width: 0;
  }

  .hero h1 {
    font-size: 2.7rem;
  }

  .intro-grid,
  .archive-grid,
  .cards,
  .stat-band,
  .book-layout,
    .compact-grid,
    .part-links,
    .reader-shell,
    .companion-source-grid,
    .audio-track-grid,
    .portable-handoff,
    .device-help-grid {
    grid-template-columns: 1fr;
  }

  .listen-bar {
    grid-template-columns: 1fr;
    gap: 0.55rem;
  }

  .listen-download {
    justify-self: start;
  }

  .toc-panel,
  .source-panel {
    position: static;
    max-height: none;
  }

  .book-article {
    padding: 1.2rem;
  }
}
"""


SEARCH_JS = """
(async () => {
  const input = document.querySelector("#site-search");
  const results = document.querySelector("#search-results");
  if (!input || !results) return;

  const response = await fetch("search-index.json?v=__SITE_ASSET_VERSION__");
  const index = await response.json();

  function snippet(text, term) {
    const haystack = text.toLowerCase();
    const needle = term.toLowerCase();
    const at = haystack.indexOf(needle);
    if (at === -1) return text.slice(0, 210);
    const start = Math.max(0, at - 80);
    const end = Math.min(text.length, at + needle.length + 140);
    return `${start > 0 ? "... " : ""}${text.slice(start, end)}${end < text.length ? " ..." : ""}`;
  }

  function render(query) {
    const term = query.trim();
    if (term.length < 2) {
      results.innerHTML = "";
      return;
    }
    const normalized = term.toLowerCase();
    const matches = index
      .map((row) => {
        const titleHit = row.title.toLowerCase().includes(normalized);
        const textAt = row.text.toLowerCase().indexOf(normalized);
        if (!titleHit && textAt === -1) return null;
        return { row, score: titleHit ? 0 : textAt + 10 };
      })
      .filter(Boolean)
      .sort((a, b) => a.score - b.score)
      .slice(0, 12);

    results.innerHTML = matches
      .map(({ row }) => `
        <article class="search-result">
          <h3><a href="${row.url}">${row.title}</a></h3>
          <p>${row.source_label || row.kind}</p>
          <p>${snippet(row.text, term)}</p>
        </article>
      `)
      .join("") || "<p>No matches found.</p>";
  }

  input.addEventListener("input", (event) => render(event.target.value));
})();
""".replace("__SITE_ASSET_VERSION__", SITE_ASSET_VERSION)


AUDIO_JS = """
(() => {
  const storageKey = "alain-audiobook-progress-v1";
  const players = Array.from(document.querySelectorAll("audio[data-audio-key]"));
  if (!players.length) return;

  let progress = {};
  try {
    progress = JSON.parse(localStorage.getItem(storageKey) || "{}") || {};
  } catch (_error) {
    progress = {};
  }

  function writeProgress() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(progress));
    } catch (_error) {
      // Playback remains fully native when storage is unavailable.
    }
  }

  players.forEach((player) => {
    const key = player.dataset.audioKey;
    let lastSavedSecond = -1;

    player.addEventListener("loadedmetadata", () => {
      const saved = Number(progress[key]);
      if (Number.isFinite(saved) && saved >= 5 && saved < player.duration - 30) {
        player.currentTime = saved;
      }
    });

    player.addEventListener("play", () => {
      players.forEach((other) => {
        if (other !== player && !other.paused) other.pause();
      });
    });

    player.addEventListener("timeupdate", () => {
      const second = Math.floor(player.currentTime);
      if (second < 5 || second - lastSavedSecond < 5) return;
      lastSavedSecond = second;
      if (Number.isFinite(player.duration) && second >= player.duration - 30) {
        delete progress[key];
      } else {
        progress[key] = second;
      }
      writeProgress();
    });

    player.addEventListener("ended", () => {
      delete progress[key];
      writeProgress();
    });
  });
})();
""".strip() + "\n"


if __name__ == "__main__":
    raise SystemExit(cli_main())
