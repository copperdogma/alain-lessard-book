#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "output" / "processed-pages"
MANIFEST_PATH = PROCESSED_DIR / "manifest.json"
PDF_DIR = ROOT / "output" / "pdf"
DISTRIBUTION_PDF = PDF_DIR / "alain-lessard-book-searchable.pdf"
ARCHIVAL_PDF = PDF_DIR / "alain-lessard-book-archival-searchable.pdf"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "family-site"
DEFAULT_AUDIO_SCRIPT_DIR = ROOT / "audiobook" / "script"

SITE_TITLE = "Alain Lessard"
SITE_SUBTITLE = "Our First Ancestors and A Compilation of Stories of Their Descendants"
PUBLIC_HOST = "https://alain-lessard.copper-dog.com"
BOOK_YEAR = "1987"


@dataclass(frozen=True)
class Section:
    slug: str
    title: str
    start_page: int
    end_page: int
    group: str
    summary: str
    audio: bool = True

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"


SECTIONS: tuple[Section, ...] = (
    Section(
        "chapter-001",
        "Opening Matter",
        1,
        7,
        "Front matter",
        "Cover, title page, dedication, introduction, acknowledgements, and preface.",
        True,
    ),
    Section(
        "chapter-002",
        "Alain Family History",
        8,
        13,
        "Alain family",
        "The Alain name, coat of arms, Simon Allain, and the family path toward Henri Alain.",
        True,
    ),
    Section(
        "chapter-003",
        "Henri Delphice Alain",
        14,
        20,
        "Alain family stories",
        "Henri and Alma's story, early Saskatchewan homesteading, and family memories.",
        True,
    ),
    Section(
        "chapter-004",
        "Moise \"Smokey\" Alain",
        21,
        23,
        "Alain family stories",
        "Moise Alain's recollections of childhood, work, sport, and family life.",
        True,
    ),
    Section(
        "chapter-005",
        "Louis and Clara Alain",
        24,
        63,
        "Alain family stories",
        "The central Louis and Clara story and the stories of their children and families.",
        True,
    ),
    Section(
        "chapter-006",
        "Yvonne, Rolland, and Alain Family Stories",
        64,
        76,
        "Alain family stories",
        "Yvonne O'Brien, Rolland Alain, their family stories, and related Alain family memories.",
        True,
    ),
    Section(
        "chapter-007",
        "Additional Alain and L'Heureux Stories",
        77,
        81,
        "Additional stories",
        "Moise L'Heureux, Bruno Alain, and supporting family stories.",
        True,
    ),
    Section(
        "chapter-008",
        "Alain, Folley, and L'Heureux Genealogy",
        82,
        87,
        "Genealogy",
        "Genealogical tables and reference pages for connected Alain family lines.",
        False,
    ),
    Section(
        "chapter-009",
        "Lessard Family History",
        88,
        95,
        "Lessard family",
        "The Lessard name, Etienne de Lessart, Edouard Lessard, and the ancestral line.",
        True,
    ),
    Section(
        "chapter-010",
        "Lessard Family Stories",
        96,
        130,
        "Lessard family stories",
        "Joseph Deride Lessard, Gene Lessard, Martin Lessard, Joseph Lessard, and descendant stories.",
        True,
    ),
    Section(
        "chapter-011",
        "Additional Lessard Material",
        131,
        135,
        "Additional stories",
        "Simeon Bernier, Lessard genealogy, and Strasser family material.",
        False,
    ),
    Section(
        "chapter-012",
        "Veillardville",
        136,
        142,
        "Place history",
        "Veillardville's founding, local businesses, community life, and related memories.",
        True,
    ),
    Section(
        "chapter-013",
        "Memories and Personal Records",
        143,
        152,
        "Memories",
        "Reunions, newspaper clippings, personal records, and later family memories.",
        True,
    ),
    Section(
        "chapter-014",
        "Index",
        153,
        153,
        "Reference",
        "The printed index for names and topics in the book.",
        False,
    ),
)


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "section"


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraphs_from_text(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(paragraphs) <= 1:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        paragraphs = []
        buffer: list[str] = []
        for line in lines:
            if len(line) < 34 and buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = [line]
            else:
                buffer.append(line)
        if buffer:
            paragraphs.append(" ".join(buffer).strip())
    return [re.sub(r"\s+", " ", paragraph).strip() for paragraph in paragraphs if paragraph.strip()]


def load_page_texts() -> dict[int, str]:
    require_file(DISTRIBUTION_PDF, "distribution searchable PDF")
    reader = PdfReader(str(DISTRIBUTION_PDF))
    return {
        page_number: normalize_text(page.extract_text() or "")
        for page_number, page in enumerate(reader.pages, start=1)
    }


def load_manifest() -> dict:
    require_file(MANIFEST_PATH, "processing manifest")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def page_image_path(page_number: int) -> Path:
    return PROCESSED_DIR / f"page-{page_number:03d}.jpg"


def section_for_page(page_number: int) -> Section:
    for section in SECTIONS:
        if section.start_page <= page_number <= section.end_page:
            return section
    return SECTIONS[-1]


def write_site_assets(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "site.css").write_text(SITE_CSS, encoding="utf-8")
    (assets_dir / "search.js").write_text(SEARCH_JS, encoding="utf-8")


def write_web_images(output_dir: Path) -> None:
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    for page_number in range(1, 154):
        source = page_image_path(page_number)
        require_file(source, f"processed page {page_number}")
        destination = images_dir / f"page-{page_number:03d}.jpg"
        with Image.open(source) as image:
            image = image.convert("RGB")
            max_width = 1280
            if image.width > max_width:
                ratio = max_width / image.width
                image = image.resize((max_width, round(image.height * ratio)), Image.Resampling.LANCZOS)
            image.save(destination, quality=84, optimize=True, progressive=True)


def copy_downloads(output_dir: Path) -> None:
    downloads_dir = output_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    for source in (DISTRIBUTION_PDF, ARCHIVAL_PDF):
        if source.exists():
            shutil.copy2(source, downloads_dir / source.name)


def page_title(page_number: int, text: str) -> str:
    if page_number == 1:
        return "Cover"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:8]:
        letters = [char for char in line if char.isalpha()]
        if len(line) >= 5 and (not letters or sum(char.isupper() for char in letters) >= max(3, len(letters) * 0.6)):
            return line[:80].title()
    if lines:
        return lines[0][:80]
    return f"Page {page_number}"


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
  <link rel="stylesheet" href="assets/site.css">
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
    <p>Digitized from the 1987 family history book. Raw scans, processing scripts, and provenance notes are maintained in the project archive.</p>
  </footer>
