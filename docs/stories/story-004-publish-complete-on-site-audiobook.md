---
title: "Publish the complete on-site audiobook"
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
category_refs:
  - "spec:4"
compromise_refs:
  - "C4"
input_coverage_refs:
  - "audiobook-scripts"
  - "family-site-reading-sections"
architecture_domains:
  - "audiobook content model"
  - "static family site"
  - "DreamHost media delivery"
roadmap_tags:
  - "reviewed-audio-files"
legacy_system: "script-only audiobook page with 52 reviewed local MP3 files not yet published"
---

# Story 004 — Publish the complete on-site audiobook

**Priority**: High
**Status**: Done
**Decision Refs**: `docs/ideal.md`, `docs/spec.md`,
`docs/infrastructure.md`, `docs/runbooks/onward-process-map.md`,
`tests/fixtures/formats/_coverage-matrix.json`, reference implementation
`/Users/cam/Documents/Projects/onward-to-the-unknown-website/audiobook/manifest.json`,
reference builders `modules/build_family_site.py` and
`modules/build_full_audiobook.py`, reference Story 011 and
`docs/runbooks/elevenlabs-audiobook.md`, and the live
`https://onward.copper-dog.com/audiobook.html` surface inspected on 2026-07-16;
none found after search for a repo-local audiobook ADR
**Depends On**: Story 003

## Goal

Publish the reviewed 52-track Alain Lessard audiobook as a first-class part of
the static family archive. Extend the canonical audiobook manifest from a
script handoff into an inspectable audio-asset contract, build one complete
audiobook from the ordered tracks, publish both the full-book and individual
MP3 files, add low-friction native players and downloads to the audiobook and
matching reading pages, and verify the deployed files as seekable production
media. Reuse the proven Onward pattern while fixing the gaps that matter for
this larger corpus: many tracks can belong to one reading entry, some tracks
span several entries, the full audiobook must not be optional at release time,
and long-form listening should resume gracefully.

## Acceptance Criteria

- [x] `audiobook/manifest.json` is the canonical ordered inventory for all 52
      reviewed tracks and records each track's title, script source, local MP3
      source, stable ASCII public path, duration, source lineage, and zero or
      more matching site entry ids without hand-maintained HTML links.
- [x] The manifest and loader support both many tracks on one reading entry
      and one track spanning several reading entries; the track 07–34 mapping
      to `chapter-001` and the multi-entry tracks are covered explicitly.
- [x] A maintained `make build-full-audiobook` command compiles the ordered
      track set with a manifest-configured inter-track pause, preserves a
      speech-appropriate mono output instead of upmixing to stereo, writes
      useful ID3 title/album/narrator metadata, and produces a duration within
      tolerance of the track sum plus configured pauses.
- [x] A strict audiobook validation command fails on missing, corrupt,
      duplicated, misordered, or mismatched chapter MP3s; it verifies all 52
      files decode, the full audiobook exists and decodes, public filenames are
      ASCII-safe, and the full duration is consistent with the manifest.
- [x] `make build-family-site` copies the individual MP3s and complete
      audiobook into stable `build/family-site/audiobook/` paths, records them
      in the build summary, and refuses a release-ready build when any declared
      track or the full audiobook is absent. Markdown remains under `script/`;
      no MP3 is duplicated or accidentally published beneath that script path.
- [x] `audiobook.html` leads with the complete audiobook player and a direct
      same-origin `Download complete audiobook` MP3 link labelled with its
      duration and human-readable file size, then lists all 52 tracks with
      track number, title, run time, native `<audio controls preload="none">`,
      download link, and exactly one plain `Read` link to the corresponding
      semantic reading section when one exists.
- [x] The main reading experience is organized by meaningful book sections,
      not printed-page routes or `Page N` labels. Multi-page narratives such as
      Part I, Henri Delphice Alain, and Moise are merged into one reading page;
      shared source chapters are split at story headings where that aligns with
      the audiobook tracks; non-narrative tables, figures, genealogy, front
      matter, and bibliography remain available in clearly titled reference
      sections so no source content is dropped.
- [x] Reading and companion-document pages show a compact, always-visible
      native listening bar at the top for the applicable track: play controls,
      track title, and run time appear without a disclosure click or a second
      nested panel, and the bar remains usable on mobile and without JavaScript.
      Any decorative audio cue is visibly a listening/headphones symbol rather
      than a second play control.
- [x] The homepage offers a clear audiobook entry point, keeps the primary
      `Start Reading` section ahead of the less-prominent companion documents,
      and reader-facing copy
      says that no app or account is needed while honestly identifying the
      ElevenLabs Multilingual v2 / Matilda AI narration.
- [x] A small progressive enhancement prevents multiple players from talking
      over one another and remembers useful playback positions locally so a
      listener can resume after reloading; native playback and downloads still
      work when JavaScript or storage is unavailable.
