---
title: "Portable eReader and chaptered audiobook editions"
status: "Done"
priority: "High"
ideal_refs:
  - "Website Family Archive"
  - "Onward-Style Audio Companion"
  - "Accessible Reading"
  - "Trustworthy Source Lineage"
  - "One Canon, Many Experiences"
spec_refs:
  - "spec:4"
  - "C4"
adr_refs: []
depends_on:
  - "story-003-doc-web-powered-onward-style-site"
  - "story-004-publish-complete-on-site-audiobook"
category_refs:
  - "spec:4"
compromise_refs:
  - "C4"
input_coverage_refs:
  - "doc-web-html-bundle"
  - "family-site-reading-sections"
  - "reviewed-audiobook-tracks"
  - "complete-audiobook"
architecture_domains:
  - "portable publication packaging"
  - "audiobook content model"
  - "static family site"
roadmap_tags:
  - "portable-family-editions"
legacy_system: "website, PDF, and MP3-only distribution without reader-app or chaptered-audiobook downloads"
---

# Story 005 — Portable eReader and chaptered audiobook editions

**Priority**: High
**Status**: Done
**Decision Refs**: `docs/scout/scout-001-ereader-and-audiobook-formats.md`,
`docs/ideal.md`, `docs/spec.md`, `docs/runbooks/onward-process-map.md`,
`docs/infrastructure.md`, `tests/fixtures/formats/_coverage-matrix.json`, W3C
EPUB 3.3 and EPUB Accessibility 1.1, EPUBCheck, and current Apple, Amazon,
Kobo, and Google reader-import documentation; none found after search for a
repo-local portable-publication ADR
**Depends On**: Stories 003 and 004

## Goal

Publish the same trusted Alain Lessard family edition in two portable formats
that relatives can take into familiar reading and listening apps: a reflowable,
accessible EPUB 3 containing the complete semantic reading edition and its two
companion documents, and a single M4B containing the 52 reviewed recordings as
named chapters. Add large, plain-language download choices and short Apple,
Kindle, Kobo, Google Play Books, and audiobook-app instructions to the static
site without pretending that browsers can silently install files into every
third-party app.

## Acceptance Criteria

- [x] A maintained deterministic command builds a DRM-free EPUB 3 from the
      same canonical `doc-web` bundle and 57-section reading model as the site,
      then appends the two accepted companion documents without using printed
      page routes or hand-copied prose.
- [x] The EPUB contains a real cover, publication metadata, landmarks and table
      of contents, all 57 named main-book sections in order, both companion
      documents, every referenced meaningful figure/caption, usable narrow-
      screen tables, and a short source/archive note; it preserves all 1,737
      main-book source block ids exactly once.
- [x] EPUB content is reflowable and accessible: language and title metadata,
      semantic headings, image alternative text, visible focus/link treatment,
      responsive images and tables, no website navigation/player chrome, and
      no remote assets or scripting. The packaged EPUB remains below Amazon's
      current 200 MB Send to Kindle limit.
- [x] The EPUB passes a repo-owned structural validator and the current
      official EPUBCheck release with zero errors; it is visually inspected in
      Apple Books and at least one independent/Kindle-compatible renderer for
      contents, resizing, figures, captions, tables, links, and companions.
- [x] A maintained deterministic command builds a single `.m4b` from the 52
      reviewed MP3s in manifest order, adds the manifest's configured silence,
      encodes compatible mono AAC-LC, embeds a compact cover and title/album/
      artist/narrator metadata, and defines exactly 52 correctly named chapters.
- [x] M4B validation proves chapter numbering, names, order, boundaries,
      duration, mono sample profile, AAC codec, embedded cover, and metadata;
      representative beginning, middle, boundary, and ending samples are
      decode-checked and listening-compared without changing source MP3s.
- [x] The static release bundle publishes stable direct download paths for the
      EPUB and M4B while retaining the searchable PDF, complete MP3, and
      individual MP3s as fallbacks; release build/validation fails if either
      new portable artifact is missing, empty, structurally invalid, or not
      linked.