</body>
</html>
"""


def section_cards() -> str:
    return "\n".join(
        f"""<article class="section-card">
  <p class="section-card-kicker">{escape(section.group)} · Pages {section.start_page}-{section.end_page}</p>
  <h3><a href="{section.filename}">{escape(section.title)}</a></h3>
  <p>{escape(section.summary)}</p>
</article>"""
        for section in SECTIONS
    )


def render_index(page_texts: dict[int, str]) -> str:
    body = f"""
    <section class="hero">
      <div class="hero-copy">
        <h1>{escape(SITE_TITLE)}</h1>
        <p>{escape(SITE_SUBTITLE)}</p>
        <div class="hero-actions">
          <a class="button primary" href="book.html">Read the book</a>
          <a class="button" href="downloads/{DISTRIBUTION_PDF.name}">Download PDF</a>
        </div>
      </div>
      <figure class="hero-cover">
        <img src="images/page-001.jpg" alt="Green cover of the Alain Lessard book">
      </figure>
    </section>

    <section class="intro-grid">
      <article>
        <h2>A family archive edition</h2>
        <p>This site brings together the scanned book, cleaned page images, OCR text, source PDFs, and audio-script handoff in one place. The book remains the center; companion scans and later audio can connect to the same source lineage.</p>
      </article>
      <article>
        <h2>What is ready now</h2>
        <ul>
          <li>Reader-facing and archival PDFs.</li>
          <li>Page-by-page web reading with scan images and OCR text.</li>
          <li>Search data across all scanned pages.</li>
          <li>Onward-style audio scripts for narrative sections, not tables.</li>
        </ul>
      </article>
      <article>
        <h2>Source honesty</h2>
        <p>Secondary materials can be added when they are scanned. Missing companion items are kept explicit rather than silently represented as complete.</p>
      </article>
    </section>

    <section class="section-list">
      <div class="section-heading">
        <h2>Book Sections</h2>
        <p>Section ranges are based on the printed table of contents and the OCR page map. Every section links back to individual scan pages.</p>
      </div>
      <div class="cards">{section_cards()}</div>
    </section>
