# AGENTS.md - Alain Lessard Book

Read this file at the start of every session.

> **Mission:** Build a trustworthy digital edition of the *Alain Lessard*
> family book from local scans, then use that canon as the basis for a durable
> family website and companion archive. The current truth surface is the local
> `input/` folder and the generated scan/PDF artifacts in `output/`.
>
> **The Ideal (`docs/ideal.md`) is the primary decision filter.** Every active
> compromise in `docs/spec.md` should point back to a named limitation and an
> honest evolution path.

## Ideal-First Methodology

**Graph + state structure:** `docs/ideal.md` captures the product and execution
ideal. `docs/spec.md` records active constraints against that ideal.
`docs/methodology/state.yaml` owns mutable planning state,
`tests/fixtures/formats/_coverage-matrix.json` owns the machine-readable source
inventory, and `docs/methodology/graph.json` compiles those surfaces into a
single inspectable planning artifact. `docs/stories.md` is generated from that
graph.

**Operating rule:** planning starts from `docs/methodology/state.yaml`,
`docs/methodology/graph.json`, and
`tests/fixtures/formats/_coverage-matrix.json`. Implementation starts from the
active story, but the relevant spec and state context still need to be read
first.

**Canonical bootstrap / refresh surface:** `/setup-methodology`

## Working Rules

- Treat `input/` as the current source contract unless the user explicitly
  redirects the project.
- Preserve raw scans. Processing scripts must write generated artifacts under
  `output/` or `tmp/`.
- For a new scan set, run `make scan-intake-report SCAN_INPUT="<path>"` before
  adapting crop, color, OCR, or PDF profile logic.
- Do not hide missing archive material. If supplemental scans are not present
  yet, keep that state explicit in docs and manifests.
- For scan processing, prefer deterministic scripts and recorded manifests over
  manual image edits.
- For PDF work, render and inspect pages before calling the output final.
- For website work, build the static bundle with `make build-family-site` and
  verify rendered pages before deployment.
- For deployment, use `make deploy-static`, keep `.env` secret, and verify the
  public host in `docs/infrastructure.md`.
- For website work, keep reader-facing language warm, family-centered, and free
  of build/process terminology.
- Provenance matters. Generated pages, OCR text, PDFs, and future website
  records should be traceable to source scans.
- Do not invent runtime commands or deployment conventions that do not exist in
  this repo yet.
- No implicit commits or pushes.
- Fresh verification required. Do not claim a transform, OCR pass, PDF, or site
  behavior is working unless it was checked in this pass.

## Skills

Canonical location: `.agents/skills/`

- Use `/setup-methodology` to install or refresh the methodology package.
- Use `/triage` to choose the next highest-leverage slice.
- Use `/align` after meaningful changes to sweep for methodology drift.
- Run `scripts/sync-agent-skills.sh` after changing project skills.

## Core Docs

- `docs/ideal.md` - product and execution ideals
- `docs/spec.md` - active project constraints with stable `spec:N` ids
- `docs/input-contract.md` - current local input contract
- `docs/infrastructure.md` - DreamHost target, DNS, and deploy command truth
- `docs/runbooks/future-book-scan-intake.md` - reusable intake and handoff
  process for future book scan projects
- `docs/runbooks/scan-to-pdf.md` - scan cleanup, PDF, and OCR runbook
- `docs/runbooks/onward-process-map.md` - mapping from previous Onward scan,
  processing, website, and `doc-web` workflows
- `docs/runbooks/doc-web-import.md` - downstream website-intake boundary
- `docs/methodology/state.yaml` - mutable planning state
- `docs/methodology/graph.json` - compiled methodology view
- `docs/setup-checklist.md` - working setup checklist
- `docs/evals/README.md` - eval registry protocol
- `docs/evals/registry.yaml` - eval source of truth
- `docs/runbooks/setup-methodology.md` - setup/refresh runbook
- `docs/templates/book-scan-intake-checklist.md` - checklist to copy for a new
  scan set
- `docs/stories.md` - generated story index
- `docs/stories/` - story files
- `docs/decisions/` - decision records
- `CHANGELOG.md` - repo change log

## Current Repo Reality

The repo has raw main-book scans, deterministic scan-to-PDF tooling, two
searchable main-book PDFs, an accepted `doc-web` HTML/provenance bundle at
`input/doc-web-html/alain-lessard-book-r1/`, 52 reviewed narrative audio tracks,
and a generated static family archive under `build/family-site/`. The current
website is built from the active `doc-web` bundle and preserves semantic reading
sections, source scan links, figures, captions, tables, TOC, search, the complete
MP3, and individual recordings. The 2026-07-16 SFTP deploy published all 53 MP3
assets to DreamHost at `/home/onward_user/alain-lessard.copper-dog.com`; public
HTTPS MIME, length, byte-range, playback, resume, download, and no-JavaScript
verification passed. The complete known supplemental scan set is present under
`input/raw scans/Alain's Song/` and
`input/raw scans/Growing Up on the Farm/`. Story 005 has also built and locally
validated a reflowable EPUB 3, a 52-chapter M4B, and device-help site surface.
The 2026-07-17 SFTP deploy published both portable files, and strict production
MIME, exact-length, byte-range, desktop, and mobile validation passed.