- [x] The family site adds a warm `Read or listen in another app` handoff with
      large literal EPUB, M4B, MP3, and help actions plus short Apple Books,
      Kindle/Send to Kindle, Kobo, Google Play Books, and audiobook-app steps.
      Direct downloads work without JavaScript and no user-agent sniffing,
      brittle app deep links, account requirement, or universal-install claim
      is introduced.
- [x] Focused fixtures cover EPUB package invariants, source-block and image
      coverage, M4B metadata/chapter math, artifact copying, release failure,
      platform-help content, and no-JavaScript direct links without copying the
      real multi-gigabyte corpus into tests.
- [x] README, audiobook/runbook/infrastructure guidance, spec/state/coverage
      truth, and changelog describe the portable release and its public
      delivery honestly.
- [x] Production serves the EPUB as `application/epub+zip` and the M4B as
      `audio/mp4` at their stable paths with exact local byte lengths and
      working `206 Partial Content` ranges; the complete public page/link/audio
      gate and desktop/mobile browser smoke pass after deployment.

## Out of Scope

- Publishing to Audible, Apple Books Store, Kindle Store, Kobo Store, Spotify,
  podcast directories, or any account-backed commercial catalog.
- DRM, purchases, account creation, or a service that uploads files on a
  relative's behalf.
- MOBI/AZW3 as maintained outputs, fixed-layout EPUB, or a bespoke reader app.
- Embedding the nine-hour audiobook into the EPUB, word/sentence highlighting,
  media overlays, or regenerating narration.
- Replacing the scanned searchable PDFs, existing website reader, complete MP3,
  or individual MP3s.
- Claiming a universal one-click install where platform security/import flows
  require a download, share sheet, upload, or USB sideload.

## Approach Evaluation

- **Simplification baseline**: The current site has no EPUB, M4B, reader-app
  help, or portable-edition link. One LLM call cannot package standards-
  compliant ZIP/XML publications, transcode nine hours of audio, or prove
  binary chapter boundaries; deterministic code is the simpler baseline.
- **Candidate A — Pandoc plus one merged audiobook transcode**: Quick EPUB
  scaffolding, but it would require flattening/reconstructing the existing HTML
  and risks losing source ids, figures, captions, and table semantics. Encoding
  the already merged MP3 is simple but adds another lossy generation.
- **Candidate B — repo-owned EPUB package plus manifest-driven M4B assembly**:
  Reuse the exact semantic reading catalog and companion HTML, normalize it to
  EPUB XHTML, copy only referenced images, and use the 52 source tracks plus
  generated chapter metadata for one AAC encoding pass. This is the working
  choice because it keeps canon/lineage visible and makes validation explicit.
- **Candidate C — W3C Audiobook/LPF or synchronized read-along EPUB**: Open and
  expressive, but familiar consumer-app ingestion is weaker and synchronized
  text/audio would require timing data the repo does not own.
- **AI-only**: Not appropriate for packaging, media conversion, manifest math,
  ZIP ordering, XML validation, or byte-level artifact checks.
- **Hybrid**: AI judgment may help spot-check reader-facing wording and visual
  results, but deterministic builders and validators own all release truth.
- **Pure code**: Correct for canonical-content transformation, image copying,
  metadata, chapter math, transcoding, static rendering, and validation.
- **Repo constraints / prior decisions**: Story 004 intentionally deferred M4B
  until the browser/MP3 lane shipped. The new artifacts remain ignored and
  reproducible; `build/family-site/` stays the only deploy source; source scans,
  reviewed MP3s, and accepted `doc-web` content are unchanged.
- **Existing patterns to reuse**: `scripts/reading_sections.py`,
  `derive_site_reading_catalog`, companion-document HTML normalization,
  `scripts/audiobook.py`, the full-audiobook preflight, manifest-configured
  pauses, strict site release validation, and direct-download/no-JS behavior.
- **Eval**: The baseline is zero EPUB/M4B files and zero portable-app links.
  The selected approach must pass structural fixtures, EPUBCheck, `ffprobe`
  chapter/stream assertions, exact source coverage, real artifact inspection,
  and representative reader/app smoke checks.

