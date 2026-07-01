# Runbook: Future Book Scan Intake

## Purpose

Use this runbook when a new book or booklet has been scanned and needs the same
journey as this repo: raw scans to cleaned page masters, searchable PDFs, and
eventual website intake.

The goal is not to reuse this exact book's constants blindly. The goal is to
reuse the evidence discipline, processing stages, validation checks, and profile
decisions that emerged here.

## Starting Point

Put the new raw scans in a dedicated folder and leave them unchanged. Preferred
layout:

```bash
input/raw scans/<book-or-item-name>/
```

Then run the reusable scan inspector:

```bash
make scan-intake-report SCAN_INPUT="input/raw scans/<book-or-item-name>"
```

Outputs:

- `output/intake/scan-intake-report.json`
- `output/intake/scan-intake-report.md`

Read the report before touching crop or OCR logic.

## Intake Questions To Answer First

Record these in `docs/input-contract.md` or a new project-specific intake doc:

- How many scans are present?
- Are filenames already in page order?
- Which page, if any, is a color cover?
- Are interior pages true grayscale, or RGB files with identical channels?
- Are there mixed color pages inside the book?
- What dimensions and DPI did the scanner emit?
- Is the page upright, rotated, or alternating orientation?
- Does the scanner platen appear at the top, bottom, left, or right?
- Does the platen position alternate predictably?
- Are there supplemental scans that are not part of the main book?

Do not infer these from file names alone. Use the intake report, image metadata,
contact sheets, and rendered samples.

## Project Setup Pattern

For a new project, start by copying or adapting these surfaces:

- `AGENTS.md` for operating rules and raw-scan preservation.
- `README.md` for current commands and artifact paths.
- `Makefile` for repeatable pipeline commands.
- `scripts/inspect_scan_set.py` for scan-set evidence.
- `scripts/process_book_scans.py` as the starting implementation, then rename
  and edit constants for the new book.
- `docs/input-contract.md` for the local source contract.
- `docs/runbooks/scan-to-pdf.md` for the project-specific processing rules.
- `docs/runbooks/doc-web-import.md` for the later website boundary.
- `docs/evals/registry.yaml` and `docs/evals/attempt-template.md` for repeatable
  validation records if the project uses methodology docs.

If the repo uses the methodology package, run `/setup-methodology` first, then
adapt the source inventory, story, and eval entries to the new book.

## Processing Pipeline

The expected local pipeline is:

1. Preserve raw scans under `input/`.
2. Run `scripts/inspect_scan_set.py` and write down the intake contract.
3. Crop scanner-platen bands or page-edge artifacts into processed page masters.
4. Normalize processed pages to one canvas size without stretching content.
5. Generate contact sheets for fast human review.
6. Assemble image-only PDFs before OCR.
7. Build a reader-facing distribution PDF.
8. Build a preservation-facing archival PDF.
9. Add OCR text with OCRmyPDF.
10. Validate page count, metadata, text extraction, image streams, and rendered
    sample pages.

Keep generated artifacts under `output/` or `tmp/`. Never rewrite raw scans.

## Crop And Normalization Rules

Do not assume the Alain Lessard crop constants are correct for another book.
Use them as a starting point only.

For this project, the successful pattern was:

- Detect a strong dark horizontal platen boundary in the top or bottom scan
  region.
- Ignore the first and last small bands where a normal page edge can look like a
  platen boundary.
- Apply a residual trim after the primary crop.
- Normalize every page to a fixed canvas with a white background.
- Render contact sheets and sample PDF pages before accepting the crop.

For a new scan set, first inspect:

- whether the platen is horizontal or vertical
- whether crop bands are top/bottom, left/right, or mixed
- whether the cover has different dimensions
- whether blank pages, foldouts, or inserted documents need exceptions
- whether automatic deskew improves or damages the page image

Document exceptions in the manifest instead of handling them silently.

## Color Policy

Use color only where the source contains real color.

Lessons from this project:

- The cover scan was real color and should stay RGB.
- Interior pages looked grayscale and had identical RGB channels even when the
  JPEG file reported three components.
- Storing those interior pages as RGB added size without adding information.
- The archival profile should preserve quality, not redundant color channels.

Default policy for future books:

- Keep covers and genuinely color pages as RGB.
- Store grayscale pages as single-channel grayscale JPEGs.
- If RGB channels are identical, treat the page as grayscale content.
- If interior pages have non-identical RGB channels, inspect them visually before
  deciding whether they are real color, scanner noise, or staining that should
  be preserved.

Use `pdfimages -list <pdf>` after PDF construction to verify that the embedded
image streams match the intended color policy.

## PDF Profiles

Maintain two output profiles unless the user explicitly wants only one:

### Distribution

Purpose: reader-facing, smaller, broadly compatible.

Recommended defaults:

- non-cover grayscale pages at lower JPEG quality
- PDF/A output with OCRmyPDF, usually `--output-type pdfa`
- OCRmyPDF `--force-ocr` is acceptable when the goal is compact output
- `--deskew` and `--rotate-pages` can be used when they improve readability

### Archival

Purpose: preservation-facing, larger, minimal image rewriting.

Recommended defaults:

- color only for pages with real color
- high-quality grayscale for grayscale pages
- image-only PDF assembled before OCR
- OCRmyPDF without `--force-ocr`
- `--output-type pdf`
- `--optimize 0`

Important: `--force-ocr` can cause OCRmyPDF to rewrite image streams even when
`--optimize 0` is set. Test a two-page sample if file sizes or `pdfimages`
output look suspicious.

## OCR And Metadata

OCRmyPDF is the successful OCR layer for this workflow.

Set metadata during the OCR pass:

- title
- author
- subject
- keywords

Expect Tesseract warnings on some pages. Do not treat warnings as success or
failure by themselves. Validate by extracting text from representative pages and
visually reviewing rendered samples.

## Validation Gate

Before calling a PDF done, run checks equivalent to:

```bash
make validate-pdf
make render-pdf-checks
pdfinfo output/pdf/<book>-searchable.pdf
pdfinfo output/pdf/<book>-archival-searchable.pdf
pdfimages -list output/pdf/<book>-archival-searchable.pdf | sed -n '1,20p'
```

The validation should prove:

- raw page count matches processed page count
- final PDFs have the expected page count
- title, author, subject, and keywords are present
- OCR text extracts from text-heavy pages
- rendered samples are upright, legible, and free of platen bands
- the distribution PDF is meaningfully smaller than archival
- the archival PDF preserves the intended image streams

For high-risk pages, render and inspect specific page numbers with `pdftoppm`.

## Relationship To `doc-web`

`doc-web` starts after a clean source PDF or cleaned page-image directory exists.
Do not use `doc-web` as the primary PDF construction tool for this scan phase.

Use local scripts for:

- crop cleanup
- page normalization
- image-only PDF assembly
- OCR-backed PDF creation
- PDF validation

Use `doc-web` later for:

- HTML or website intake
- page and chapter manifests
- provenance sidecars
- image crop extraction
- search/readability bundles

## Handoff For The Next Agent

When handing off a new book scan project, leave these durable artifacts:

- an intake report under `output/intake/`
- an updated input contract
- a project-specific scan-to-PDF runbook
- a deterministic processing script
- contact sheets
- image-only PDFs
- distribution and archival searchable PDFs
- rendered PDF samples
- validation command output summarized in the final response or eval attempt

The future agent should be able to start from the runbook and commands, rerun
the pipeline, and understand why each profile exists.
