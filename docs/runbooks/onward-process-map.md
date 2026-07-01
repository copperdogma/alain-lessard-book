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

## Not Reused For This Phase

`onward-to-the-unknown-processing` starts from chapter PDFs and focuses on
Markdown, plain text, and audio-ready narrative outputs. It belongs after the
searchable PDF exists.

`onward-to-the-unknown-website` and `doc-web` define the website intake seam.
They consume the finished PDF or cleaned image directory and emit structural
HTML, manifests, image crops, and provenance sidecars. They are downstream of
the scan-to-PDF phase.

## Current Alain Mapping

1. Raw scans: `input/raw scans/main book/`
2. Clean page master: `output/processed-pages/page-###.jpg`
3. Distribution PDF: `output/pdf/alain-lessard-book-searchable.pdf`
4. Archival PDF: `output/pdf/alain-lessard-book-archival-searchable.pdf`
5. Future website input: distribution PDF, archival PDF, or clean page master
   depending on the chosen `doc-web` recipe.