## Tasks

- [x] Add focused failing fixtures for EPUB ordering/coverage/package rules,
      M4B chapter math/metadata, site copying/links, and strict missing-artifact
      behavior; add a maintained `make test-portable-editions` target.
- [x] Add a focused portable-publication module that consumes the canonical
      reading/companion substrate and builds a valid EPUB 3 with normalized
      XHTML, referenced images, cover, CSS, navigation, metadata, and traceable
      section/source ids.
- [x] Add a repo-owned EPUB validator and CLI/build target, invoke EPUBCheck
      when available, and make errors actionable without requiring a reader app.
- [x] Add a focused manifest-driven M4B builder with one-pass AAC-LC encoding,
      compact cover generation, exact 52-chapter ffmetadata, overwrite safety,
      and strict `ffprobe` verification.
- [x] Extend the static site build and release validator to publish/require the
      EPUB and M4B, render direct download/help surfaces, and preserve PDF/MP3
      fallbacks without JavaScript or user-agent branching.
- [x] Build and inspect the real EPUB/M4B artifacts, including EPUBCheck,
      source-block/image/package audits, M4B cover/metadata/chapter/duration
      audits, representative decoded audio comparisons, file sizes, and app/
      reader visual smoke checks available on this Mac.
- [x] Update `README.md`, `audiobook/README.md`,
      `docs/infrastructure.md`, `docs/runbooks/onward-process-map.md`,
      `docs/spec.md`, `docs/methodology/state.yaml`, the coverage matrix, and
      `CHANGELOG.md` after fresh local evidence exists.
- [x] Check whether the chosen implementation makes hand-maintained format
      paths or duplicated metadata redundant; keep one portable-edition
      contract and remove parallel constants where practical.
- [x] Run required checks for touched scope:
  - [x] Python syntax compilation for all changed/new Python modules.
  - [x] `make test-audiobook` and `make test-portable-editions` (the repo has no
        generic `make test` or `make lint` targets).
  - [x] `make build-portable-editions RELEASE=1`, `make validate-audiobook`,
        `make validate-family-site RELEASE=1`, and inspect generated artifacts.
  - [x] `make doc-web-validate-active`, `make validate-companion-doc-web`,
        `make validate-supplemental-docs`, and `make methodology-check`.
- [x] If evals or goldens changed: not expected; record deterministic fixture,
      binary, and renderer checks in the story instead of creating an AI eval.
- [x] Search all docs and update anything related to portable output or release
      validation that the implementation changes.
- [x] Run formal diff/story validation, including all untracked files, the full
      20-test Python suite, Ruff, source/companion validators, official
      EPUBCheck, media decode/probe checks, strict site validation, and
      methodology/skill checks.
- [x] Publish the strict `build/family-site/` bundle to the repo-declared Alain
      DreamHost path, then run the strict public validator across every
      page/reference, all 53 MP3s, and both portable files.
- [x] Smoke-test the real production homepage, device-help page, and audiobook
      page at desktop and 390px mobile widths; verify literal download links,
      live asset version, counts, no horizontal overflow, and clean browser
      logs.
- [x] Harden the SFTP helper so an EOF with a nonzero or unknown child exit
      status cannot be reported as a successful upload; cover failure and
      success exits with focused regression tests.
- [x] Verify Central Tenets:
  - [x] T0 — Traceability: EPUB sections/images and M4B chapters map back to the
        accepted reading and audiobook manifests.
  - [x] T1 — AI-First: use AI only for bounded review judgment; keep standards
        packaging and media transformation deterministic.
  - [x] T2 — Eval Before Build: record the zero-artifact/link baseline and add
        structural fixtures before implementation.
  - [x] T3 — Fidelity: preserve all canonical source blocks and reviewed audio
        order without editorial or narration changes.
  - [x] T4 — Modular: keep portable packaging outside the large site builder
        and consume existing contracts rather than fork them.
  - [x] T5 — Inspect Artifacts: render/open the EPUB and probe/decode/listen to
        representative M4B content, not merely trust command exits.

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

