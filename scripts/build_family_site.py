#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_BUNDLE_PATH = ROOT / "input" / "doc-web-html" / "active-bundle.json"
PROCESSED_DIR = ROOT / "output" / "processed-pages"
PDF_DIR = ROOT / "output" / "pdf"
DISTRIBUTION_PDF = PDF_DIR / "alain-lessard-book-searchable.pdf"
ARCHIVAL_PDF = PDF_DIR / "alain-lessard-book-archival-searchable.pdf"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "family-site"
AUDIOBOOK_MANIFEST_PATH = ROOT / "audiobook" / "manifest.json"

SITE_TITLE = "Alain Lessard"
SITE_SUBTITLE = "Our First Ancestors and A Compilation of Stories of Their Descendants"
PUBLIC_HOST = "https://alain-lessard.copper-dog.com"
BOOK_YEAR = "1987"
SITE_ASSET_VERSION = "20260702-docweb-r2"

ARTICLE_RE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.IGNORECASE | re.DOTALL)
IMAGE_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=")images/', re.IGNORECASE)
IMG_TAG_RE = re.compile(r"<img\b(?![^>]*\bloading=)", re.IGNORECASE)
DECORATIVE_FIGURE_RE = re.compile(
    r'<figure\b[^>]*>\s*<img\b(?![^>]*\bsrc=)[^>]*alt="Decorative line break"[^>]*/?>\s*</figure>',
    re.IGNORECASE,
)
NO_SRC_IMG_RE = re.compile(r"<img\b(?![^>]*\bsrc=)[^>]*>", re.IGNORECASE)
TABLE_RE = re.compile(r"(<table\b.*?</table>)", re.IGNORECASE | re.DOTALL)
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


def ordered_entries(bundle: Bundle) -> list[Entry]:
    entries = [Entry.from_record(record) for record in bundle.manifest.get("entries", [])]
    by_id = {entry.entry_id: entry for entry in entries}
    ordered: list[Entry] = []
    for entry_id in bundle.manifest.get("reading_order") or []:
        if entry_id in by_id:
            ordered.append(by_id.pop(entry_id))
    ordered.extend(sorted(by_id.values(), key=lambda entry: (entry.order, entry.entry_id)))
    return ordered


def read_article_html(bundle: Bundle, entry: Entry) -> str:
    source = bundle.root / entry.path
    require_file(source, f"doc-web entry {entry.entry_id}")
    html = source.read_text(encoding="utf-8")
    match = ARTICLE_RE.search(html)
    if not match:
        raise SystemExit(f"Could not find article body in {source}")
    article = match.group(1).strip()
    article = IMAGE_SRC_RE.sub(r"\1images/doc-web/", article)
    article = IMG_TAG_RE.sub('<img loading="lazy" decoding="async"', article)
    article = DECORATIVE_FIGURE_RE.sub('<hr class="decorative-break">', article)
    article = NO_SRC_IMG_RE.sub("", article)
    article = TABLE_RE.sub(r'<div class="table-scroll">\1</div>', article)
    return article


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


def source_scan_links(entry: Entry) -> str:
    pages = list(entry.source_pages)
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
</body>
</html>
"""


def render_chapter_card(bundle: Bundle, entry: Entry) -> str:
    article = read_article_html(bundle, entry)
    label = entry_meta_label(entry)
    return f"""<article class="entry-card">
  <p class="eyebrow">{escape(entry.kind.title())}{f" | {escape(label)}" if label else ""}</p>
  <h3><a href="{escape(entry.path)}">{escape(entry.title)}</a></h3>
  <p>{escape(excerpt_from_html(article))}</p>
</article>"""


def render_home(bundle: Bundle, entries: list[Entry]) -> str:
    chapters = [entry for entry in entries if entry.kind == "chapter"]
    feature_cards = "\n".join(render_chapter_card(bundle, entry) for entry in chapters[:6])
    table_count = sum(read_article_html(bundle, entry).lower().count("<table") for entry in entries)
    figure_count = sum(read_article_html(bundle, entry).lower().count("<figure") for entry in entries)
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
        <h2>Search and source pages</h2>
        <p>Names, places, and stories can be searched across the reading edition, and each entry links back to its source scans.</p>
      </article>
      <article>
        <h2>Audio handoff</h2>
        <p>Narrative chapters have audiobook scripts prepared separately from reference tables and indexes.</p>
      </article>
    </section>

    <section class="stat-band" aria-label="Edition summary">
      <div><strong>{len(entries)}</strong><span>reading entries</span></div>
      <div><strong>{figure_count}</strong><span>figures and captions</span></div>
      <div><strong>{table_count}</strong><span>structured tables</span></div>
    </section>

    <section class="section-list">
      <div class="section-heading">
        <h2>Start Reading</h2>
        <p>Browse the chapter entries or use the full table of contents on the reading page.</p>
      </div>
      <div class="cards">{feature_cards}</div>
    </section>
"""
    return html_page("Home", body, "Home")