"""
    return html_page("Home", body, "Home")


def render_book(page_texts: dict[int, str]) -> str:
    toc = "\n".join(
        f'<li><a href="{section.filename}">{escape(section.title)}</a><span>Pages {section.start_page}-{section.end_page}</span></li>'
        for section in SECTIONS
    )
    page_list = "\n".join(
        f"""<article class="page-row" data-page="{page_number}" data-section="{escape(section_for_page(page_number).title)}">
  <a href="pages/page-{page_number:03d}.html"><img src="images/page-{page_number:03d}.jpg" alt="Scanned page {page_number}" loading="lazy"></a>
  <div>
    <p class="eyebrow">Page {page_number:03d}</p>
    <h3><a href="pages/page-{page_number:03d}.html">{escape(page_title(page_number, page_texts.get(page_number, "")))}</a></h3>
    <p>{escape((page_texts.get(page_number, "")[:260] or "Cover image").replace(chr(10), " "))}</p>
  </div>
</article>"""
        for page_number in range(1, 154)
    )
    body = f"""
    <section class="page-title">
      <h1>Read the Book</h1>
      <p>Browse by section or search OCR text across the scanned pages.</p>
    </section>
    <section class="book-tools">
      <label class="search-label" for="site-search">Search the OCR text</label>
      <input id="site-search" class="search-input" type="search" placeholder="Search names, places, stories">
      <div id="search-results" class="search-results" aria-live="polite"></div>
    </section>
    <section class="book-layout">
      <aside class="toc-panel">
        <h2>Sections</h2>
        <ol>{toc}</ol>
      </aside>
      <div class="page-list">{page_list}</div>
    </section>
    <script src="assets/search.js"></script>
"""
    return html_page("Read", body, "Read")


def render_section(section: Section, page_texts: dict[int, str]) -> str:
    page_links = "\n".join(
        f'<a class="page-pill" href="pages/page-{page_number:03d}.html">Page {page_number}</a>'
        for page_number in range(section.start_page, section.end_page + 1)
    )
    pages = "\n".join(
        f"""<article class="reading-page">
  <figure><img src="images/page-{page_number:03d}.jpg" alt="Scanned page {page_number}" loading="lazy"></figure>
  <div class="ocr-text">
    <p class="eyebrow">Page {page_number:03d}</p>
    {render_text_paragraphs(page_texts.get(page_number, ""))}
  </div>
</article>"""
        for page_number in range(section.start_page, section.end_page + 1)
    )
    audio_note = (
        '<p class="callout">This section is included in the narrative audio-script queue.</p>'
        if section.audio
        else '<p class="callout">This section is kept as readable/searchable reference material rather than narrated audio.</p>'
    )
    body = f"""
    <section class="page-title">
      <p class="eyebrow">{escape(section.group)} · Pages {section.start_page}-{section.end_page}</p>
      <h1>{escape(section.title)}</h1>
      <p>{escape(section.summary)}</p>
      {audio_note}
      <div class="page-pills">{page_links}</div>
    </section>
    <section class="reading-stack">{pages}</section>
"""
    return html_page(section.title, body, "Read")


def render_text_paragraphs(text: str) -> str:
    paragraphs = paragraphs_from_text(text)
    if not paragraphs:
        return "<p>No OCR text was extracted for this page.</p>"
    rendered: list[str] = []
    for index, paragraph in enumerate(paragraphs[:24]):
        if index == 0 and len(paragraph) < 90:
            rendered.append(f"<h2>{escape(paragraph)}</h2>")
        else:
            rendered.append(f"<p>{escape(paragraph)}</p>")
    if len(paragraphs) > 24:
        rendered.append("<p><em>OCR text continues on the scanned page image.</em></p>")
    return "\n".join(rendered)


def render_page(page_number: int, page_texts: dict[int, str]) -> str:
    section = section_for_page(page_number)
    previous_link = f'pages/page-{page_number - 1:03d}.html' if page_number > 1 else None
    next_link = f'pages/page-{page_number + 1:03d}.html' if page_number < 153 else None
    nav = "\n".join(
        [
            f'<a class="button" href="../{previous_link}">Previous page</a>' if previous_link else "",
            f'<a class="button" href="../{section.filename}">{escape(section.title)}</a>',
            f'<a class="button" href="../{next_link}">Next page</a>' if next_link else "",
        ]
    )
    body = f"""
    <section class="page-title">
      <p class="eyebrow">{escape(section.title)}</p>
      <h1>Page {page_number}</h1>
      <div class="hero-actions">{nav}</div>
    </section>
    <section class="single-page">
      <figure><img src="../images/page-{page_number:03d}.jpg" alt="Scanned page {page_number}"></figure>
      <article class="ocr-text">
        <h2>OCR Text</h2>
        {render_text_paragraphs(page_texts.get(page_number, ""))}
      </article>
    </section>