- **Owning module / area**: New focused portable-publication and M4B modules own
  package/media generation and validation. Existing reading/audio contracts own
  order and lineage; `scripts/build_family_site.py` only copies and links the
  declared results; `scripts/validate_family_site.py` owns release presence and
  reader-facing surface checks.
- **Methodology reality**: `spec:4` has an `exists` substrate and C4 can return
  to `hold`: the coverage matrix records generated EPUB/M4B artifacts and their
  verified production delivery alongside the deployed PDF/MP3 truth.
- **Substrate evidence**: `build/family-site/_internal/reading-sections.json`
  records 57 semantic sections and 1,737 main-book source blocks are already
  coverage-checked by the reader builder. The active `doc-web` bundle includes
  the corresponding HTML and about 89 MiB of figure crops. The canonical v4
  audio manifest and reviewed corpus contain 52 ordered mono MP3 tracks plus a
  verified 9:00:14 complete MP3. `ffmpeg`, `ffprobe`, Pandoc, and Java exist;
  EPUBCheck 5.3.0 was exercised from its official release jar and epub.js was
  used as a temporary independent renderer; Calibre is not installed.
- **Data contracts / schemas**: Add one tracked portable-edition metadata
  contract with stable generated/public paths, MIME types, source counts, and
  expected M4B chapter count. EPUB internals follow EPUB 3/OCF rather than a
  bespoke schema; M4B chapters derive from the existing v4 audiobook manifest.
  No database or cross-repo API schema changes.
- **File sizes**: `scripts/build_family_site.py` is 2,930 lines and
  `scripts/validate_family_site.py` is 1,213 lines, so core builders/validators
  remain focused modules. `scripts/deploy_static_site.py` is 357 lines and now
  has a focused exit-status test; avoid pushing format logic into the deployer.
- **Decision context**: Reviewed Ideal/spec/state/graph/coverage, Stories 003
  and 004, Onward process/infrastructure guidance, Scout 001, current accepted
  source/artifact contracts, and official platform/EPUB documentation. No ADR
  exists or is required because this adds deterministic outputs within the
  existing static publishing boundary; a storefront or shared publication API
  would require a separate decision.

## Files to Modify

- `docs/stories/story-005-portable-ereader-and-chaptered-audiobook.md` — plan,
  execution record, and evidence (new)
- `portable/manifest.json` — tracked format/output contract (new)
- `scripts/portable_editions.py` — shared contract, EPUB build/validation, and
  site-facing artifact inventory (new)
- `scripts/build_m4b.py` — manifest-driven chaptered audiobook builder (new)
- `scripts/build_family_site.py` — copy/link formats and render help surface
  (2,701 lines; keep logic thin)
- `scripts/validate_family_site.py` — strict format and UI checks (1,026 lines)
- `tests/test_portable_editions.py` and `tests/test_build_m4b.py` — focused
  small-fixture coverage (new)
- `scripts/deploy_static_site.py` and `tests/test_deploy_static_site.py` — fail
  closed when SFTP itself does not exit successfully
- `Makefile` and `.gitignore` — build/test commands and generated artifacts
  (111 and 19 lines)
- `README.md`, `audiobook/README.md`, `docs/infrastructure.md`,
  `docs/runbooks/onward-process-map.md`, `docs/spec.md`,
  `docs/methodology/state.yaml`, `tests/fixtures/formats/_coverage-matrix.json`,
  and `CHANGELOG.md` — durable truth after validation

## Redundancy / Removal Targets

- Repeated EPUB/M4B filenames or metadata in builder, renderer, and validator;
  `portable/manifest.json` should be the sole contract.
- A second copy of section/companion ordering; portable EPUB generation must
  consume the maintained reading and companion models.
- Any tempted user-agent-specific or pseudo-universal install link; retain
  plain direct downloads and official platform guidance.
- A second audio concatenation order or hand-maintained chapter list; derive
  all M4B chapters from `audiobook/manifest.json`.

## Notes

- This is a new Story 005 rather than reopened Story 004 because Story 004
  explicitly deferred chapterized M4B and closed on the deployed browser/MP3
  experience. EPUB adds a distinct publication format, validation standard,
  app-import UX, and release artifact boundary.
