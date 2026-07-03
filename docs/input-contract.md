# Input Contract

The current intake boundary is local and file-based.

## Main Book Scans

- Path: `input/raw scans/main book/`
- Format: JPG
- Count observed on 2026-07-01: 153 files
- Filename pattern: `IMG_20260630_####.jpg`
- First file: `IMG_20260630_0001.jpg`
- Last file: `IMG_20260630_0153.jpg`
- Dimensions:
  - cover: `2550x3371`
  - remaining pages: `2550x3504`

## Scan Shape

- Page 1 is the green cover and is already close to the normalized page canvas.
- Pages after the cover alternate scanner-platen bands at the top and bottom.
- Non-cover scans are encoded as 3-component JPEGs, but their RGB channels are
  identical; they are treated as grayscale source pages.
- The processing pipeline removes only the detected platen band and keeps raw
  scans unchanged.
- Processed page images are normalized to a `2550x3371` white canvas.

## Generated Outputs

- Scan intake JSON report: `output/intake/scan-intake-report.json`
- Scan intake Markdown report: `output/intake/scan-intake-report.md`
- Processed pages: `output/processed-pages/page-###.jpg`
- Processing manifest: `output/processed-pages/manifest.json`
- Contact sheets: `output/processed-pages/contact-sheets/`
- Distribution image-only PDF: `tmp/pdfs/alain-lessard-book-distribution-image-only.pdf`
- Archival image-only PDF: `tmp/pdfs/alain-lessard-book-archival-image-only.pdf`
- Distribution searchable PDF: `output/pdf/alain-lessard-book-searchable.pdf`
- Archival searchable PDF: `output/pdf/alain-lessard-book-archival-searchable.pdf`
- Rendered QA pages: `tmp/pdfs/rendered/`

## PDF Profiles

- Distribution: reader-facing searchable PDF/A, with non-cover pages converted
  to lower-quality grayscale JPEGs before OCR output.
- Archival: preservation-facing searchable PDF, with the color cover retained,
  non-cover pages stored as high-quality grayscale JPEGs, and OCR added with
  minimal PDF rewriting.
- Both profiles carry the same title, author, subject, and keyword metadata.

## `doc-web` Boundary

`doc-web` consumes `output/processed-pages/` for website and audio intake. The
active accepted bundle is:

- Active marker: `input/doc-web-html/active-bundle.json`
- Accepted snapshot: `input/doc-web-html/alain-lessard-book-r1/`
- Manifest: `input/doc-web-html/alain-lessard-book-r1/manifest.json`
- Provenance: `input/doc-web-html/alain-lessard-book-r1/provenance/blocks.jsonl`
- Image crops: `input/doc-web-html/alain-lessard-book-r1/images/`

This does not replace this repo's scan cleanup and PDF construction path,
because `doc-web` emits an HTML/provenance bundle rather than a PDF.

## Supplemental Inputs

The supplemental scans found tucked into the book are now present. The user
confirmed on 2026-07-02 that these are all of the secondary documents for this
edition.

### Alain's Song

- Path: `input/raw scans/Alain's Song/`
- Format: JPG
- Count observed on 2026-07-02: 6 files
- Filename pattern: `IMG_20260702_####.jpg`
- Dimensions: `2550x3260` to `2550x3272`
- DPI: 300
- Intake report: `output/intake/alains-song/scan-intake-report.md`

### Growing Up on the Farm

- Path: `input/raw scans/Growing Up on the Farm/`
- Format: JPG
- Count observed on 2026-07-02: 13 files
- Filename pattern: `IMG_20260702_####.jpg`
- Dimensions: `2550x3268` to `2550x3292`
- DPI: 300
- Intake report: `output/intake/growing-up-on-the-farm/scan-intake-report.md`

Both supplemental scan sets are encoded as RGB JPEGs with identical channels,
so they are processed as grayscale pages. Intake found no scanner-platen bands
requiring crop logic; the supplemental pipeline normalizes the pages to the
same `2550x3371` canvas used by the main book.

## Supplemental Generated Outputs

- Supplemental manifest: `output/supplemental-documents/manifest.json`
- Supplemental processed pages:
  `output/supplemental-documents/<document>/processed-pages/page-###.jpg`
- Supplemental OCR text:
  `output/supplemental-documents/<document>/ocr-text.txt`
- Alain's Song distribution PDF:
  `output/pdf/alains-song-searchable.pdf`
- Alain's Song archival PDF:
  `output/pdf/alains-song-archival-searchable.pdf`
- Growing Up on the Farm distribution PDF:
  `output/pdf/growing-up-on-the-farm-searchable.pdf`
- Growing Up on the Farm archival PDF:
  `output/pdf/growing-up-on-the-farm-archival-searchable.pdf`