- [x] Focused regression coverage proves manifest validation, one-to-many and
      many-to-one entry mapping, full-audiobook duration math, asset copying,
      page rendering, fallback behavior, and resume/single-player JavaScript
      hooks without copying the real 740 MiB track set into test fixtures.
- [x] After deployment, the audiobook page, every individual MP3, and the full
      audiobook return successfully over HTTPS with `audio/mpeg`, non-zero
      content lengths, and byte-range support (`206` for a range request) so
      browser seeking works through DreamHost and Cloudflare.
- [x] `docs/spec.md`, `docs/methodology/state.yaml`,
      `tests/fixtures/formats/_coverage-matrix.json`, infrastructure/runbook
      docs, and the changelog describe reviewed and deployed audio truth rather
      than the former script-only state.

## Full-Book Assembly And Download Method

Follow Onward's deterministic assembly path, with Alain-specific completeness
and output improvements:

1. Treat the ordered tracks in `audiobook/manifest.json` as the sole assembly
   order; validate every declared MP3 before starting the merge.
2. Have `make build-full-audiobook` invoke a maintained Python wrapper around
   `ffmpeg`. As in Onward, pass each track as an input, generate the configured
   inter-track silence with `anullsrc`, and concatenate the resulting audio
   stream into one MP3. Onward uses a four-second manifest value; keep Alain's
   value configurable and listening-check representative transitions before
   fixing it.
3. Normalize only what concatenation requires. Preserve Alain's 44.1 kHz mono
   narration instead of copying Onward's forced stereo output, leave the 52
   reviewed source MP3s unchanged, and write ID3 metadata only to the generated
   complete-book file.
4. Use `ffprobe` and decode checks to confirm format, metadata, first and last
   content, and a duration equal to the track sum plus all declared pauses
   within a documented tolerance.
5. Keep the merged MP3 as an ignored, reproducible local artifact. The family-
   site build copies it to a stable same-origin path under
   `build/family-site/audiobook/` alongside the individual track files.
6. Publish both a native full-book player and a normal direct MP3 download link
   showing duration and file size. A release build and deploy verification must
   fail if this file is missing, empty, undecodable, incorrectly typed, or not
   publicly downloadable; chapter-only publication is not complete.

This is deliberately stricter than the current Onward deployment: Onward has
the merge script and manifest contract, but its live full-book section still
falls back to a placeholder when the generated file is absent.

## Out of Scope

- Regenerating or editorially changing the reviewed narration scripts or MP3s.
- Automating ElevenLabs credentials, uploads, or paid generation.
- Spotify, Apple Podcasts, Audible, podcast RSS, storefront distribution, or
  any other external publishing lane.
- A bespoke waveform player, transcript synchronization, sentence-level
  highlighting, or account-backed cross-device progress.
- A chapterized M4B edition, ZIP bundle, or cover-art redesign; these may be
  evaluated later after the required MP3 experience is shipped.
- Committing the approximately 740 MiB source MP3 corpus or generated full
  audiobook to Git; these remain ignored local/deploy artifacts with a tracked
  manifest and reproducible build path.

## Approach Evaluation

- **Simplification baseline**: The proven baseline is the Onward pattern: a
  tracked manifest, native browser audio controls, direct downloads, a
  deterministic `ffmpeg` merge, and static DreamHost delivery. No LLM call is
  needed for this deterministic plumbing. The build-story eval should first
  reproduce that minimum with small fixtures before accepting richer playback
  behavior.
- **Candidate A — copy Onward directly**: Lowest implementation effort and
  already proven publicly for individual tracks. It does not fit unchanged:
  Onward forbids duplicate `target_entry_id` values, conditionally tolerates a
  missing full audiobook, and upmixes its merged output to stereo. The live
  reference page inspected on 2026-07-16 still showed the full-audiobook
  placeholder rather than a player/download.
- **Candidate B — adapt the Onward manifest and native-player pattern**: Add
  explicit `target_entry_ids`, strict release completeness, mono full-book
  output, metadata, and lightweight local playback state while keeping native
  controls. This adds bounded deterministic behavior and directly addresses
  Alain's 52-track/39-entry shape.
- **Candidate C — external audio hosting or a custom JavaScript player**:
  Could reduce DreamHost bundle size or provide a richer playlist, but adds a
  second deployment/account boundary and more failure modes for relatives.
  It should only win if the static baseline fails measured size, seeking, or
  usability checks.
- **AI-only**: Not appropriate. An LLM cannot safely own binary integrity,
  ordered concatenation, manifest validation, static asset copying, or HTTP
  range verification.
- **Hybrid**: AI judgment is unnecessary for implementation. The already
  completed human/ASR review establishes content correctness; deterministic
  code should own packaging and publication.
- **Pure code**: A strong fit for manifest parsing, `ffprobe` validation,
  `ffmpeg` compilation, static rendering, asset copy, metadata, and deployment
  checks.