- The first EPUB includes the complete readable edition, not only narrated
  prose. Tables, reference sections, and both companion documents remain
  readable; audio still follows the reviewed narrative-only contract.
- Direct-download links are the durable baseline. Platform help should say
  exactly what happens next instead of promising that a browser can choose or
  configure another app automatically.

## Plan

1. **Lock deterministic contracts and failing fixtures (S).** Add
   `portable/manifest.json`, small XHTML/image/audio fixtures, and tests for OCF
   ZIP ordering, metadata/navigation/spine, source block coverage, referenced
   assets, chapter-boundary math, M4B stream metadata, and release-copy/link
   failure. Done means the baseline records zero artifacts/links and the tests
   express the portable release boundary without the real corpus.
2. **Build the EPUB from canonical semantic content (L).** Add a focused module
   that imports the maintained reading/companion composition functions,
   normalizes HTML5 fragments to EPUB XHTML, removes site-only attributes,
   rewrites/copies referenced images, emits cover/CSS/nav/package documents,
   stores `mimetype` first and uncompressed, and validates the ZIP/XML/content
   graph. Done means all source ids, sections, companions, images, captions,
   and tables are present in a sub-200 MB `.epub` with no remote dependencies.
3. **Build the chaptered audiobook once (M).** Add M4B chapter math and an
   `ffmpeg` builder that preflights all reviewed tracks, inserts the manifest
   pause, encodes mono AAC-LC in one pass, attaches a compact cover, and writes
   52 ffmetadata chapters plus publication metadata. Done means `ffprobe`
   reports one AAC audio stream, an attached cover, 52 ordered chapters, and a
   duration matching the source sum plus gaps.
4. **Publish a literal, no-surprises handoff (M).** Extend the site with a
   compact homepage/book/audiobook entry and one help page explaining Apple,
   Kindle, Kobo, Google, and generic audiobook imports. Copy declared EPUB/M4B
   artifacts to stable paths and retain PDF/MP3 options. Done means every
   action is an ordinary same-origin link, works without JavaScript, and makes
   no universal-install claim.
5. **Make portable release completeness strict (M).** Extend release mode and
   tests to reject absent/invalid artifacts, wrong counts/MIME paths, stale
   links, or missing help. Keep development builds honest when ignored binary
   outputs are absent, but make `build-portable-editions RELEASE=1` and deploy
   validation require them.
6. **Exercise real artifacts and renderers (L).** Build against all 57 sections,
   two companions, referenced crops, and 52 tracks; run internal validation,
   official EPUBCheck, chapter/cover/codec probes, representative decode/audio
   comparisons, file-size checks, and Apple Books plus another available
   renderer/app smoke. Inspect desktop/mobile/no-JS site output as well.
7. **Run independent story validation (M).** Audit tracked and untracked diffs,
   run the complete code/source/package/media/site/methodology check matrix, and
   fix only narrow close-out findings. Done means every acceptance criterion is
   freshly evidenced and the story is recommended `Close now` before upload.
8. **Deploy and prove public delivery (L).** Confirm the repo-local
   infrastructure target, credential presence, deploy dependency, source
   bundle, ignored `_internal/` boundary, and inclusion of `.htaccess`; upload
   the entire maintained bundle and require a real zero SFTP exit. Then run the
   strict public validator for every HTML/reference, all existing audio, EPUB/
   M4B MIME, exact bytes, and `206` ranges. The upload transcript alone is not a
   release proof, and the media-heavy all-at-once transfer can take several
   minutes within the configured 30-minute timeout.
9. **Smoke production and close durable truth (M).** Inspect the live homepage,
   help surface, and audiobook page at desktop and a 390px mobile viewport;
   confirm literal links, current asset version, expected players/cards, no
   horizontal overflow, and no browser warnings/errors. Only then update
   infrastructure/spec/state/coverage/scout/changelog truth, run
   `/mark-story-done`, and proceed to `/check-in-diff`.

## Reusable Onward Handoff Checklist

