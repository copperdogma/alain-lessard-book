# Runbook: `doc-web` Import

This repo should use `doc-web` after a clean source PDF or cleaned page-image
set exists.

## Current Decision

- Use local repo scripts for scan cleanup and searchable PDF construction.
- Use `doc-web` for structural HTML, page/chapter manifests, image crops,
  table preservation, caption placement, and provenance sidecars that feed the
  website and audio-script handoff.
- Do not treat `doc-web` as the source of the final PDF. Its maintained export
  path is `doc_web_bundle_manifest_v1` plus HTML/provenance files.

## Active Input

- Cleaned images: `output/processed-pages/`
- Recipe: `configs/doc-web/recipe-alain-images-html-mvp.yaml`
- Runtime config: `doc-web-runtime.json`
- Sibling runtime checkout: `/Users/cam/Documents/Projects/doc-web`
- Accepted bundle: `input/doc-web-html/alain-lessard-book-r1/`
- Active marker: `input/doc-web-html/active-bundle.json`

## Commands

```bash
make doc-web-contract
make doc-web-run DOC_WEB_RUN_ID=alain-lessard-book-r1
make doc-web-import-run DOC_WEB_RUN_ID=alain-lessard-book-r1 DOC_WEB_SNAPSHOT_ID=alain-lessard-book-r1
make doc-web-validate-active DOC_WEB_SNAPSHOT_ID=alain-lessard-book-r1
make build-family-site
```

The imported bundle should validate with:

- `entry_count`: 39
- `provenance_row_count`: 1738
- `image_count`: 155
- reading order: 21 page entries followed by 18 chapter entries

The family-site build wraps each imported `doc-web` entry in the repo's public
site chrome while preserving the article HTML, figure crops, captions, table
HTML, and source page metadata.

## Companion Documents

The two supplemental documents found inside the book use a separate accepted
`doc-web` bundle root so the main book's active bundle marker stays stable:

```bash
make companion-doc-web
make validate-companion-doc-web
make build-family-site
```

The accepted companion bundles live under
`input/doc-web-html/companion-documents/`. The family-site builder reads those
bundles for the companion HTML pages while the downloadable companion PDFs
continue to come from `scripts/process_supplemental_scans.py`.

## Upstream References

From the sibling checkout at `/Users/cam/Documents/Projects/doc-web`, the
generic recipes that shaped this project recipe are:

- `configs/recipes/recipe-images-ocr-html-mvp.yaml`
- `configs/recipes/recipe-pdf-ocr-html-mvp.yaml`

The Onward-specific recipes are useful references, but should not be reused
unchanged because their table rescue and validation knobs are tuned to *Onward
to the Unknown*.

## Known Runtime Note

The 2026-07-02 Alain run exposed a local `doc-web` bug in
`table_rescue_html_loop_v1`: its report tried to serialize a provider usage
object directly. The sibling checkout was patched locally to JSON-normalize the
usage value before writing the report. If a future fresh checkout fails at table
rescue report writing, port that fix upstream before rerunning from the
`table_rescue` stage.

## Boundary

The `doc-web` bundle is website and audio intake evidence, not
PDF-construction evidence. The downloadable PDFs continue to come from
`scripts/process_book_scans.py`.
