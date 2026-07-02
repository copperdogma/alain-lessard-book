---
title: "doc-web powered Onward-style site"
status: "Done"
priority: "High"
ideal_refs:
  - "Website Family Archive"
  - "Onward-Style Audio Companion"
  - "Trustworthy Source Lineage"
spec_refs:
  - "spec:4"
  - "C4"
adr_refs: []
depends_on:
  - "story-001-main-book-scan-to-searchable-pdf"
  - "story-002-dreamhost-hosted-subdomain-public-verification"
category_refs:
  - "spec:4"
compromise_refs:
  - "C4"
input_coverage_refs:
  - "main-book-raw-scans"
  - "processed-pages"
  - "searchable-pdf"
architecture_domains:
  - "doc-web import"
  - "static family site"
  - "audiobook script generation"
roadmap_tags:
  - "website-quality"
legacy_system: ""
---

# Story 003 - doc-web powered Onward-style site

**Priority**: High
**Status**: Done
**Decision Refs**: `docs/runbooks/doc-web-import.md`, `docs/runbooks/onward-process-map.md`, `docs/input-contract.md`
**Depends On**: story-001, story-002

## Goal

Replace the first-pass page-range website with a doc-web-powered digital edition that is much closer to the Onward treatment. The cleaned Alain page images should feed doc-web, the resulting HTML/provenance bundle should become the canonical website and audio-script source, and the public site should preserve doc-web sections, tables, figures, captions, source links, and a working table of contents.

## Acceptance Criteria

- [x] The repo has a documented `doc-web` runtime config, Alain-specific recipe, and Make targets that run/import a doc-web bundle without relying on hand-written section ranges.
- [x] A fresh doc-web run against `output/processed-pages/` is imported into the repo under `input/doc-web-html/` with manifest, entry HTML, images, and provenance sidecars intact.
- [x] `make build-family-site` builds the website from the active doc-web bundle, preserving tables, figures, captions, entry navigation, page ranges, search, archive downloads, and source provenance notes.
- [x] `make build-audiobook-script` uses the doc-web bundle and skips table/list/index-heavy entries so audio remains Onward-style narrative audio.
- [x] Local artifact inspection verifies representative section pages with tables and figures, the TOC, search index, and copied image assets.
- [x] The DreamHost deployment is refreshed and the public host is checked after deployment.

## Out of Scope

- Creating new supplemental scans that are not present yet.
- Producing reviewed narrated MP3 files.
- Replacing the already accepted scan cleanup and searchable PDF construction path.
- Editing source scan pixels manually outside deterministic scripts.

## Approach Evaluation

- **Simplification baseline**: A one-off LLM conversion could improve a few pages, but it would not produce the durable manifest/provenance contract or repeatable Onward-style pipeline the user asked for.
- **AI-only**: Letting an LLM emit an entire site from scans would be expensive, difficult to verify, and weak on source lineage.
- **Hybrid**: Use doc-web for OCR/structure/table/figure/caption extraction, then use repo-owned deterministic builders for site/audio/deploy. This matches Onward and preserves traceable artifacts.
- **Pure code**: Pure code can wire the bundle and site, but cannot reliably recover scan structure, tables, and captions from page images by itself.
- **Repo constraints / prior decisions**: `docs/runbooks/doc-web-import.md` says doc-web starts after cleaned PDFs/images and should emit `doc_web_bundle_manifest_v1` plus provenance, not the final PDF.
- **Existing patterns to reuse**: Onward `doc-web-runtime.json`, `scripts/doc_web_import.py`, doc-web generic image/PDF recipes, and Onward's bundle-driven website builder patterns.
- **Eval**: A fresh doc-web run plus local static build inspection is the primary eval; sample HTML pages must contain preserved `<table>` and `<figure>/<figcaption>` structures and public deployment must serve the rebuilt bundle.

## Tasks

- [x] Add Alain doc-web runtime config, recipe, wrapper script, and Make targets.
- [x] Dry-run and then run doc-web against `output/processed-pages/`; validate/import the bundle snapshot under `input/doc-web-html/`.
- [x] Rework `scripts/build_family_site.py` to read the active doc-web bundle and render linked section pages, TOC, search, figures, tables, archive, and provenance surfaces.
- [x] Rework `scripts/build_audiobook_script.py` to read doc-web entries and skip table/list/index-heavy entries.
- [x] Update docs/spec/state/coverage/runbooks/README to name the new doc-web website source of truth.
- [x] Run required checks for touched scope: doc-web contract/dry-run/full run, `make build-audiobook-script`, `make build-family-site`, local HTML/link/asset inspection, deployment, and public host check.
- [x] Check whether the old hard-coded section-range path is redundant and remove it or leave a documented fallback.
- [x] Verify Central Tenets:
  - [x] T0 - Traceability: output pages/scripts trace to source pages and doc-web provenance.
  - [x] T1 - AI-First: doc-web owns OCR/structure recovery where AI is useful.
  - [x] T2 - Eval Before Build: current hard-coded baseline was inspected and found not doc-web-backed.
  - [x] T3 - Fidelity: tables, figures, captions, and page links are preserved.
  - [x] T4 - Modular: Alain recipe/config is project-owned and doc-web remains the upstream runtime.
  - [x] T5 - Inspect Artifacts: generated pages and public deploy are inspected.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning module / area**: `scripts/doc_web_import.py`, `doc-web-runtime.json`, `configs/doc-web/`, `scripts/build_family_site.py`, `scripts/build_audiobook_script.py`.
