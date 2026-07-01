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

`doc-web` can consume either `output/processed-pages/` or the final searchable
PDF for future website intake. It does not replace this repo's scan cleanup and
PDF construction path, because its maintained output contract is an
HTML/provenance bundle rather than a PDF.

## Supplemental Inputs

Supplemental scans mentioned by the user are not present yet. Add them under
`input/raw scans/` with a named subfolder and update this contract before
processing them.
