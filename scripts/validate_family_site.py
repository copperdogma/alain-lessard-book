#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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
DEFAULT_BUILD_DIR = ROOT / "build" / "family-site"
ASSET_VERSION = "20260702-docweb-r6"
EXPECTED_ENTRY_COUNT = 39
EXPECTED_HTML_PAGE_COUNT = 43
EXPECTED_DOC_WEB_IMAGES = 155
EXPECTED_SCAN_IMAGES = 153
EXPECTED_FIGURES = 155
EXPECTED_FIGCAPTIONS_MIN = 140
EXPECTED_TABLES = 12
EXPECTED_PERSONAL_RECORD_TABLES = 8

SITE_COPY_FILES = ("index.html", "book.html", "archive.html", "audiobook.html")
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
    required = {"index.html", "book.html", "archive.html", "audiobook.html"}
    required.update(str(entry.get("path")) for entry in entries if isinstance(entry, dict) and entry.get("path"))
    for page in sorted(required):
        validation.require((build_dir / page).exists(), f"Required page is missing: {page}")


def check_search_index(build_dir: Path, validation: Validation) -> None:
    index_path = build_dir / "search-index.json"
    index = read_json(index_path, validation, "search index")
    if not isinstance(index, list):
        validation.error("Search index is not a JSON list")
        return
    validation.require(len(index) == EXPECTED_ENTRY_COUNT, f"Expected {EXPECTED_ENTRY_COUNT} search rows, found {len(index)}")
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
        validation.require((build_dir / url).exists(), f"Search row {row_number} points at missing page: {url}")
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

    personal_records = build_dir / "chapter-016.html"
    if personal_records.exists():
        personal_text = personal_records.read_text(encoding="utf-8")
        personal_tables = personal_text.lower().count("<table")
        validation.require(
            personal_tables == EXPECTED_PERSONAL_RECORD_TABLES,
            f"Expected {EXPECTED_PERSONAL_RECORD_TABLES} personal-record tables in chapter-016.html, found {personal_tables}",
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
        if page.name.startswith(("chapter-", "page-")):
            text = page.read_text(encoding="utf-8")
            validation.require(
                bool(re.search(r'<section class="entry-header">.*?<h1>.*?</h1>', text, re.IGNORECASE | re.DOTALL)),
                f"{rel(page, build_dir)} is missing a page-level reader heading",
            )

    audiobook_text = parsed[build_dir / "audiobook.html"].visible_text.lower() if (build_dir / "audiobook.html") in parsed else ""
    validation.require("tables, indexes, and dense records stay" in audiobook_text, "Audiobook page should clearly explain why tables are not narrated")
    validation.require("page 1 page-level material" not in audiobook_text, "Audiobook page should not list raw page-level skip rows")

    book_path = build_dir / "book.html"
    book_html = book_path.read_text(encoding="utf-8") if book_path.exists() else ""
    book_text = parsed[book_path].visible_text if book_path in parsed else ""
    validation.require("Preface" in book_text, "book.html should expose Preface in the contents")
    validation.require("Part I - Alain Family History" in book_text, "book.html should expose Part I in the contents")
    validation.require("Part II - Alain Family Stories" in book_text, "book.html should expose Part II in the contents")
    validation.require("HENRI DELPHICE ALAIN" in book_text, "book.html should expose Part II family-entry headings")
    validation.require("MOISE (SMOKEY) ALAIN" in book_text, "book.html should expose Moise Alain as a jump target")
    validation.require("Page Entries" not in book_text, "book.html should not split the contents into generic Page Entries")
    generic_toc_links = re.findall(r'<li class="heading-level-[12]"><a href="[^"]+">((?:Page|Image) [^<]+)</a>', book_html)
    validation.require(not generic_toc_links, f"book.html TOC should not expose generic page/image labels: {generic_toc_links[:8]}")
    part_link_blocks = re.findall(r'<ol class="part-links">(.*?)</ol>', book_html, flags=re.IGNORECASE | re.DOTALL)
    validation.require(all("<span" not in block.lower() for block in part_link_blocks), "book.html TOC heading links should not include per-entry page labels")
    validation.require("scroll-padding-top: 6.5rem" in (build_dir / "assets" / "site.css").read_text(encoding="utf-8"), "site CSS should offset hash navigation for the sticky header")
    expanded_markers = [match.start() for match in re.finditer(r"\nFront Matter\n\d+ headings", book_text)]
    expanded_contents_start = expanded_markers[-1] if expanded_markers else -1
    expanded_contents = book_text[expanded_contents_start:] if expanded_contents_start >= 0 else book_text
    if all(term in expanded_contents for term in ("Preface", "Part I - Alain Family History", "Part II - Alain Family Stories", "LOUIS AND CLARA")):
        validation.require(
            expanded_contents.index("Preface") < expanded_contents.index("Part I - Alain Family History") < expanded_contents.index("Part II - Alain Family Stories") < expanded_contents.index("LOUIS AND CLARA"),
            "book.html contents order should follow front matter, Part I, Part II, then Louis and Clara",
        )


def check_asset_version(build_dir: Path, validation: Validation) -> None:
    book_html = (build_dir / "book.html").read_text(encoding="utf-8")
    search_js = (build_dir / "assets" / "search.js").read_text(encoding="utf-8")
    validation.require(f"assets/search.js?v={ASSET_VERSION}" in book_html, "book.html does not reference the current search.js asset version")
    validation.require(f"search-index.json?v={ASSET_VERSION}" in search_js, "search.js does not fetch the current search-index asset version")


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
        validation.require(len(public_index) == EXPECTED_ENTRY_COUNT, f"Public search index has {len(public_index)} rows, expected {EXPECTED_ENTRY_COUNT}")
        stale_urls = [row.get("url") for row in public_index if isinstance(row, dict) and "pages/" in str(row.get("url") or "")]
        validation.require(not stale_urls, f"Public search index has stale pages/ URLs: {stale_urls[:5]}")
    except Exception as exc:  # noqa: BLE001 - public verification should surface the exact failure.
        validation.error(f"Could not verify public search index: {exc}")


def run_validation(build_dir: Path, public_base: str | None, timeout: float) -> Validation:
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
    check_asset_version(build_dir, validation)
    validation.note(f"Checked {len(parsed)} HTML pages, {len(public_refs)} local references, and {EXPECTED_ENTRY_COUNT} search rows.")

    if public_base:
        check_public_site(build_dir, public_base, public_refs, validation, timeout)
        validation.note(f"Checked public host: {public_base.rstrip('/')}")
    return validation


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Validate the built Alain Lessard family site.")
    parser.add_argument("--build-dir", default=str(DEFAULT_BUILD_DIR), help="Built site directory to validate.")
    parser.add_argument("--public-base", default="", help="Optional public base URL to verify with HTTP requests.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout for public HTTP checks.")
    args = parser.parse_args()

    build_dir = Path(args.build_dir).resolve()
    validation = run_validation(build_dir, args.public_base.strip() or None, args.timeout)

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