"""
    html = html_page(f"Page {page_number}", body, "Read")
    return html.replace('href="assets/site.css"', 'href="../assets/site.css"').replace('href="index.html"', 'href="../index.html"').replace('href="book.html"', 'href="../book.html"').replace('href="audiobook.html"', 'href="../audiobook.html"').replace('href="archive.html"', 'href="../archive.html"')


def render_archive(manifest: dict) -> str:
    pdf_cards = []
    for label, pdf in (("Reader PDF", DISTRIBUTION_PDF), ("Archival PDF", ARCHIVAL_PDF)):
        if pdf.exists():
            size_mb = pdf.stat().st_size / 1024 / 1024
            pdf_cards.append(
                f"""<article class="section-card">
  <p class="section-card-kicker">{label}</p>
  <h3><a href="downloads/{pdf.name}">{pdf.name}</a></h3>
  <p>{size_mb:.1f} MiB. Generated from the cleaned page-image pipeline.</p>
</article>"""
            )
    body = f"""
    <section class="page-title">
      <h1>Archive Sources</h1>
      <p>Download the generated PDFs and inspect the source-processing contract.</p>
    </section>
    <section class="cards">{''.join(pdf_cards)}</section>
    <section class="intro-grid">
      <article>
        <h2>Raw scans</h2>
        <p>The raw main-book scan set contains {manifest.get('page_count', 153)} files and remains unchanged under the project input folder.</p>
      </article>
      <article>
        <h2>Processing manifest</h2>
        <p>The local processing manifest records crop decisions, page dimensions, and output paths for each scan.</p>
      </article>
      <article>
        <h2>Secondary materials</h2>
        <p>Companion scans are not yet present in this repo. They should be added as a named raw-scan folder before PDF or website intake.</p>
      </article>
    </section>
"""
    return html_page("Archive", body, "Archive")


def audio_script_files() -> list[Path]:
    if not DEFAULT_AUDIO_SCRIPT_DIR.exists():
        return []
    return sorted(DEFAULT_AUDIO_SCRIPT_DIR.glob("*.md"))


def render_audiobook() -> str:
    scripts = audio_script_files()
    if scripts:
        script_cards = "\n".join(
            f"""<article class="section-card">
  <p class="section-card-kicker">Audio script</p>
  <h3><a href="audiobook/script/{path.name}">{escape(script_title(path))}</a></h3>
  <p>Prepared for narration from OCR text and reviewed section boundaries.</p>
</article>"""
            for path in scripts
        )
    else:
        script_cards = '<p class="callout">Audio scripts have not been generated yet. Run <code>make build-audiobook-script</code>.</p>'
    body = f"""
    <section class="page-title">
      <h1>Audio Companion</h1>
      <p>The audio lane follows the Onward model: narrative sections become audiobook material, while genealogy tables, indexes, and dense lists stay readable and searchable.</p>
    </section>
    <section class="intro-grid">
      <article>
        <h2>What belongs in audio</h2>
        <p>Stories, introductions, poems, recollections, and place histories are prepared as narration scripts.</p>
      </article>
      <article>
        <h2>What stays visual</h2>
        <p>Tables, genealogy lists, indexes, and reference structures remain on the site and in the PDFs where they can be searched and scanned.</p>
      </article>
    </section>
    <section class="cards">{script_cards}</section>