- **Methodology reality**: `spec:4` substrate exists but is below the ideal because the current site is generated from hard-coded page ranges and PDF text rather than doc-web structural HTML.
- **Substrate evidence**: `output/processed-pages/` contains 153 cleaned page JPEGs; `/Users/cam/Documents/Projects/doc-web` has `driver.py` and generic image/PDF HTML recipes; Onward has a committed doc-web bundle under `input/doc-web-html/story206-onward-proof-r10/`.
- **Data contracts / schemas**: Consume existing `doc_web_bundle_manifest_v1` and `doc_web_provenance_block_v1`; no schema change expected.
- **File sizes**: `scripts/build_family_site.py` is 930 lines and should be simplified or kept focused while adding bundle support; `scripts/build_audiobook_script.py` is 151 lines; `Makefile` is 54 lines; `docs/runbooks/doc-web-import.md` is 47 lines.
- **Decision context**: No ADRs exist beyond `docs/decisions/README.md`; the relevant decision truth is in the doc-web and Onward process runbooks.

## Files to Modify

- `doc-web-runtime.json` - project runtime config for sibling doc-web.
- `configs/doc-web/recipe-alain-images-html-mvp.yaml` - Alain-specific recipe.
- `scripts/doc_web_import.py` - run/import helper for doc-web bundles.
- `Makefile` - doc-web contract/run/import targets.
- `scripts/build_family_site.py` - render from doc-web manifest/content.
- `scripts/build_audiobook_script.py` - generate narrative scripts from doc-web entries.
- `docs/runbooks/doc-web-import.md`, `docs/input-contract.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `tests/fixtures/formats/_coverage-matrix.json`, `README.md`, `CHANGELOG.md` - durable truth updates.

## Redundancy / Removal Targets

- Hard-coded `SECTIONS` in `scripts/build_family_site.py`.
- PDF text extraction as the website and audio source.
- Documentation that says doc-web is only a future boundary.

## Notes

Use the cleaned page images as doc-web input rather than the PDF so cropped figure assets are derived from the accepted processed pages and avoid another PDF rasterization pass. The PDF pipeline remains the source for downloadable PDFs.

## Plan

1. Add project-owned doc-web config/recipe/import tooling and dry-run it.
2. Run doc-web against the cleaned page images, import the generated HTML bundle, and inspect manifest/provenance plus sample entries.
3. Rebuild the site/audio generators around the imported bundle and keep PDF downloads from the existing PDF pipeline.
4. Verify locally with generated artifacts and browser checks; deploy and public-check the host.
5. Update docs, methodology state, and commit/push once checks pass.

## Work Log

20260701-2251 - action: created story from user goal; evidence: existing site builder uses hard-coded `SECTIONS` and PDF text while Onward stores doc-web bundles under `input/doc-web-html`; next step: add doc-web runtime/recipe/import tooling.
20260702-0027 - action: ran and imported `doc-web` bundle `alain-lessard-book-r1`; evidence: `make doc-web-validate-active` reports 39 entries, 1,738 provenance rows, 155 images; next step: rebuild site/audio from active bundle.
20260702-0108 - action: replaced hard-coded site/audio builders with active-bundle readers; evidence: `make build-family-site` built 39 entry pages, 15 audio scripts, 155 doc-web crops, 153 source scan images, local link/image verifier passed 43 HTML files and 847 references; next step: deploy and public-check.
20260702-0124 - action: browser-verified local build; evidence: homepage, search, figure-heavy `chapter-001.html`, and table-heavy `chapter-016.html` render with no page-level overflow after table scroll containment; next step: deploy static bundle.
20260702-0159 - action: deployed rebuilt doc-web-powered site; evidence: `make deploy-static` uploaded root-level `chapter-###.html`, `page-###.html`, `images/doc-web`, `images/scans`, scripts, data, and downloads to DreamHost; public checks returned `HTTP/2 200` for `/`, `chapter-001.html`, and `chapter-016.html`; live browser search for "Veillardville" returned 12 results with first link `chapter-014.html`; next step: `/check-in-diff`.

## Closeout Evidence

- `make doc-web-validate-active` passed for `input/doc-web-html/alain-lessard-book-r1/` with 39 entries, 1,738 provenance rows, and 155 images.
- `python3 -m py_compile scripts/build_family_site.py scripts/build_audiobook_script.py` passed.
- `make build-family-site` passed and rebuilt 39 entry pages plus 15 narrative audio scripts.
- Local generated-site validation passed for 43 HTML files, 691 local links, and 156 image references.
- Browser checks passed locally for homepage, search, `chapter-001.html` figure/caption placement, `chapter-016.html` table preservation, desktop overflow, and mobile overflow.
- `make deploy-static` completed against `/home/onward_user/alain-lessard.copper-dog.com`.
- Public checks verified the deployed r2 bundle:
  - `https://alain-lessard.copper-dog.com/` returns `HTTP/2 200`.
  - `https://alain-lessard.copper-dog.com/chapter-001.html` returns `HTTP/2 200` and contains `images/doc-web/page-024-000.jpg` plus the "The little cowboys" caption.
  - `https://alain-lessard.copper-dog.com/chapter-016.html` returns `HTTP/2 200` and contains `table-scroll` wrappers around preserved tables.
  - `https://alain-lessard.copper-dog.com/search-index.json?v=20260702-docweb-r2` has 39 entries and no stale `pages/` URLs.
  - Live browser search for "Veillardville" returned 12 results; first result is `Part V - Veillardville` linking to `chapter-014.html`.
