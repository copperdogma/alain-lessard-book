---
title: "Main book scan to searchable PDF"
status: "Active"
---

# Main Book Scan To Searchable PDF

## Context

The main book scans are present under `input/raw scans/main book/`. The raw
images alternate scanner-platen bands at the top and bottom after the cover.

## Goal

Produce a cleaned, normalized, searchable PDF of the main book while preserving
raw scans and recording page-level processing decisions.

## Scope

- Process 153 raw JPG scans.
- Remove detected top/bottom scanner-platen bands.
- Normalize processed pages to a common canvas.
- Assemble distribution and archival image-only PDF profiles.
- Run OCR and metadata assignment with profile-specific output settings.
- Keep the distribution PDF compact and reader-facing, and keep the archival
  PDF higher-quality and preservation-facing without storing redundant RGB
  channels for grayscale source pages.
- Render representative pages for visual review.
- Validate page count and OCR text extraction.

## Acceptance

- `output/processed-pages/manifest.json` records 153 processed pages.
- `output/pdf/alain-lessard-book-searchable.pdf` has 153 pages.
- `output/pdf/alain-lessard-book-archival-searchable.pdf` has 153 pages.
- Both PDFs carry expected title, author, subject, and keyword metadata.
- OCR text extraction returns non-empty text for text-heavy sample pages.
- Rendered sample PNGs show no scanner platen band and remain legible.