- **Repo constraints / prior decisions**: `spec:4` names reviewed audio as the
  remaining production-readiness gap. MP3s are intentionally ignored by Git,
  `build/family-site/` is the deploy source, and `scripts/deploy_static_site.py`
  already handles large ignored artifacts with a remote deletion manifest.
- **Existing patterns to reuse**: Onward's `onward_audiobook_manifest_v1`,
  `load_audiobook_catalog`, `build_full_audiobook`, native player cards,
  page-level `<details>` panels, duration probing, fixture-based tests, and
  DreamHost public delivery. Keep Alain's existing ASCII slug filenames and
  current site visual language rather than copying Onward's CSS wholesale.
- **Eval**: Compare candidates on manifest completeness, exact ordered duration,
  generated bundle size, mono/stereo output, native no-JS playback, duplicate
  page mappings, mobile/desktop usability, resume behavior, public `200`/`206`
  responses, and whether a missing full audiobook can still pass a release
  build. Candidate B is the working hypothesis, not a pre-approved result.

## Tasks

- [x] Inventory the reviewed local MP3 set from `audiobook/script/`, record the
      exact total size/duration and format profile, and preserve the existing
      filename-to-script pairing as the baseline fixture report.
- [x] Extend the generated audiobook manifest and its schema/version so each
      track declares expected local and public audio paths, probed duration,
      source ids, and explicit `target_entry_ids`; keep rebuilds from resetting
      reviewed audio metadata to `null`.
- [x] Add a focused audiobook catalog/validation module rather than putting all
      parsing, probing, compilation, and mapping logic into the already
      2,061-line `scripts/build_family_site.py`.
- [x] Add `scripts/build_full_audiobook.py` and a Make target that use the
      canonical track order, insert the configured pause, emit mono MP3 with
      appropriate ID3 metadata, refuse accidental overwrite unless requested,
      and fail clearly when `ffmpeg`/`ffprobe` or a source track is missing.
- [x] Add a strict local audiobook validator for the 52 chapter files and full
      output, including decode checks, hash-based duplicate detection, duration
      math, sequential numbering, script/audio pairing, and ASCII public paths.
- [x] Extend the family-site build to copy declared audio assets, expose a
      full-book player/download, render 52 track cards with run times and
      read-this-section links, inject all matching players into main-book and
      supplemental pages, and add a homepage audiobook entry point.
- [x] Replace raw doc-web page/chapter navigation with a derived semantic
      reading-section model that groups multi-page narratives, splits shared
      story chapters, preserves all source HTML/provenance in named reference
      sections, emits stable section routes, and gives each applicable audio
      track exactly one reading target without changing the v4 audio schema.
- [x] Replace entry-page `<details>` listening panels with one compact native
      listening bar per track-aligned section and companion page; simplify each
      audiobook card to one `Read` action and remove page-number wording from
      the reader contents, search index, cards, and navigation.
- [x] Add focused regression and release-validation coverage for semantic
      grouping, source-content coverage, single read targets, absence of page-
      number navigation, compact no-disclosure audio bars, and unchanged table,
      figure, scan-link, and companion-document coverage.
- [x] Restrict the existing script publisher to Markdown files so the current
      blanket directory copy cannot leak or duplicate MP3s under the public
      `script/` path; make validation reject that stale layout.
- [x] Add a small versioned audio JavaScript asset that pauses other players,
      persists playback positions with guarded `localStorage`, avoids restoring
      positions near the end of a track, and leaves native controls functional
      when unavailable.
- [x] Add focused small-fixture regression tests for the catalog, full-book
      builder, site renderer, multiple-track/multiple-entry mappings, and
      playback hooks; add a maintained Make target for these tests because this
      repo has no generic `make test` or `make lint` targets.
- [x] Expand `scripts/validate_family_site.py` to require the expected audio
      page/panels/assets and to distinguish a normal development build from a
      strict release/deploy build where all 53 MP3 outputs are mandatory.
- [x] Update `scripts/deploy_static_site.py` only where needed to preserve
      large-media timeouts, stale-file deletion, and content-type-safe paths;
      do not create a second uploader or external host without measured need.
- [x] Add a public verification command/report that checks the audiobook HTML,
      all 52 chapter assets, the full audiobook, MIME types, content lengths,
      and representative HTTP byte ranges after deployment.
- [x] Update `README.md`, `docs/infrastructure.md`, the Onward process map,
      `docs/spec.md`, `docs/methodology/state.yaml`,
      `tests/fixtures/formats/_coverage-matrix.json`, and `CHANGELOG.md` after
      the implementation changes the documented audio reality.
- [x] Check whether the chosen implementation makes the script-only audiobook
      cards, `audio_path: null`, or duplicated manifest-reading code redundant;
      remove them instead of retaining parallel audio paths.