"""
    return html_page("Audio Companion", body, "Audio")


def script_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8").splitlines()
    for line in text:
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def write_search_index(output_dir: Path, page_texts: dict[int, str]) -> None:
    rows = []
    for page_number, text in page_texts.items():
        section = section_for_page(page_number)
        rows.append(
            {
                "page": page_number,
                "title": page_title(page_number, text),
                "section": section.title,
                "url": f"pages/page-{page_number:03d}.html",
                "text": re.sub(r"\s+", " ", text).strip(),
            }
        )
    (output_dir / "search-index.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def copy_audio_scripts(output_dir: Path) -> None:
    scripts = audio_script_files()
    if not scripts:
        return
    destination = output_dir / "audiobook" / "script"
    destination.mkdir(parents=True, exist_ok=True)
    for script in scripts:
        shutil.copy2(script, destination / script.name)


def build(output_dir: Path) -> None:
    manifest = load_manifest()
    page_texts = load_page_texts()
    clean_dir(output_dir)
    write_site_assets(output_dir)
    write_web_images(output_dir)
    copy_downloads(output_dir)
    write_search_index(output_dir, page_texts)
    copy_audio_scripts(output_dir)

    (output_dir / "index.html").write_text(render_index(page_texts), encoding="utf-8")
    (output_dir / "book.html").write_text(render_book(page_texts), encoding="utf-8")
    (output_dir / "archive.html").write_text(render_archive(manifest), encoding="utf-8")
    (output_dir / "audiobook.html").write_text(render_audiobook(), encoding="utf-8")
    for section in SECTIONS:
        (output_dir / section.filename).write_text(render_section(section, page_texts), encoding="utf-8")
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for page_number in range(1, 154):
        (pages_dir / f"page-{page_number:03d}.html").write_text(render_page(page_number, page_texts), encoding="utf-8")
    (output_dir / "_internal").mkdir(parents=True, exist_ok=True)
    (output_dir / "_internal" / "build-summary.json").write_text(
        json.dumps(
            {
                "title": SITE_TITLE,
                "page_count": len(page_texts),
                "sections": [section.__dict__ for section in SECTIONS],
                "public_host": PUBLIC_HOST,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"built family site: {output_dir}")


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Build the Alain Lessard static family archive site.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    build(Path(args.output).resolve())
    return 0


SITE_CSS = r"""
:root {
  --bg: #f7f2e9;
  --paper: #fffdf8;
  --paper-soft: #f1e6d8;
  --ink: #241b13;
  --muted: #6c5d4d;
  --border: #dac9b4;
  --accent: #315d49;
  --accent-strong: #244534;
  --accent-soft: #dfe9df;
  --rose: #8b4f48;
  --shadow: 0 18px 50px rgba(61, 45, 27, 0.12);
  --serif: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
  --sans: "Avenir Next", "Segoe UI", Helvetica, Arial, sans-serif;
}
* { box-sizing: border-box; }
html { background: var(--bg); color: var(--ink); font-size: 18px; }
body {
  margin: 0;
  font-family: var(--serif);
  line-height: 1.75;
  background: linear-gradient(180deg, #fbf8f2 0%, var(--bg) 34rem);
}
a { color: inherit; text-underline-offset: .18em; }
img { display: block; max-width: 100%; height: auto; }
.site-header, main, .site-footer {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
}
.site-header {
  min-height: 84px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0;
}
.brand {
  display: inline-flex;
  gap: .75rem;
  align-items: center;
  text-decoration: none;
  font-family: var(--sans);
}
.brand-mark {
  width: 3rem;
  height: 3rem;
  display: inline-grid;
  place-items: center;
  background: var(--accent);
  color: white;
  border-radius: 50%;
  font-weight: 800;
  letter-spacing: .04em;
}
.brand strong { display: block; font-size: 1.1rem; line-height: 1.1; }
.brand small { display: block; color: var(--muted); max-width: 24rem; line-height: 1.25; }
.site-nav { display: flex; flex-wrap: wrap; gap: .5rem; justify-content: flex-end; }
.nav-link, .button, .page-pill {
  min-height: 2.55rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: .55rem .9rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  font-family: var(--sans);
  font-size: .92rem;
  font-weight: 700;
  text-decoration: none;
  background: rgba(255,255,255,.66);
}
.nav-link.is-active, .button.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.hero {
  min-height: calc(100vh - 112px);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 430px);
  align-items: center;
  gap: clamp(2rem, 5vw, 5rem);
  padding: 1rem 0 4rem;
}
.hero h1, .page-title h1 {
  margin: 0;
  font-family: var(--sans);
  font-size: clamp(3rem, 9vw, 7.5rem);
  line-height: .94;
  letter-spacing: 0;
}
.hero p {
  max-width: 42rem;
  color: var(--muted);
  font-size: clamp(1.15rem, 2vw, 1.55rem);
}
.hero-actions { display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; margin-top: 1.4rem; }
.hero-cover {
  margin: 0;
  padding: .75rem;
  background: var(--paper);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.hero-cover img { aspect-ratio: 2550 / 3371; object-fit: cover; }
.intro-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 2rem 0 4rem;
}
.intro-grid article, .section-card, .toc-panel, .book-tools, .ocr-text {
  background: var(--paper);
  border: 1px solid var(--border);
  box-shadow: 0 10px 28px rgba(61, 45, 27, 0.06);
}
.intro-grid article, .section-card, .toc-panel, .book-tools { padding: 1.2rem; }
h2, h3 { font-family: var(--sans); line-height: 1.18; }
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  margin-bottom: 1rem;
}
.section-heading h2, .page-title h1 { margin-bottom: .4rem; }
.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}
.section-card h3 { margin: .1rem 0 .45rem; font-size: 1.2rem; }
.section-card p { margin: .35rem 0 0; }
.section-card-kicker, .eyebrow {
  font-family: var(--sans);
  text-transform: uppercase;
  letter-spacing: .08em;
  font-size: .72rem;
  font-weight: 800;
  color: var(--rose);
}
.page-title {
  padding: 3rem 0 1.5rem;
  max-width: 820px;
}
.page-title p { color: var(--muted); font-size: 1.1rem; }
.book-tools { margin-bottom: 1.25rem; }
.search-label { display: block; font-family: var(--sans); font-weight: 800; margin-bottom: .45rem; }
.search-input {
  width: 100%;
  min-height: 3rem;
  border: 1px solid var(--border);
  border-radius: .35rem;
  padding: .7rem .9rem;
  font: 1rem var(--sans);
}
.search-results { margin-top: 1rem; display: grid; gap: .75rem; }
.search-hit {
  display: block;
  padding: .85rem;
  background: var(--paper-soft);
  border: 1px solid var(--border);
  text-decoration: none;
}
.book-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}
.toc-panel { position: sticky; top: 1rem; }
.toc-panel ol { padding-left: 1.1rem; margin: 0; }
.toc-panel li { margin: .7rem 0; }
.toc-panel span { display: block; color: var(--muted); font-size: .86rem; font-family: var(--sans); }
.page-list { display: grid; gap: 1rem; }
.page-row {
  display: grid;
  grid-template-columns: 130px minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
  padding: .85rem;
  background: rgba(255,255,255,.62);
  border: 1px solid var(--border);
}
.page-row img { border: 1px solid var(--border); background: white; }
.reading-stack { display: grid; gap: 2rem; }
.reading-page, .single-page {
  display: grid;
  grid-template-columns: minmax(280px, 43%) minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
}
.reading-page figure, .single-page figure {
  margin: 0;
  background: white;
  border: 1px solid var(--border);
  padding: .5rem;
  position: sticky;
  top: 1rem;
}
.ocr-text { padding: 1.25rem; }
.ocr-text h2 { margin-top: 0; }
.page-pills { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
.callout {
  padding: .85rem 1rem;
  border-left: .25rem solid var(--accent);
  background: var(--accent-soft);
  color: var(--accent-strong) !important;
}
.site-footer {
  margin-top: 4rem;
  padding: 2rem 0;
  border-top: 1px solid var(--border);
  color: var(--muted);
}
@media (max-width: 860px) {
  .site-header { align-items: flex-start; flex-direction: column; }
  .site-nav { justify-content: flex-start; }
  .hero, .intro-grid, .cards, .book-layout, .reading-page, .single-page {
    grid-template-columns: 1fr;
  }
  .hero { min-height: auto; padding-top: 2rem; }
  .toc-panel, .reading-page figure, .single-page figure { position: static; }
  .page-row { grid-template-columns: 92px minmax(0, 1fr); }
}
"""


SEARCH_JS = r"""
(async () => {
  const input = document.querySelector("#site-search");
  const results = document.querySelector("#search-results");
  if (!input || !results) return;
  const response = await fetch("search-index.json");
  const rows = await response.json();

  function excerpt(text, term) {
    const lower = text.toLowerCase();
    const index = lower.indexOf(term.toLowerCase());
    if (index === -1) return text.slice(0, 220);
    const start = Math.max(0, index - 90);
    return text.slice(start, start + 260);
  }

  input.addEventListener("input", () => {
    const query = input.value.trim();
    results.innerHTML = "";
    if (query.length < 2) return;
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    const hits = rows.filter(row => terms.every(term =>
      row.text.toLowerCase().includes(term) ||
      row.title.toLowerCase().includes(term) ||
      row.section.toLowerCase().includes(term)
    )).slice(0, 18);
    if (!hits.length) {
      results.innerHTML = '<p class="callout">No matches found.</p>';
      return;
    }
    for (const hit of hits) {
      const a = document.createElement("a");
      a.className = "search-hit";
      a.href = hit.url;
      a.innerHTML = `<strong>${hit.title}</strong><br><small>${hit.section} · Page ${hit.page}</small><p>${excerpt(hit.text, query)}</p>`;
      results.appendChild(a);
    }
  });
})();
"""


if __name__ == "__main__":
    raise SystemExit(cli_main())