Use these as the implementation and release gates when adapting Story 005 to
Onward; replace Alain-specific counts, titles, paths, and hosts with Onward's
canonical contracts rather than copying them literally.

1. Inventory the semantic reading order, companion content, image references,
   reviewed audio order/durations, current static deploy source, and public
   host before choosing output paths.
2. Add one tracked portable manifest that owns publication metadata, cover,
   generated paths, public paths, MIME types, size ceiling, codec profile, and
   expected section/chapter counts. Keep EPUB/M4B binaries reproducible and
   gitignored.
3. Build EPUB from the same canonical reading model as the site, not rendered
   page routes or copied prose. Preserve ids, headings, figures/captions,
   tables, companion documents, source/archive context, reflow, accessibility,
   deterministic ZIP order, and local-only assets.
4. Build M4B directly from reviewed chapter sources in manifest order with the
   configured pauses, a single AAC-LC encode, cover, publication/narrator
   metadata, and manifest-derived chapter names and boundaries. Do not encode
   from an already lossy merged MP3 when the original reviewed tracks exist.
5. Add direct EPUB/M4B links, retain PDF/MP3 fallbacks, and provide brief Apple,
   Kindle, Kobo, Google, and generic audiobook-app guidance. Use ordinary
   no-JavaScript links and do not promise universal one-click installation.
6. Make release mode fail closed on missing/invalid artifacts, incorrect
   package/stream/chapter/source coverage, missing UI links, or wrong MIME
   mappings. Cover these contracts with small fixtures before building real
   media.
7. Validate real outputs with the repo validator, official EPUBCheck, at least
   two EPUB renderers including a familiar reader, `ffprobe`, representative
   audio decodes/comparisons, and an audiobook app import/chapter/playback
   smoke. Record exact bytes, duration, hashes, counts, and tool versions.
8. Preflight the actual deployment target and source. Ensure the server config
   file that declares `application/epub+zip` and `audio/mp4` is included while
   maintenance-only files remain excluded. Treat a nonzero or unknown SFTP
   child exit as failure and allow enough timeout for the full media bundle.
9. After upload, validate the public host—not the transcript—for all pages and
   existing audio plus EPUB/M4B HTTP 200, exact `Content-Type` and
   `Content-Length`, and ranged GET `206`/`Content-Range` behavior.
10. Smoke live desktop and narrow mobile UI, direct links, fallback copy,
    expected counts, overflow, current asset version, and browser logs. Update
    story/spec/state/coverage/infrastructure truth only after that proof, then
    close, commit, sync, and push.

Impact/risk: malformed XHTML, duplicate ids, source-image path rewrites, very
large tables, AAC compatibility/quality, cover attachment semantics, and the
site's already-large release bundle are the main risks. The plan isolates both
builders, uses small fixtures before the real corpus, keeps source artifacts
untouched, and does not add a runtime service or paid publishing account. The
user explicitly pre-approved build-story stop points and high-agency execution
on 2026-07-17, so no additional human gate is required for this written plan.

## Work Log

20260717-1416 — action: created Story 005 from approved Scout 001 and completed
build-story exploration/plan before implementation; result: confirmed this is
a distinct story because Story 004 explicitly deferred M4B and had no EPUB
success surface, while the current repo has sufficient canonical reading,
companion, image, and audio substrate to build both formats without editorial
changes; evidence: the current baseline has zero `.epub`/`.m4b` artifacts and
zero reader-app handoff links, the semantic catalog has 57 sections and the
audio manifest 52 reviewed tracks, accepted figure crops total about 89 MiB,
and local tools include `ffmpeg`, `ffprobe`, Pandoc, Java, and AAC encoders but
not EPUBCheck/Calibre; decisions: select a repo-owned EPUB 3 package and direct
manifest-driven AAC-LC M4B instead of Pandoc flattening, synchronized EPUB, or
W3C audiobook packaging; files at risk: the 2,701-line site builder, 1,026-line
site validator, clean build directory, and approximately 2.0 GiB release
bundle; next step: mark the story In Progress, add fixtures/contracts, and
implement under the user's explicit pre-approval of build-story stop points.