- [x] Run required checks for touched scope:
  - [x] `python -m py_compile` for every changed Python module.
  - [x] The new focused audiobook test target.
  - [x] `make build-audiobook-script` and verify it preserves reviewed audio
        manifest fields and all 52 script/audio pairings.
  - [x] `make build-full-audiobook` and inspect format, metadata, duration,
        first/last track boundaries, and representative chapter transitions.
  - [x] `make build-family-site` and `make validate-family-site` in strict
        release mode.
  - [x] `make doc-web-validate-active`, `make validate-companion-doc-web`,
        `make validate-supplemental-docs`, and `make methodology-check`.
  - [x] Browser-check desktop and mobile audiobook, multi-track reading, and
        companion pages with native playback, single-player behavior, resume,
        downloads, and JavaScript disabled.
  - [x] Deploy with `make deploy-static`, then run the public 53-asset and range
        verification before declaring the story complete.
- [x] If evals or goldens changed: not expected; record the fixture/build/public
      verification in the story closeout rather than creating an AI eval.
- [x] Verify Central Tenets:
  - [x] T0 — Traceability: every player and downloadable MP3 comes from the
        manifest and retains script/source-entry lineage.
  - [x] T1 — AI-First: narration is already AI-assisted; packaging remains
        deterministic where code is the correct tool.
  - [x] T2 — Eval Before Build: the Onward baseline and its live missing-full-
        audiobook gap are recorded before choosing the Alain implementation.
  - [x] T3 — Fidelity: no narration content changes; track order and complete
        boundaries remain verified.
  - [x] T4 — Modular: audio catalog/build logic stays outside the site-builder
        monolith and the manifest prevents hardcoded track HTML.
  - [x] T5 — Inspect Artifacts: local MP3s, merged output, generated pages,
        browser behavior, and deployed byte-range responses are all inspected.

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

- **Owning module / area**: The repo-owned audiobook manifest and a focused new
  audiobook catalog/build module own binary truth; `scripts/build_family_site.py`
  consumes that contract for UI and copying; the existing deploy helper owns
  publication.
- **Methodology reality**: `spec:4` and C4 now distinguish the locally reviewed
  release bundle from the still-pending public deployment. The active
  `campaign:reviewed-audio-files` is in progress, and the coverage matrix owns
  separate reviewed-track, complete-audiobook, and built-site-audio rows backed
  by the new strict validators.
- **Substrate evidence**: `audiobook/script/` contains 52 Markdown files and 52
  correspondingly named MP3s totaling approximately 740 MiB. The MP3 audit on
  2026-07-16 verified unique files, clean decoding, correct openings/endings,
  and a complete corrected track 52. `audiobook/manifest.json` already has 52
  ordered script/source rows. `scripts/build_family_site.py` already builds
  `audiobook.html`; `scripts/deploy_static_site.py` already deploys the entire
  generated bundle. `ffmpeg` and `ffprobe` are available locally.
- **Data contracts / schemas**: Evolve
  `alain_lessard_audiobook_manifest_v3` to a new backward-intolerant version or
  add strictly validated optional fields with an explicit compatibility path.
  The contract needs `audio_path`, `public_audio_path`, `duration_seconds`,
  `target_entry_ids`, full-audiobook metadata, and release completeness state.
  No `schemas.py` exists in this repo; validation belongs in the focused
  audiobook module and fixture tests.
- **File sizes**: `scripts/build_family_site.py` is 2,061 lines and must not
  absorb the full catalog/compiler implementation; `scripts/validate_family_site.py`
  is 708 lines; `scripts/deploy_static_site.py` is 350 lines;
  `scripts/build_audiobook_script.py` is 838 lines after the reviewed-script
  work; `audiobook/manifest.json` is 766 lines; `Makefile` is 88 lines;
  `docs/infrastructure.md` is 139 lines; `docs/spec.md` is 119 lines;
  `docs/methodology/state.yaml` is 84 lines; and the coverage matrix is 80
  lines. New binary/catalog logic should start in a focused module with focused
  tests.
- **Decision context**: Reviewed this repo's ideal, spec, state, graph, coverage
  matrix, Story 003, infrastructure and Onward process runbooks. Reviewed the
  Onward reference manifest, full-audiobook builder, site catalog/render/copy
  path, regression tests, Story 011, audiobook runbook, public audiobook page,
  and public MP3 byte-range behavior. No repo-local audiobook ADR exists. A new
  ADR is not required unless implementation chooses external hosting, a new
  public schema shared with other repos, or a custom player architecture.

## Files to Modify

- `docs/stories/story-004-publish-complete-on-site-audiobook.md` — execution
  record and closeout evidence (new file)
- `audiobook/manifest.json` — 52-track and full-book audio contract (766 lines)
- `scripts/build_audiobook_script.py` — preserve/generated reviewed audio
  fields while rebuilding scripts (838 lines)
- `scripts/audiobook.py` — focused manifest, probing, validation, entry-mapping,
  and shared audio model (new file; exact name may be refined during build)
- `scripts/build_full_audiobook.py` — deterministic full-book compiler and CLI
  (new file)
