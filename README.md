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
make doc-web-contract
make doc-web-run
make doc-web-import-run
make build-audiobook-script
make test-audiobook
make inspect-audiobook
make build-full-audiobook
make validate-audiobook
make test-portable-editions
make build-portable-editions RELEASE=1
make validate-portable-editions EPUBCHECK=1 EPUBCHECK_JAR=/path/to/epubcheck.jar
make build-family-site
make build-family-site RELEASE=1
make validate-family-site RELEASE=1
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

`make doc-web-run` sends the cleaned page images through the sibling
`doc-web` checkout. `make doc-web-import-run` validates and accepts the latest
HTML/provenance bundle under `input/doc-web-html/`.

`make build-audiobook-script` generates Onward-style narration scripts and the
canonical 52-track audio manifest from the active `doc-web` HTML bundle while
leaving genealogy tables, indexes, personal-record forms, and dense lists as
readable/searchable material. It preserves the reviewed local MP3 contract and
refreshes durations whenever those ignored files are present.

`make build-full-audiobook` uses `ffmpeg` to compile the manifest-ordered track
set into `audiobook/generated/alain-lessard-complete-audiobook.mp3`, inserting
the configured two-second pause between tracks and preserving a 44.1 kHz mono
speech profile. `make validate-audiobook` probes, hashes, and decodes all 52
tracks plus the complete file.

`make build-portable-editions RELEASE=1` builds two app-friendly derivatives
from the same maintained contracts: a reflowable EPUB containing all 57 book
sections and both companion documents, and a chaptered M4B containing the 52
reviewed recordings. The tracked `portable/manifest.json` owns their metadata,
generated paths, public paths, format settings, and expected counts. Run
`make validate-portable-editions` for the built-in package/media checks; add
`EPUBCHECK=1 EPUBCHECK_JAR=/path/to/epubcheck.jar` to run the official EPUBCheck
jar as part of the maintained command.

`make build-family-site` builds the static website bundle under
`build/family-site/`, including 57 meaningful reading/reference sections derived
from the `doc-web` source, figures, captions, tables, source scan links, search
data, PDF downloads, archive notes, the complete audiobook, individual track
players/downloads, and compact listening bars on track-aligned sections. The
reader does not expose printed-page routes as navigation; legacy page URLs
redirect to their containing section. Use `RELEASE=1` to require all 53 MP3
assets plus the generated EPUB and M4B. The release bundle also publishes a
plain-language device-help page and direct no-JavaScript download links.

`make deploy-static` first runs strict audiobook bundle validation, then uploads
`build/family-site/` to DreamHost using the gitignored local `.env`. The
intended public host is
`alain-lessard.copper-dog.com`. Install the deploy helper dependency first:

```bash
make deploy-deps
```

That target deliberately uses the same Python interpreter as the deployment
target, avoiding a dependency installed into a different local environment.

The 2026-07-01 SFTP upload completed to DreamHost, the DreamHost hosted
subdomain is mapped to the uploaded directory, Cloudflare points the proxied
record at DreamHost's assigned origin, and public HTTPS verification now passes;
see `docs/infrastructure.md`.

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
- `audiobook/manifest.json`
- `audiobook/generated/alain-lessard-complete-audiobook.mp3`
- `audiobook/generated/alain-lessard-complete-audiobook.m4b`
- `output/portable/alain-lessard-family-history.epub`
- `portable/manifest.json`
- `build/family-site/`

## `doc-web` Boundary

`doc-web` is the active downstream runtime for turning this book into a
website-ready HTML/provenance bundle. It consumes the cleaned image set at
`output/processed-pages/` through `configs/doc-web/recipe-alain-images-html-mvp.yaml`.

The accepted bundle is committed under `input/doc-web-html/alain-lessard-book-r1/`,
with `input/doc-web-html/active-bundle.json` naming the current source for the
website and audio-script builders.

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

The main-book scan cleanup, searchable PDFs, hosted site path, doc-web HTML
intake, reviewed 52-track narration set, complete local audiobook, and strict
audio-enabled site bundle are established. The complete audiobook and all 52
individual tracks were deployed and publicly range-verified on 2026-07-16. The
production closeout also verified native playback, resume, single-player
behavior, downloads, and the no-JavaScript fallback; Story 004 is complete.
Story 005 adds EPUB 3 and chaptered M4B release artifacts plus the device-help
website surface. Both files were deployed on 2026-07-17 and passed strict public
MIME, exact-length, byte-range, desktop, and mobile verification; Story 005 is
complete.

## Audiobook

The audio was generated with ElevenLabs Multilingual v2 using the voice
"Matilda" (voiceId: `XrExE9yKIg1WjnnlVkGX`). The reviewed source MP3s and
generated complete audiobook are intentionally ignored by Git; the tracked
manifest, builder, validators, and documentation make the release reproducible
from those local assets.