20260717-1438 — action: implemented the tracked portable-edition contract,
focused EPUB/M4B builders and validators, small fixtures, Make targets, and
ignored output paths; result: the EPUB builder consumes the canonical
57-section reading catalog and two companion documents, while the M4B builder
derives all chapter order/timing from the 52-track v4 audiobook manifest and
encodes directly from reviewed sources; evidence: seven portable-package/site
tests and one two-track M4B integration test pass, including OCF order, exact
source ids, alternative text, duplicate-heading avoidance, copying, strict
missing-artifact failure, literal no-JavaScript links, metadata, cover, and
chapter math; decision: `portable/manifest.json` remains the only manually
maintained publication/path/format contract; next step: build and inspect the
full real artifacts.

20260717-1448 — action: built and standards-validated the real EPUB; result:
`output/portable/alain-lessard-family-history.epub` is 94,390,319 bytes (90.0
MiB), contains 221 files, 59 content documents (57 main plus 2 companions), 156
local image references, all 1,737 expected main source ids exactly once, local
CSS/navigation/landmarks/metadata, and no remote asset or script; evidence:
repo validation passed and the official EPUBCheck 5.3.0 jar reported 0 fatals,
0 errors, 0 warnings, and 0 infos under EPUB 3.3 rules; Apple Books import
showed the full contents through Personal Records, Bibliography, Alain's Song,
and Growing Up on the Farm, rendered figures/captions/alt text and wide tables,
and reflowed the tables after font enlargement; independent epub.js rendering
also exposed all 59 contents, semantic tables, images, and the complete final
companion with no console warnings/errors; next step: build/probe/listen to the
full chaptered audiobook.

20260717-1456 — action: built and inspected the real chaptered M4B; result:
`audiobook/generated/alain-lessard-complete-audiobook.m4b` is 269,966,138
bytes (257.5 MiB), 9:00:14.352, mono AAC-LC at 44.1 kHz, with attached JPEG
cover, publication/narrator metadata, and exactly 52 manifest-named chapters;
evidence: strict `ffprobe` validation passed all chapter names/order/boundaries
to millisecond tolerance, beginning/middle/chapter-boundary/ending samples all
decoded cleanly, and beginning/middle/ending comparisons against the complete
MP3 reported 167.664–167.716 dB audio PSNR; Apple Books imported it as an
audiobook, displayed chapter 1 through chapter 52 including the complete final
tribute, reported nine hours remaining, and played six seconds normally before
being paused; next step: publish both binaries into the strict static bundle.

20260717-1503 — action: added and visually inspected the portable site handoff;
result: the homepage, book, audiobook, and new `reading-apps.html` page expose
ordinary direct EPUB/M4B links, existing PDF/MP3 fallbacks, and plain Apple
Books, Send to Kindle, Kobo, Google Play Books, generic audiobook-app, and
no-download website guidance; release mode requires structurally valid source
and copied artifacts and the generated `.htaccess` declares EPUB/M4B MIME
types; evidence: strict build published 53 MP3s and 2 portable files, strict
validation passed 103 HTML pages, 401 local references, and 59 search rows;
desktop 1280×720 and mobile 390×844 browser inspection showed readable stacked
actions with no horizontal overflow, and device help/site/independent-renderer
console logs had no warnings or errors; decision: retain literal same-origin
downloads and no user-agent sniffing or brittle deep links; next step: update
durable truth and run the full source/methodology check matrix.

20260717-1510 — action: completed the build-story verification and truth sweep;
result: a forced `make build-portable-editions RELEASE=1` rebuilt the exact
90.0 MiB EPUB and 257.5 MiB M4B and repackaged the strict site; evidence:
Python syntax compilation, 18 focused audiobook/portable tests, strict source
audio decode validation, M4B validation, official EPUBCheck, strict site
validation, active doc-web validation (39 entries/1,738 provenance rows/155
images), two companion bundle checks, and 19-page supplemental validation all
pass; README, audiobook/portable guidance, Onward runbook, infrastructure,
spec, state, coverage, and changelog now distinguish locally validated portable
artifacts from not-yet-public delivery; decision: leave Story 005 In Progress
with only formal `/validate`, deployment/public MIME-length-range proof, and
`/mark-story-done` outstanding; next step: hand off the completed build for
independent validation and deploy closeout.