- `scripts/build_family_site.py` — consume catalog, copy assets, and render
  audiobook/home/entry surfaces without owning parsing/compilation (2,061 lines)
- `scripts/validate_family_site.py` — local/release audio assertions (708 lines)
- `scripts/deploy_static_site.py` — only narrowly scoped large-media/public
  verification support if current generic deployment proves insufficient (350 lines)
- `assets` generated by `scripts/build_family_site.py` — small audio playback
  enhancement and styling (currently emitted from the site builder)
- `tests/test_audiobook.py` and `tests/test_build_full_audiobook.py` — small
  synthetic/fixture coverage (new files)
- `Makefile` — full-book build, audio validation, and focused test targets (88 lines)
- `README.md`, `docs/infrastructure.md`, `docs/runbooks/onward-process-map.md`,
  `docs/spec.md`, `docs/methodology/state.yaml`,
  `tests/fixtures/formats/_coverage-matrix.json`, and `CHANGELOG.md` — durable
  truth updates after implementation

## Redundancy / Removal Targets

- Script-only audiobook cards that link to Markdown after reviewed MP3s become
  the primary listener surface.
- `audio_path: null` rows and any hand-edited audio links that the generated
  manifest can own.
- Parallel manifest parsing inside the site builder once the focused audiobook
  catalog exists.
- Onward's permissive "full audiobook will appear here" release behavior; this
  story requires the declared full audiobook before deployment can pass.
- Stereo upmixing of mono narration in the merged output.

## Notes

- This is a new story rather than a reopened Story 003 because Story 003's
  success boundary was the doc-web site and script handoff. Story 004 owns new
  binary artifacts, compilation, media UI, large-file deployment, and public
  seekability validation.
- The Onward reference remains the template, not a code dependency. Copy the
  proven contract and behavior deliberately into Alain's simpler static
  builder rather than introducing a cross-repo runtime import.
- The live Onward check on 2026-07-16 returned `200` for
  `audiobook.html`; chapter MP3s returned `audio/mpeg`, `Accept-Ranges: bytes`,
  and `206` for a 1 KiB range request. The live full-audiobook section still
  showed a future placeholder because the generated full MP3 was absent. Alain
  should keep the proven chapter delivery while making full-book completeness
  a release gate.
- The source MP3s are mono, 44.1 kHz, approximately 192 kbps, and total
  8 hours 58 minutes 32 seconds / 739.66 MiB. A full-book output should not
  become larger by
  copying Onward's stereo normalization blindly. Measure output quality and
  size before fixing an encoding preset.
- A chapterized M4B could improve third-party audiobook-app navigation, but it
  is intentionally deferred until the family-first browser/MP3 lane is shipped
  and observed.

## Plan

1. **Lock the baseline and tests first (S).** Add small synthetic fixtures and
   standard-library tests in `tests/test_audiobook.py` and
   `tests/test_build_full_audiobook.py`, plus a focused Make target. Cover the
   schema, sequential/duplicate/path failures, one-to-many and many-to-one
   entry mappings, duration math, source/public asset separation, missing-full-
   book release failure, and a tiny two-track `ffmpeg` merge. Done means the
   new tests express the required behavior and fail against the current
   script-only implementation without needing the 740 MiB corpus.
2. **Establish one audio contract (M).** Add `scripts/audiobook.py` for typed
   manifest loading, stable ASCII public-path checks, `ffprobe` metadata,
   hashing/duplicate checks, entry mapping, and development-versus-release
   completeness. Evolve `audiobook/manifest.json` and
   `scripts/build_audiobook_script.py` so all 52 rows declare deterministic
   source/public MP3 paths, durations, and `target_entry_ids`, while rebuilds
   preserve or refresh reviewed audio metadata instead of resetting it to
   `null`. Map `companion:*` targets explicitly and leave the manual preamble
   without a reading-page target. Done means a script rebuild retains all 52
   pairings and strict validation reports the measured 8:58:32 mono corpus.
3. **Build the complete audiobook deterministically (M).** Add
   `scripts/build_full_audiobook.py` and `make build-full-audiobook`, adapting
   Onward's `ffmpeg` input/silence/concat filter for 44.1 kHz mono output and
   ID3 metadata. Keep the pause in the manifest, listening-check representative
   short and long transitions before finalizing its value, refuse overwrite
   without `FORCE=1`, and verify the output with `ffprobe`. Done means the
   ignored full-book MP3 decodes and its duration matches 52 tracks plus 51
   configured gaps within tolerance.
4. **Publish the listening surfaces without parallel paths (L).** Make
   `scripts/build_family_site.py` consume the focused catalog, copy tracks once
   to `audiobook/tracks/` and the merged file to its stable full-book path,
   restrict `write_audio_scripts` to Markdown, and record audio counts/bytes in
   the build summary. Replace script cards with the full-book player/download,
   52 native track players, all matching reading/companion-page disclosures,
   and the homepage entry point. Generate a small versioned audio JavaScript
   asset for single-player behavior and guarded local resume. Done means no
   MP3 remains under public `script/`, every declared target page exposes every
   applicable track, and native controls/downloads survive JavaScript being
   disabled.
