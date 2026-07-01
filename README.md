# Alain Lessard Book

This repo owns the scan processing, OCR, PDF construction, and future website
work for the *Alain Lessard* family book project.

The current source of truth is the local raw scan set:

- `input/raw scans/main book/`
- 153 JPG scans from the main book
- page 1 is the green cover; the remaining pages alternate scanner-platen
  bands at the top and bottom

## Current Commands

```bash
make scan-intake-report
make scan-pdf-all
make build-audiobook-script
make build-family-site
make render-pdf-checks
make methodology-compile
make methodology-check
```

`make scan-intake-report` inspects a raw scan folder and writes reusable intake
evidence under `output/intake/`. For another scan set, pass `SCAN_INPUT`:

```bash
make scan-intake-report SCAN_INPUT="input/raw scans/<book-or-item-name>"
```

`make scan-pdf-all` runs the deterministic local pipeline:

1. crop scanner-platen bands from raw scans
2. normalize processed page images to one canvas size
3. assemble an image-only PDF
4. create both distribution and archival image-only PDF profiles
5. OCR with profile-specific settings and write book metadata with OCRmyPDF

`make build-audiobook-script` generates Onward-style narration scripts for
story/prose sections while leaving genealogy tables, indexes, and dense lists
as readable/searchable material.

`make build-family-site` builds the static website bundle under
`build/family-site/`, including page images, OCR reading pages, search data, PDF
downloads, archive notes, and audio-script links.

`make deploy-static` uploads `build/family-site/` to DreamHost using the
gitignored local `.env`. The intended public host is
`alain-lessard.copper-dog.com`. Install the deploy helper dependency first:

```bash
python -m pip install -r requirements-deploy.txt
```

The 2026-07-01 SFTP upload completed to DreamHost, and the Cloudflare DNS
record now exists. Public verification is still blocked because DreamHost
returns its missing-site page until the hosted subdomain is mapped to the
uploaded directory; see `docs/infrastructure.md`.

Final PDF outputs:

- `output/pdf/alain-lessard-book-searchable.pdf` - reader-facing distribution PDF/A copy
- `output/pdf/alain-lessard-book-archival-searchable.pdf` - higher-quality archival copy with the color cover preserved and non-cover pages stored as high-quality grayscale

Pipeline manifests and review images:

- `output/intake/scan-intake-report.json`
- `output/intake/scan-intake-report.md`
- `output/processed-pages/manifest.json`
- `output/processed-pages/contact-sheets/`
- `tmp/pdfs/rendered/`
- `audiobook/script/`
- `build/family-site/`

## `doc-web` Boundary

`doc-web` is the right downstream runtime for turning this book into a
website-ready HTML/provenance bundle. It should consume the cleaned image set or
the final searchable PDF after this repo has produced it.

For the PDF deliverable itself, keep using this repo's local scan pipeline:
`doc-web` emits HTML bundles and provenance manifests, not the polished
image-backed searchable PDF.

## Onward Process Mapping

The first-pass scan/PDF workflow is anchored to the older local Onward scan
project, especially its book-scan README notes: clean and straighten scans,
merge images into PDF, run OCRmyPDF, keep a smaller public PDF and a larger
archival PDF, and set useful PDF metadata. This repo keeps that process in code
instead of Photoshop/Preview/manual metadata edits.

## Reusing This Pipeline

For a future book, start with `docs/runbooks/future-book-scan-intake.md` and the
checklist template at `docs/templates/book-scan-intake-checklist.md`. The first
step is always to preserve raw scans, run `make scan-intake-report`, and record
the input contract before adapting crop, color, OCR, or PDF profile settings.

## Methodology

This repo is bootstrapped from the same reusable methodology package used by
the Onward project. Planning starts from:

- `docs/ideal.md`
- `docs/spec.md`
- `docs/methodology/state.yaml`
- `docs/methodology/graph.json`
- `docs/stories.md`

The completed first story is the main-book scan cleanup and searchable PDF. The
current open gate is DreamHost hosted-subdomain verification for the uploaded
static site, followed by supplemental scan intake and reviewed audio-file
generation.