def render_toc(entries: list[Entry]) -> str:
    lines = []
    for entry in entries:
        label = entry_meta_label(entry)
        lines.append(
            f'<li><a href="{escape(entry.path)}">{escape(entry.title)}</a>'
            f'<span>{escape(label or entry.kind.title())}</span></li>'
        )
    return "\n".join(lines)


def render_book(bundle: Bundle, entries: list[Entry]) -> str:
    chapters = [entry for entry in entries if entry.kind == "chapter"]
    pages = [entry for entry in entries if entry.kind == "page"]
    chapter_cards = "\n".join(render_chapter_card(bundle, entry) for entry in chapters)
    page_cards = "\n".join(
        f"""<article class="compact-entry">
  <a href="{escape(entry.path)}">{escape(entry.title)}</a>
  <span>{escape(entry_meta_label(entry) or "Source page")}</span>
</article>"""
        for entry in pages
    )
    body = f"""
    <section class="page-title">
      <h1>Read the Book</h1>
      <p>Search the text, browse the table of contents, and open chapters with their photographs, captions, and tables in place.</p>
    </section>
    <section class="book-tools">
      <label class="search-label" for="site-search">Search the book</label>
      <input id="site-search" class="search-input" type="search" placeholder="Search names, places, stories">
      <div id="search-results" class="search-results" aria-live="polite"></div>
    </section>
    <section class="book-layout">
      <aside class="toc-panel">
        <h2>Contents</h2>
        <ol>{render_toc(entries)}</ol>
      </aside>
      <div class="entry-list">
        <h2>Chapters</h2>
        <div class="cards">{chapter_cards}</div>
        <h2>Page Entries</h2>
        <div class="compact-grid">{page_cards}</div>
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


def render_entry_page(bundle: Bundle, entries: list[Entry], index: int) -> str:
    entry = entries[index]
    article = read_article_html(bundle, entry)
    label = entry_meta_label(entry)
    body = f"""
    <section class="entry-header">
      <p class="eyebrow">{escape(entry.kind.title())}{f" | {escape(label)}" if label else ""}</p>
    </section>
    {entry_nav(entries, index)}
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
    return html_page(entry.title, body, "Read")


def render_archive(bundle: Bundle, entries: list[Entry]) -> str:
    pdf_cards = []
    for label, pdf in (("Reader PDF", DISTRIBUTION_PDF), ("Archival PDF", ARCHIVAL_PDF)):
        if pdf.exists():
            size_mb = pdf.stat().st_size / 1024 / 1024
            pdf_cards.append(
                f"""<article class="entry-card">
  <p class="eyebrow">{label}</p>
  <h3><a href="downloads/{pdf.name}">{pdf.name}</a></h3>
  <p>{size_mb:.1f} MiB.</p>
</article>"""
            )
    provenance_link = (
        '<li><a href="data/block-provenance.jsonl">Block provenance data</a></li>' if bundle.provenance_path else ""
    )
    body = f"""
    <section class="page-title">
      <h1>Archive</h1>
      <p>Downloads and source records for the family book edition.</p>
    </section>
    <section class="cards">{''.join(pdf_cards)}</section>
    <section class="archive-grid">
      <article>
        <h2>Structured Reading Files</h2>
        <ul>
          <li><a href="data/structured-manifest.json">Reading manifest</a></li>
          {provenance_link}
          <li>{len(entries)} reading entries</li>
          <li>{len(bundle.manifest.get("asset_roots", []))} asset roots</li>
        </ul>
      </article>
      <article>
        <h2>Source Scans</h2>
        <p>Each chapter and page entry links back to the scans that produced it. Supplemental items can be added as they are scanned.</p>
      </article>
    </section>
"""
    return html_page("Archive", body, "Archive")