5. **Make incomplete audio undeployable (M).** Extend
   `scripts/validate_family_site.py` with strict release mode and audio-aware
   local/public checks: 53 expected files, decode/duration consistency, HTML
   links, MIME, content length, and representative byte ranges. Wire explicit
   Make targets so `deploy-static` cannot upload a release bundle that lacks
   the complete audiobook. Reuse `scripts/deploy_static_site.py` unchanged
   unless measured large-file behavior proves a narrow timeout or verification
   adjustment is necessary. Done means the formerly passing zero-player
   baseline fails release validation for the right reasons.
6. **Exercise and inspect the real local corpus (L).** Run the focused tests,
   compile checks, script rebuild, strict audio validation, full-book build,
   site build, and all existing doc-web/companion/supplemental/methodology
   checks. Inspect full-book metadata, first/last content, representative
   transitions, generated HTML, desktop/mobile layout, no-JavaScript playback,
   downloads, single-player behavior, and resume. This step may create large
   ignored artifacts but must not change narration content.
7. **Move durable truth only after evidence (S).** Update `README.md`,
   `audiobook/README.md`, `docs/infrastructure.md`, the Onward process map,
   `docs/spec.md`, `docs/methodology/state.yaml`, the coverage matrix, and
   `CHANGELOG.md` to distinguish reviewed source tracks, generated full-book
   audio, built site assets, and deployed public truth. Recompile the graph and
   keep Story 004 `In Progress` at build handoff.
8. **Defer external release proof to validation/closeout.** The build-story
   pass prepares and locally verifies the release bundle. DreamHost upload and
   the public 53-asset/range sweep remain the next `/validate` and closeout
   boundary unless the user separately asks to deploy during implementation.
9. **Replace print-page navigation with semantic reading sections (L).** Add a
   focused `scripts/reading_sections.py` model that consumes the canonical
   doc-web entry HTML plus the audiobook track-to-source mapping. Group the
   early multi-page narratives and whole-part tracks, split source entries that
   contain several independently titled stories, and carry every unpaired
   source block into a plainly titled front-matter, genealogy, personal-record,
   or bibliography section. The site builder should render stable semantic
   routes, source-scan unions, previous/contents/next navigation, book contents,
   homepage cards, and search rows from that derived model. Existing raw doc-web
   data remains the provenance contract; the v4 audio manifest does not need a
   schema change. Done means tracks 04, 05, 06, 37, 39, 41, and 46 each expose
   exactly one `Read` target, no reader-facing card or search result is titled
   `Page N`, and table/figure/text coverage remains unchanged.
10. **Flatten entry listening UI and verify the revised experience (M).** Replace
    the entry `<details>` panels with a compact native audio bar that shows the
    track title, run time, controls, and download action without a disclosure.
    Update fixture tests and the release validator before rebuilding the real
    site, then browser-check desktop/mobile audiobook, Part I, Moise, a split
    multi-story section, a reference-only section, and both companions. Done
    means one click starts native playback from the visible bar, mobile layout
    does not overflow, JavaScript remains optional, and source/reference
    material is still discoverable.

Impact/risk: the main blast radius is the now-2,456-line site builder, its clean-
directory rebuild, and the current 39-row search/navigation contract. Keep the
new semantic grouping in a focused module rather than growing the renderer
again, and exercise it with small source-block fixtures before changing the
real bundle. The ignored source
MP3s mean a fresh checkout can still build scripts in development mode, while
strict release mode must fail honestly without the local reviewed assets. No
new package dependency, ADR, external host, or schema consumer is required;
choosing any of those would be a new human-approval blocker. The graph/state
remain in `spec:4` / `C4`, and coverage records the reviewed tracks, complete
audiobook, published media, and derived semantic-reading manifest only after
their validators and artifacts exist.

## Work Log

