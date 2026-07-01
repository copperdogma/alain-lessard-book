# Runbook: `doc-web` Import

This repo should use `doc-web` after a clean source PDF or cleaned page-image
set exists.

## Current Decision

- Use local repo scripts for scan cleanup and searchable PDF construction.
- Use `doc-web` later for structural HTML, page/chapter manifests, image crops,
  and provenance sidecars that can feed the website.
- Do not treat `doc-web` as the source of the final PDF. Its maintained export
  path is `doc_web_bundle_manifest_v1` plus HTML/provenance files.

## Candidate Inputs

- Cleaned images: `output/processed-pages/`
- Distribution searchable PDF: `output/pdf/alain-lessard-book-searchable.pdf`
- Archival searchable PDF: `output/pdf/alain-lessard-book-archival-searchable.pdf`

## Candidate `doc-web` Recipes

From the sibling checkout at `/Users/cam/Documents/Projects/doc-web`:

- `configs/recipes/recipe-images-ocr-html-mvp.yaml`
- `configs/recipes/recipe-pdf-ocr-html-mvp.yaml`

The Onward-specific recipes are useful references, but should not be reused
unchanged because their table rescue and validation knobs are tuned to *Onward
to the Unknown*.

## Future First Run

After the final PDFs are accepted, create a project-specific wrapper or run
config that points `doc-web` at the distribution PDF unless the website needs
the larger archival profile:

```bash
cd /Users/cam/Documents/Projects/doc-web
python driver.py \
  --recipe configs/recipes/recipe-pdf-ocr-html-mvp.yaml \
  --input-pdf /Users/cam/Documents/Projects/alain-lessard-book/output/pdf/alain-lessard-book-searchable.pdf \
  --run-id alain-lessard-book-r1 \
  --force
```

That run should be treated as website-intake evidence, not PDF-construction
evidence.