def render_audiobook() -> str:
    if AUDIOBOOK_MANIFEST_PATH.exists():
        manifest = json.loads(AUDIOBOOK_MANIFEST_PATH.read_text(encoding="utf-8"))
        entries = manifest.get("entries", [])
        skipped = manifest.get("skipped_entries", [])
    else:
        entries = []
        skipped = []
    script_rows = "\n".join(
        f"""<article class="entry-card">
  <p class="eyebrow">Script {int(entry["index"]):02d}</p>
  <h3><a href="{escape(str(entry["script"]))}">{escape(str(entry["title"]))}</a></h3>
  <p>{escape(str(entry.get("source_label") or ""))}</p>
</article>"""
        for entry in entries
    )
    skipped_rows = "\n".join(
        f"<li>{escape(str(item.get('title')))} <span>{escape(str(item.get('reason')))}</span></li>" for item in skipped
    )
    body = f"""
    <section class="page-title">
      <h1>Audiobook</h1>
      <p>Onward-style narration scripts are prepared for story chapters. Tables, indexes, and dense records stay in the readable archive.</p>
    </section>
    <section class="cards">{script_rows or '<p>No narration scripts have been generated yet.</p>'}</section>
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


def copy_downloads(output_dir: Path) -> None:
    downloads_dir = output_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    for source in (DISTRIBUTION_PDF, ARCHIVAL_PDF):
        if source.exists():
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
    shutil.copytree(source, destination, dirs_exist_ok=True)


def write_search_index(output_dir: Path, bundle: Bundle, entries: list[Entry]) -> None:
    rows = []
    for entry in entries:
        article = read_article_html(bundle, entry)
        rows.append(
            {
                "entry_id": entry.entry_id,
                "kind": entry.kind,
                "title": entry.title,
                "url": entry.path,
                "source_label": entry_meta_label(entry),
                "text": re.sub(r"\s+", " ", html_to_text(article)).strip(),
            }
        )
    (output_dir / "search-index.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_build_summary(output_dir: Path, bundle: Bundle, entries: list[Entry]) -> None:
    summary = {
        "schema_version": "alain_family_site_build_summary_v1",
        "bundle_snapshot_id": bundle.active.get("snapshotId"),
        "bundle_root": bundle.active.get("bundleRoot"),
        "entry_count": len(entries),
        "chapter_count": sum(1 for entry in entries if entry.kind == "chapter"),
        "page_entry_count": sum(1 for entry in entries if entry.kind == "page"),
        "figure_count": sum(read_article_html(bundle, entry).lower().count("<figure") for entry in entries),
        "table_count": sum(read_article_html(bundle, entry).lower().count("<table") for entry in entries),
        "public_host": PUBLIC_HOST,
    }
    internal_dir = output_dir / "_internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    (internal_dir / "build-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build(output_dir: Path) -> None:
    bundle = load_bundle()
    entries = ordered_entries(bundle)
    clean_dir(output_dir)
    write_site_assets(output_dir)
    write_scan_images(output_dir)
    copy_doc_web_images(bundle, output_dir)
    copy_downloads(output_dir)
    copy_structured_data(bundle, output_dir)
    write_audio_scripts(output_dir)

    (output_dir / "index.html").write_text(render_home(bundle, entries), encoding="utf-8")
    (output_dir / "book.html").write_text(render_book(bundle, entries), encoding="utf-8")
    (output_dir / "archive.html").write_text(render_archive(bundle, entries), encoding="utf-8")
    (output_dir / "audiobook.html").write_text(render_audiobook(), encoding="utf-8")
    for index, entry in enumerate(entries):
        (output_dir / entry.path).write_text(render_entry_page(bundle, entries, index), encoding="utf-8")
    write_search_index(output_dir, bundle, entries)
    write_build_summary(output_dir, bundle, entries)
    print(f"built family site: {output_dir}")
    print(f"entries: {len(entries)}")


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Build the Alain Lessard family archive website from the active doc-web bundle.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    build(Path(args.output).resolve())
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
.compact-entry {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.intro-grid article,
.archive-grid article,
.entry-card,
.source-panel,
.book-tools,
.toc-panel {
  padding: 1rem;
}

.intro-grid h2,
.archive-grid h2,
.section-heading h2,
.page-title h1,
.entry-list h2,
.source-panel h2 {
  margin: 0 0 0.55rem;
  line-height: 1.15;
  letter-spacing: 0;
}

.stat-band {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.entry-card h3 {
  margin: 0 0 0.55rem;
  font-size: 1.08rem;
  line-height: 1.25;
  letter-spacing: 0;
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
  .reader-shell {
    grid-template-columns: 1fr;
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

  const response = await fetch("search-index.json?v=20260702-docweb-r2");
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
"""


if __name__ == "__main__":
    raise SystemExit(cli_main())