20260716-1528 — action: created the next audiobook publication story from the
reviewed 52-track checkpoint and Onward reference audit; result: packaged the
proven manifest/native-player/full-book pattern plus Alain-specific one-to-many
mapping, strict completeness, mono output, resume, and public range validation;
evidence: local Alain corpus has 52 paired MP3s, Onward Story 011 and builders
define the baseline, and the live Onward page serves individual seekable MP3s
while its full-audiobook asset remains absent; next step: run `/build-story`
against Story 004 and select the bounded implementation through its fixture and
bundle-size eval.
20260716-1540 — action: completed build-story exploration, substrate check, and
eval-first plan without changing implementation code; result: Story 004 closes
the named `spec:4` / `C4` gap, Story 003 and all 52 reviewed sources are present,
`ffmpeg`/`ffprobe` are available, and no ADR blocks the adapted Onward approach;
evidence: fresh probes found 52/52 readable MP3s, all MP3/44.1 kHz/mono/192 kbps,
775,585,234 bytes and 32,312.352 seconds (8:58:32), with seven multi-source
tracks and 28 tracks targeting `chapter-001`; the current renderer reports 52
null `audio_path` values, 52 script links, zero MP3 links, and zero `<audio>`
elements, yet `make validate-family-site` passes; surprise: the blanket script
directory copy has already duplicated all 52 ignored MP3s under
`build/family-site/script/`, contributing to a 1.6 GiB bundle despite exposing
no player; decision: adapt Onward through a focused Alain audio module, strict
release mode, mono merge, and canonical `audiobook/` public paths, while keeping
the full corpus out of fixtures and Git; next step: obtain human approval for
the written plan, then set the story In Progress and implement tests first.
20260716-1622 — action: implemented the approved adapted-Onward audiobook
release path and exercised it against the real corpus; result: manifest v4 now
owns 52 ordered source/public MP3 pairings and entry mappings, the focused
catalog validates and decodes them, the deterministic compiler produced a
44.1 kHz mono 128 kbps full audiobook with ID3 metadata, and the static site
publishes 53 audio assets without duplicating MP3s beneath `script/`; evidence:
strict audio validation reports 52/52 tracks, 32,312.352 seconds and
775,585,234 bytes, while the complete artifact is 32,414.352 seconds and
518,630,750 bytes, exactly adding 51 two-second gaps; decoded first/last
60-second comparisons correlate 0.999933/0.999740 with tracks 01/52, and three
representative boundaries contain the configured pause; the strict site build
reports 53 audio files and validation passes across 45 HTML pages, 380 local
references, and 41 search rows; focused tests pass 8/8, including duplicate
audio rejection, exact duration math, fallback rendering, and one-copy asset
publication; Python compilation, doc-web, companion, supplemental, methodology,
and `git diff --check` all pass;
desktop and mobile browser inspection found 53 players/52 cards on the
audiobook page, all 28 chapter-001 listening panels, companion panels, and no
horizontal overflow; surprise: the in-app browser could inspect native players
and downloads but could not automate playback through the browser's native
media-control shadow UI, so actual resume/single-player/no-JavaScript playback
and public byte-range behavior remain explicit validation checks; decision:
leave Story 004 In Progress and do not deploy during build-story; next step:
run `/validate`, including local playback behavior, then deploy and execute the
public 53-asset MIME/content-length/range sweep before closeout.
20260716-1642 — action: incorporated the user's local-preview feedback as a
coherent Story 004 scope correction and re-opened the build gate before code;
result: the revised target replaces print-page reading routes with semantic
sections aligned to audiobook tracks where appropriate, retains separately
named reference material where no audio exists, makes every track expose at
most one plain `Read` action, and replaces nested entry disclosures with a
visible compact audio bar; evidence: the current built site still emits 21
`page-###.html` routes, seven audiobook tracks have multiple Read actions
(tracks 04/05/06 have five/seven/three), `chapter-001.html` contains 28 nested
audio disclosures, and 67 entry disclosures exist overall; substrate check:
the accepted 39-entry doc-web bundle, block ids, headings, source-scan arrays,
and v4 track `target_entry_ids` are sufficient to derive the new structure
without changing source HTML or the audio schema; surprise: an exact forced
52-page count would omit non-audio front matter, genealogy, personal records,
and bibliography, so the plan uses roughly track-aligned narrative sections
plus a few clearly named reference sections instead of dropping material;
decision: add a focused reading-section model rather than another large block
inside the 2,456-line site builder; next step: obtain approval for the written
scope-delta plan, then add failing grouping/audio-bar fixtures before
implementation.
20260716-1724 — action: implemented the approved semantic reader and compact
audio-bar scope correction, then rebuilt and inspected the strict local release;
result: the 39 canonical source entries now produce 57 meaningful main-book
sections (49 track-aligned narratives and 8 named references), each applicable
track has exactly one Read destination, Part I and Moise are coherent multi-scan
sections, and all nested audio disclosures are gone; evidence: the derived
manifest assigns all 1,737 source block ids exactly once, focused tests pass
10/10, strict site validation passes across 102 HTML pages, 398 local references,
and 59 search rows, and strict audio validation decodes all 52 tracks plus the
9:00:14 complete audiobook; desktop and 390 px browser inspection found no
horizontal overflow, 57 section routes and no page-number links in the contents,
one compact bar on Part I/Moise, eight Personal Records tables with no invented
audio, working legacy redirects, and no console warnings/errors; surprise: an
exact 52-section total was neither necessary nor faithful because eight
non-narrated reference groupings must remain readable; decision: retain those
references alongside the track-aligned stories, keep legacy page/chapter URLs
as redirects rather than navigation, and leave Story 004 In Progress for the
separate validation/deploy/public byte-range gate; next step: user review of the
local preview, then `/validate` and deployment when approved.
20260716-1729 — action: reopened the visual build gate after the user's preview
feedback on the compact listening bar; result: the decorative black circle and
triangle is correctly identified as ambiguous because it looks like a second
play button beside the browser's real native play control; evidence: the
generated markup uses `listen-icon` with a triangle character and the screenshot
shows two nearly identical play affordances in one row; decision: reuse the
headphones metaphor from Onward's audiobook design, but render it as a quiet
tonal badge rather than another button; next step: add a regression assertion,
rebuild, and inspect the bar at desktop and mobile widths.
20260716-1732 — action: replaced the ambiguous decorative triangle with the
Onward-derived headphones metaphor and rebuilt the strict release bundle;
result: the listening bar now uses a small burgundy headphones badge while the
browser's native control is the only play affordance; evidence: the regression
suite passes 10/10 and rejects the old triangle character, strict site
validation passes across 102 HTML pages, 398 local references, and 59 search
rows, and desktop/mobile browser inspection found one headphones SVG, one native
player, zero decorative triangles, zero disclosures, no overflow, and no console
warnings/errors; decision: keep the quiet tonal badge rather than Onward's
larger section-title treatment because this bar is intentionally compact; next
step: user preview, followed by the existing `/validate` and deployment gate.
20260716-1733 — action: reopened the homepage ordering acceptance after the
user's preview feedback; result: companion documents are correctly identified
as secondary to the main `Start Reading` path; evidence: `render_home` currently
inserts the companion section immediately before `Start Reading`; decision:
retain the same cards and links but move the complete companion section below
the primary reading choices; next step: make the validator enforce the priority,
reorder the generated markup, and inspect desktop/mobile home layouts.
20260716-1735 — action: moved the full companion-document section below the
homepage `Start Reading` section and rebuilt the strict release; result: the
main book is now the clearer primary path while both companion HTML/PDF cards
remain intact immediately afterward; evidence: strict validation passes across
102 HTML pages, 398 local references, and 59 search rows and now enforces the
section order; desktop and 390 px browser inspection confirms `Start Reading`
precedes `Companion Documents`, with no horizontal overflow or console
warnings/errors; decision: preserve the existing companion content and styling,
changing only its information-hierarchy position; next step: user preview,
followed by the existing `/validate` and deployment gate.
20260716-1800 — action: deployed the approved strict Story 004 bundle to the
production DreamHost path and verified the live release; result: the 2.0 GiB
site, 52 individual tracks, and 9:00:14 complete audiobook are publicly
available at `alain-lessard.copper-dog.com`; evidence: SFTP completed against
`/home/onward_user/alain-lessard.copper-dog.com`, updated the remote manifest,
and removed two obsolete script filenames; the strict public validator passed
102 HTML pages, 398 local references, 59 search rows, and all 53 MP3s for
`audio/mpeg`, positive content length, and `206` byte-range behavior; browser
inspection confirmed asset version `20260716-semantic-reader-r2`, Start Reading
before Companion Documents, 52 track cards plus the full-book player, one
headphones badge/native player on the sampled reading section, no disclosures,
no overflow, and no console warnings/errors; surprise: the first deploy attempt
stopped before upload because Make's bundled Python lacked the pinned `pexpect`
dependency even though the shell Python had it, so the dependency was installed
into the interpreter Make actually uses and the same guarded deploy was rerun;
decision: record production deployment as complete while leaving Story 004 In
Progress for the still-explicit manual native-playback/resume/no-JavaScript
validation and formal `/mark-story-done` closeout; next step: run `/validate`.
20260716-1818 — action: completed the fresh `/mark-story-done` audit and closed
Story 004; result: every task, acceptance criterion, Central Tenet, and workflow
gate is complete; evidence: production playback advanced without media errors,
resume restored the saved position after reload, starting track 02 paused track
01, the MP3 media download completed, and disabling JavaScript left the native
player, direct source, and download available with no overflow; the temporary
browser playback state and JavaScript override were cleared afterward; the
closeout suite passed 10/10 focused tests, Python compilation, the strict
57-section/53-audio site rebuild, full decode validation for 52 tracks plus the
9:00:14 complete audiobook, doc-web/companion/supplemental checks, and strict
local/public validation across 102 HTML pages, 398 references, 59 search rows,
and all 53 public MP3 range responses; the bundled runtime did not include
`pytest` or `ruff`, but the system project tools passed `python -m pytest tests/`
(10/10) and `python -m ruff check modules/ tests/` in addition to the maintained
repo-specific suite; the landing audit added `make deploy-deps` so future
deployments install `pexpect` into Make's selected interpreter instead of
repeating the observed environment mismatch; completion report: tasks all complete,
acceptance criteria 13/13 met, Tenets verified, eval updates N/A, outstanding
none; closure recommendation: Close now; next step: `/check-in-diff`.
