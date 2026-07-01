# Runbook: Scan To PDF

## Purpose

Create a clean, searchable PDF from the main-book scans while preserving raw
inputs and emitting reviewable processing evidence.

For a new book scan project, start with
`docs/runbooks/future-book-scan-intake.md` and only then adapt this runbook's
project-specific constants and crop rules.

## Inputs

- `input/raw scans/main book/*.jpg`

## Outputs

- `output/processed-pages/page-###.jpg`
- `output/processed-pages/manifest.json`
- `tmp/pdfs/alain-lessard-book-distribution-image-only.pdf`
- `tmp/pdfs/alain-lessard-book-archival-image-only.pdf`
- `output/pdf/alain-lessard-book-searchable.pdf`
- `output/pdf/alain-lessard-book-archival-searchable.pdf`
- `tmp/pdfs/rendered/`

## Commands

```bash
make scan-intake-report
make scan-pdf-all
make validate-pdf
make render-pdf-checks
```

## Processing Rules

- Raw scans are never edited.
- The crop detector looks for a strong dark horizontal platen boundary in the
  top or bottom scan region.
- Top candidates inside the first 80 px are ignored because bottom-band pages
  can contain only a page edge there.
- Bottom candidates inside the final 80 px are ignored because top-band pages
  can contain only a page edge there.
- Processed pages are placed on a `2550x3371` white canvas with no stretching.
- The distribution profile converts non-cover pages to grayscale JPEGs at lower
  quality for a reader-facing PDF/A profile. OCRmyPDF may deskew and rotate the
  pages during this compact output pass.
- The archival profile keeps the cover in RGB, stores non-cover pages as
  high-quality grayscale JPEGs because their RGB channels are identical, and
  omits `--force-ocr`; it uses `--output-type pdf` with `--optimize 0` so
  OCRmyPDF minimizes changes to the image-only archival PDF while adding the
  text layer.
- OCR is added by OCRmyPDF after image-only PDF assembly.
- OCRmyPDF writes title, author, subject, and keyword metadata during the OCR
  pass, following the metadata discipline from the Onward scan project.

## Onward Source Process

The first Onward project documented this phase as:

1. scan at high resolution
2. crop/level/straighten/align pages
3. merge cleaned page images into PDF
4. run OCR with OCRmyPDF
5. create both a smaller normal PDF and a larger archival PDF
6. set descriptive PDF metadata

This repo keeps those steps as a reproducible script rather than manual
Photoshop, Preview, and `pdftk` operations. The later Onward processing repo
starts after this phase from chapter PDFs, and `doc-web` starts after this phase
from a PDF or image directory to produce HTML/provenance bundles.

## Relationship To `doc-web`

Use this runbook to build the clean source PDF. Use `doc-web` after that when
the project needs structural HTML, page/chapter manifests, provenance sidecars,
or website intake artifacts.

The Onward project uses `doc-web` as a sibling upstream runtime that consumes an
input PDF or image directory and emits a standard `doc_web_bundle`. That is
useful for the future website phase here, but it is not a replacement for this
repo's platen-crop, page-normalization, image-only PDF, and OCRmyPDF steps.

## Validation

Validation should include:

- `output/processed-pages/manifest.json` has 153 pages
- both searchable PDFs have 153 pages when both profiles have been built
- searchable PDF metadata matches the expected book title, author, subject, and
  keywords
- extracted text exists on OCR-heavy sample pages
- rendered PNG samples show the platen bands removed and page content legible