20260717-1514 — action: ran `/align` after compiling the updated methodology
graph; result: the portable lane is aligned with One Canon, Many Experiences,
Accessible Reading, spec:4/C4 `climb`, the active Story 005 campaign, and the
new coverage rows; evidence: `make methodology-compile`, `make
methodology-check`, and `make skills-check` pass, no portable-specific AI eval
or ADR is warranted, and no completed story was invalidated; correction: the
sweep found and fixed stale C4 phase wording in this story and the pre-audio
Current Repo Reality paragraph in `AGENTS.md`; next step: formal validation and
public deploy verification remain the only closeout work.

20260717-1518 — action: performed the final implementation/diff audit; result:
closed the remaining visible-lineage gap by adding a warm source/archive note
to the EPUB opening and declaring the subtitle and public archive as EPUB
metadata, made forced builds regenerate the derived cover, and updated the
scout approval state; evidence: the final 94,390,319-byte EPUB contains the
visible note and `dc:source`, again passes EPUBCheck 5.3.0 with zero messages,
and its exact bytes were recopied into a strict site bundle that again passes
103-page/401-reference validation; final SHA-256 values are `5afacf6a005026cf91adb85d9c11c1bce57c8a4e974d60f3c72924cecd969bfb`
for the EPUB and `307ded9b41365aa49c916b90752e725b4ece5f5b618f3fdf4129a38399e571e6`
for the M4B, and the staged copies have identical byte lengths; `git diff
--check` is clean; next step: formal validation and deployment/public
verification.

20260717-1540 — action: ran formal `/validate` against Story 005 and the entire
tracked/untracked change set; result: all 11 acceptance criteria and every
substantive task are met with an overall A grade and `Close now`
recommendation; evidence: Python compilation, Ruff, 18/18 pytest tests,
`make test-audiobook`, `make test-portable-editions`, full 52-track/complete-MP3
decode validation, 52-chapter M4B validation, official EPUBCheck with zero
messages, strict 103-page/401-reference local site validation, active doc-web,
companion, supplemental, methodology, skill, and diff checks all pass; decision:
no ADR is needed because the formats remain inside the existing static
publishing boundary; next step: publish the exact validated bundle and require
public proof.

20260717-1546 — action: deployed and smoke-tested the portable release, then
hardened the deployer around a discovered false-success path; result: the full
bundle is live at `https://alain-lessard.copper-dog.com` and the reusable
Onward sequence is captured above; evidence: DreamHost accepted `.htaccess`,
`reading-apps.html`, the 94,390,319-byte EPUB, 269,966,138-byte M4B, and remote
manifest at `/home/onward_user/alain-lessard.copper-dog.com`; strict production
validation passed 103 HTML pages, 401 references, 59 search rows, all 53 MP3s,
and both portable files with exact MIME/length/`206` checks; desktop and 390px
mobile browser smoke confirmed literal handoff links, 52 cards, 53 players,
current asset version, no overflow, and no console warnings/errors. The first
sandboxed attempt could not resolve DreamHost and exposed that `run_sftp`
accepted EOF with unknown exit status; it now closes/waits for the child and
requires exit zero, with two focused regression tests and 20/20 total tests
passing; next step: `/mark-story-done`, then `/check-in-diff`.

20260717-1550 — action: ran `/mark-story-done` after current-tip validation and
production proof; result: Story 005 is Done with 16/16 top-level tasks, 11/11
acceptance criteria, all six Central Tenets, and all workflow gates complete;
evidence: dependencies Stories 003/004 are Done, evals are N/A, the work log
contains the build/app/deploy/public/browser evidence, the final 20-test suite,
Ruff, EPUBCheck, M4B, strict local site, source/companion/supplemental,
methodology, skill, and diff checks all pass, and the public release gate passed
after upload; outstanding: none; closure recommendation: `Close now`; next
step: `/check-in-diff`.
