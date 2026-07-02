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
7. Audio-script handoff: `audiobook/script/` and `audiobook/manifest.json`

## Current `doc-web` Treatment

The Alain site now follows the Onward-style `doc-web` treatment more closely:

- the cleaned page images feed `doc-web`;
- `doc-web` cuts out 155 figure crops and places them in the chapter HTML;
- tables remain as `<table>` elements rather than flattened OCR paragraphs;
- captions remain attached to their figures;
- the static site wraps the accepted bundle with source scan links, a working
  TOC, search, archive downloads, and audio-script links;
- audio scripts are generated only for narrative entries, not personal records,
  bibliography, page-level material, or table-heavy reference sections.
