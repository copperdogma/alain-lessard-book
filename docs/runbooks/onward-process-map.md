# Runbook: Onward Process Map

## Purpose

Record which parts of the previous Onward projects should shape this repo's
book-scan workflow.

## Source Projects Checked

- `/Users/cam/Documents/Projects/Onward to the Unknown Book Scan`
- `/Users/cam/Documents/Projects/onward-to-the-unknown-processing`
- `/Users/cam/Documents/Projects/onward-to-the-unknown-website`
- `/Users/cam/Documents/Projects/doc-web`

## Reused For This Repo

From `Onward to the Unknown Book Scan/README.md`:

- high-resolution scan cleanup before OCR
- page crop, straighten, and consistent sizing discipline
- image-only PDF before OCR
- OCRmyPDF as the successful OCR layer
- smaller public PDF plus larger archival PDF
- descriptive PDF metadata

This repo implements those steps in `scripts/process_book_scans.py`.

## Phase Boundary

`onward-to-the-unknown-processing` starts from chapter PDFs and focuses on
Markdown, plain text, and audio-ready narrative outputs. In this repo, those
audio scripts now come from the accepted `doc-web` HTML bundle instead of PDF
text extraction so table-heavy/reference material can be skipped cleanly.

`onward-to-the-unknown-website` and `doc-web` define the website intake seam.
They consume the finished PDF or cleaned image directory and emit structural
HTML, manifests, image crops, tables, captions, and provenance sidecars. They
are downstream of the scan-to-PDF phase.

## Current Alain Mapping

1. Raw scans: `input/raw scans/main book/`
2. Clean page master: `output/processed-pages/page-###.jpg`
3. Distribution PDF: `output/pdf/alain-lessard-book-searchable.pdf`
4. Archival PDF: `output/pdf/alain-lessard-book-archival-searchable.pdf`
5. `doc-web` website/audio input:
   `input/doc-web-html/alain-lessard-book-r1/`
6. Public static site: `build/family-site/`
7. Reviewed audio contract: 52 paired Markdown/MP3 tracks under
   `audiobook/script/`, described by `audiobook/manifest.json`
8. Complete local audiobook:
   `audiobook/generated/alain-lessard-complete-audiobook.mp3`
9. Published media paths: `build/family-site/audiobook/`
10. Portable reading edition:
    `output/portable/alain-lessard-family-history.epub`
11. Chaptered audiobook:
    `audiobook/generated/alain-lessard-complete-audiobook.m4b`
12. Portable format contract: `portable/manifest.json`

## Current `doc-web` Treatment

The Alain site now follows the Onward-style `doc-web` treatment more closely:

- the cleaned page images feed `doc-web`;
- `doc-web` cuts out 155 figure crops and places them in the chapter HTML;
- tables remain as `<table>` elements rather than flattened OCR paragraphs;
- captions remain attached to their figures;
- the static site derives 57 meaningful reading/reference sections from the 39
  accepted entries, preserving all 1,737 source blocks while redirecting legacy
  printed-page URLs into their containing section;
- the site wraps those sections with source scan links, a working TOC, search,
  archive downloads, one Read target per applicable track, compact always-visible
  audiobook bars, and direct MP3 downloads;
- audio scripts are generated only for narrative entries, not personal records,
  bibliography, page-level material, or table-heavy reference sections.

## Audiobook Assembly And Publication

Alain follows Onward's manifest-ordered `ffmpeg` concatenation pattern but
keeps the source narration's 44.1 kHz mono profile instead of forcing stereo.
`make build-full-audiobook` inserts the manifest-configured two-second pause
between tracks and writes complete-book ID3 metadata. The generated full MP3
and reviewed source MP3s remain ignored local artifacts.

`make build-family-site RELEASE=1` copies each chapter once to
`audiobook/tracks/`, copies the complete MP3 to its stable public path, and
fails if any of the 53 files is missing or invalid. `make deploy-static` is
guarded by strict bundle validation. After upload, run:

```bash
make validate-family-site RELEASE=1 PUBLIC_BASE=https://alain-lessard.copper-dog.com
```

That public check verifies page/link coverage plus MP3 MIME types, content
lengths, and representative `206` byte-range responses.

## Portable Reader And Listener Editions

The Alain project extends the Onward website/MP3 pattern with two deterministic
derivatives rather than a storefront or podcast feed:

- `scripts/portable_editions.py` consumes the same 57-section reading catalog,
  accepted companion HTML, and referenced images as the site to build EPUB 3;
- `scripts/build_m4b.py` consumes the same 52-track audio manifest as the
  complete MP3 builder to produce an AAC-LC M4B with named chapters;
- `portable/manifest.json` is the only hand-maintained filename, metadata,
  format, and public-path contract for both artifacts;
- `make build-portable-editions RELEASE=1` builds the EPUB/M4B and strict site
  bundle, while `make validate-portable-editions` checks both formats;
- the site publishes literal downloads and short Apple Books, Kindle, Kobo,
  Google Play Books, and audiobook-app instructions without claiming a
  universal one-click install.

Both generated binaries are ignored local artifacts. Deployment still uses
the normal `build/family-site/` boundary. The 2026-07-17 release proved the
EPUB/M4B MIME types, exact lengths, and byte-range behavior publicly. The
deploy helper now requires an actual zero SFTP child exit after a sandboxed DNS
failure exposed the danger of accepting EOF/unknown status as success; the
strict public validator remains the authoritative release proof.

For the complete Onward adaptation sequence—including canonical inventory,
contracts, fixture gates, real reader/app checks, deployment preflight, public
HTTP proof, mobile/desktop smoke, and closeout truth—reuse the numbered
`Reusable Onward Handoff Checklist` in Story 005 and substitute Onward's own
counts, manifests, bundle path, and public host.
