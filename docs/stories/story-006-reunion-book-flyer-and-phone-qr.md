---
title: "Reunion book flyer and phone QR card"
status: "Done"
priority: "High"
ideal_refs:
  - "Website Family Archive"
  - "Accessible Reading"
  - "One Canon, Many Experiences"
  - "Trustworthy Source Lineage"
spec_refs:
  - "spec:4"
  - "C4"
adr_refs: []
depends_on:
  - "story-003-doc-web-powered-onward-style-site"
  - "story-004-publish-complete-on-site-audiobook"
  - "story-005-portable-ereader-and-chaptered-audiobook"
category_refs:
  - "spec:4"
compromise_refs:
  - "C4"
input_coverage_refs:
  - "doc-web-html-bundle"
  - "family-site-build"
  - "complete-audiobook"
  - "portable-epub-edition"
  - "family-site-portable-assets"
architecture_domains:
  - "offline family outreach"
  - "static family site"
roadmap_tags:
  - "reunion-outreach"
legacy_system: "word-of-mouth sharing without a readable printed or phone-display handoff"
---

# Story 006 — Reunion book flyer and phone QR card

**Priority**: High
**Status**: Done
**Decision Refs**: `docs/ideal.md`, `docs/spec.md`,
`docs/infrastructure.md`, `docs/runbooks/onward-process-map.md`,
`tests/fixtures/formats/_coverage-matrix.json`, and the accepted main-book
`doc-web` headings; none found after search for a repo-local print-design or QR
ADR, and none is needed for this bounded derivative
**Depends On**: Stories 003, 004, and 005

## Goal

Create a warm, highly legible US Letter (8.5 × 11 inch) reunion flyer that can
be taped to an RV and lets an older family audience immediately understand that
the Alain Lessard family history is online free of charge. The flyer provides a
large, reliably scannable QR code, a large typeable URL, the book title, a
source-backed set of prominent family names, and plain-language read/download/
listen choices. Create a companion phone-display image dominated by the same QR
code, title, and URL so the archive can be shared while walking around the
reunion.

## Acceptance Criteria

- [x] A maintained deterministic command builds a one-page portrait US Letter
      PDF at exactly 8.5 × 11 inches, a high-resolution PNG print preview, a
      reusable standalone QR PNG, and a portrait phone-display PNG from one
      tracked content/design contract; generated artifacts live under
      `output/outreach/` and no raw or canonical publication input is changed.
- [x] The finished story contains a self-sufficient cross-book replication
      handoff so an AI working in the *Onward to the Unknown* repository can
      make a visibly matching flyer and phone image without inspecting this
      repository's implementation. The handoff separates invariant design
      rules from Alain-specific content and records every final value rather
      than leaving references such as `same as source` or `use the screenshot`.
- [x] A tracked `outreach/reunion-flyer-design-spec.md` mirrors the story's
      final production record in copyable detail: canvas and export sizes,
      margins/grid, component geometry, palette, fonts, type sizes/line heights,
      QR parameters, copy slots and overflow rules, commands, dependency/font
      versions, input/output paths, and validation procedure. The story remains
      the human-readable authority; the design spec is the portable handoff.
- [x] The flyer visibly leads with `Alain Lessard` and the subtitle `Our First
      Ancestors and A Compilation of Stories of Their Descendants`, followed by
      a plain headline such as `Our family history is online — free` rather
      than repository, build, or format jargon.
- [x] The letter flyer includes the canonical 1987 front-cover image from the
      accepted `doc-web` bundle at a recognizable size without cropping,
      stretching, or manual retouching. Its source path and SHA-256 are recorded
      in the outreach contract/build evidence; the phone QR card remains
      deliberately cover-free and QR-dominant.
- [x] The printed cover and QR have the same height so the familiar cover has
      equal visual presence in the central row. The QR remains at least four
      inches, its module/quiet-zone geometry is unchanged, and both elements
      stay within the 36-point safe margins without overlap.
- [x] The flyer says, in large plain language, that relatives can read and
      search the book online, download the searchable PDF or eBook, and listen
      to the complete audiobook, and includes a short camera instruction near
      the code.
- [x] The default family-name band includes the prominent source-backed names
      `Alain / Allain`, `Lessard / Lessart`, `L'Heureux`, `Reindl`, `Prentice`,
      `Sevigny`, `Adrian`, `Toews`, `Menzies`, `Marsollier`, `Strasser`, and
      `Folley`; spelling, variants, inclusion, and readable layout are checked
      against the accepted main-book headings before the final print proof.
- [x] Both visual artifacts show `alain-lessard.copper-dog.com` as selectable/
      readable text while their QR codes encode the canonical HTTPS homepage
      `https://alain-lessard.copper-dog.com/`; no shortened or third-party
      redirect URL is introduced.
- [x] The QR uses a plain black-on-white module field, an intact quiet zone, and
      enough physical/display size and error correction to remain easy to scan.
      The print proof scans from at least 3 and 6 feet in bright and shaded
      conditions on two available phone camera implementations; the phone image
      scans from a second device at normal and high screen brightness.
- [x] The design is usable for a primarily 70s–80s audience: high contrast,
      matte-print-friendly color, no essential text below 18 pt, body/action
      text at least 22 pt where space permits, a substantially larger headline
      and URL, generous spacing, no dense paragraphs, and no reliance on color
      or icons to convey the available formats.
- [x] The print and phone designs use a true white `#ffffff` background. The
      Alain website palette supplies restrained accents—ink `#22231f`, deep
      green `#143d3b`, secondary green `#1f5b55`, red `#8d2f23`, gold
      `#c1912f`, muted text `#626861`, and light rule `#d8ddd5`—but the flyer
      does not reproduce the site's pale page background `#f7f8f6` or any
      large solid-color panel. Color is limited to type, thin rules, small
      marks, or similarly low-coverage details suitable for a home laser
      printer; all meaning and hierarchy remain clear in grayscale.
- [x] PDF inspection proves one page, exact media size, embedded/selectable
      title and URL text, no clipping, no unintended transparency/font fallback,
      and a crisp QR. The PDF is rendered to an image and visually inspected at
      full page and actual print scale; one physical letter-size proof is also
      inspected on the intended printer before final handoff.
- [x] The phone image fits a common 1080 × 1920 portrait screen without cropping
      or tiny text, devotes most of its useful area to the QR code, and remains
      understandable when shown as a full-screen photo with the book name and
      typeable URL still visible.
- [x] Before final generation, the canonical public homepage is freshly
      verified over HTTPS and the QR is decoded back to that exact URL. The
      landing page visibly offers online reading, PDF/eBook access, and complete
      audiobook access; if the homepage no longer does so, fix or choose a
      stable first-party landing route before printing.
- [x] Focused fixtures verify exact page dimensions, pixel dimensions, required
      wording, canonical URL, QR decode round-trip, minimum quiet zone/contrast,
      output inventory, and failure on missing or inconsistent content inputs.
- [x] The final handoff includes the print-ready PDF, print preview, phone image,
      and standalone QR image plus short practical guidance: print at 100% on
      matte white paper, mount near eye level, avoid window glare, and keep a
      second copy or weather sleeve available.
- [x] Before Story 006 can be marked Done, its `Final Production Record` and
      Work Log explain which candidate was selected, why it won at actual size,
      the exact generation and validation commands used, any manual judgment or
      post-processing performed, final artifact paths and SHA-256 hashes, and
      physical/digital scan results. Another AI can reproduce the composition
      from those entries rather than reverse-engineering finished pixels.

## Out of Scope

- Redesigning the family website, repackaging the PDF/EPUB/audiobook, changing
  the book text, or creating a new public URL-shortening service.
- A crowded reunion program, full family tree, exhaustive surname index,
  biography, contact directory, donation request, advertising, or commercial
  promotion.
- Sending the flyer to a print shop, purchasing materials, mounting it on the
  RV, or publishing personal phone/email details.
- Custom analytics or tracking parameters in the QR destination. The canonical
  first-party homepage remains the durable and privacy-respecting destination.
- Making QR scanning the only route; the literal hostname is a required equal
  fallback.

## Approach Evaluation

- **Simplification baseline**: A single design-generation call could make an
  attractive mockup, but it cannot reliably guarantee exact letter geometry,
  text spelling, a decodable URL, quiet-zone integrity, selectable PDF text, or
  reproducible print/phone outputs. First compare a simple deterministic layout
  with one bounded visual mockup before selecting the final composition.
- **Candidate A — HTML/CSS print page rendered to PDF and PNG**: Familiar layout
  control, easy text accessibility, and good browser previewing, but browser
  print margins, font availability, and exact raster output need explicit
  pinning and validation.
- **Candidate B — ReportLab vector scene graph and QR (approved direction)**:
  Use the locally available ReportLab `Drawing`/PDF renderers and vector QR
  widget with embedded Bitstream Vera Sans fonts bundled and licensed with
  ReportLab, then use the same content and geometry model for the phone card.
  Render print/phone/QR PDFs to PNG with Poppler so the raster outputs prove the
  vector masters rather than approximating them. This retains selectable text,
  exact geometry, crisp QR modules, and a small local dependency surface. The
  user approved ReportLab on 2026-07-18. Preflight then proved that the locally
  installed Source Sans Pro OTFs use unsupported PostScript outlines and that
  ReportLab's optional direct-PNG backend is absent; embedded Vera plus Poppler
  passed PDF/font/text and exact-pixel render checks without new dependencies.
- **Candidate C — SVG master rendered to PDF and PNG**: One exact vector canvas
  can own both page geometry and crisp QR/text placement, but neither CairoSVG
  nor `rsvg-convert` is currently present, so it would introduce a renderer
  dependency without a demonstrated quality advantage over Candidate B.
- **Candidate D — Pillow-only raster composition and image PDF**: Reuses an
  installed project dependency and is deterministic, but loses selectable text
  and is more fragile for typography, print scaling, and vector-quality output.
- **AI-only**: Appropriate only for bounded layout exploration or wording
  critique. It must not own QR pixels, exact wording, family-name spelling,
  dimensions, or final export truth.
- **Hybrid**: Deterministic content, QR generation, geometry, and validation;
  human/AI visual judgment for hierarchy, warmth, spacing, and print proof.
  This is the approved operating split, subject to actual-artifact verification.
- **Pure code**: Strong for final artifact production and verification, but a
  purely mechanical first layout may underperform on warmth and hierarchy.
- **Repo constraints / prior decisions**: Reader-facing language must remain
  warm and family-centered. `output/` owns generated artifacts, the public
  homepage is the declared DreamHost target, and all advertised formats already
  exist in the Story 003–005 publishing boundary.
- **Existing patterns to reuse**: Canonical `PUBLIC_HOST` and publication labels
  from `scripts/build_family_site.py`; accepted main-book headings for surnames;
  Pillow/image inspection patterns; current Makefile build/validation targets;
  PDF render-and-inspect discipline from the scan runbook.
- **Eval**: Compare candidates at actual letter size and on a 1080 × 1920 phone
  using hierarchy, minimum type, QR size/quiet zone, scan distance, glare,
  clipping, selectable text, reproducibility, and source-name fidelity. A
  beautiful preview that fails physical scanning or readable type loses.

## Tasks

- [x] Add one tracked outreach content/design contract containing the canonical
      HTTPS destination, display hostname, book title/subtitle, plain-language
      offering, camera instruction, source-backed family names, output paths,
      dimensions, minimum type/QR rules, white-background constraint, and the
      website-derived low-coverage accent palette.
- [x] Create `outreach/reunion-flyer-design-spec.md` alongside the contract with
      a complete portable template for the final production record. Populate it
      and the matching story section with measured final values during the
      build; do not defer documentation until a later cross-repo handoff.
- [x] Add focused failing fixtures for exact letter/phone dimensions, required
      copy, hostname/QR consistency, QR decode, quiet zone/contrast, surname
      inventory, output completeness, and invalid/missing contract fields.
- [x] Evaluate the deterministic ReportLab layout against the HTML/SVG/raster
      candidates and the bare preflight composition, record the user-approved
      actual-scale choice, and keep final copy short enough to preserve large
      type and whitespace.
- [x] Implement the approved ReportLab/Bitstream Vera direction after the
      focused preflight proving font embedding, selectable text, vector QR
      rendering, exact-size phone PNG output, and Poppler preview parity. Record
      exact font files, licenses/hashes, ReportLab version, and renderer
      behavior in the handoff.
- [x] Add a grayscale and toner-coverage review: reject large dark/tinted
      backgrounds, banners, or decorative fills; verify the white page remains
      dominant and the website-derived accents survive monochrome printing.
- [x] Classify every content/design field as either `shared visual system` or
      `book-specific substitution`, then exercise the substitution rules with a
      fixture containing a longer title, different hostname, different surname
      count, and different availability wording. It must remain recognizably
      matched without violating minimum type, QR, margin, or contrast rules.
- [x] Add a focused builder/validator plus Makefile targets that generate the
      vector/raster assets under `output/outreach/` without embedding a
      generated QR screenshot or duplicating the URL across unowned constants.
- [x] Render and inspect the real PDF and PNGs. Decode every final QR, inspect
      PDF text/page/font properties, review actual pixels, and stress the phone
      image with a low-brightness simulation.
- [x] Add the canonical 1987 cover as a source-owned letter-flyer element,
      preserve its aspect ratio beside the full-size QR, validate its embedded
      PDF image dimensions/hash/provenance and toner impact, and update the
      cross-book handoff so Onward substitutes its own canonical cover.
- [x] Enlarge the cover to exactly match the print QR height, derive its width
      from the canonical aspect ratio, tighten only the cover/QR gap, and repeat
      toner, grayscale, embedded-image, QR decode, and physical-proof records.
- [x] Test the phone image from a second physical device at normal and high
      screen brightness, or obtain explicit user acceptance of equivalent
      real-world behavior. The user accepted the final artifact family as
      working perfectly; individual phone/brightness cells were not reported.
- [x] Print one 100%-scale proof on matte letter paper; scan at 3 and 6 feet in
      bright and shaded conditions with two available phone cameras, inspect
      hierarchy and minimum type with the intended audience in mind, then make
      any final spacing/contrast corrections. The user printed the revised
      final flyer and reported it `works perfectly`; individual matrix cells
      were not reported, and the user explicitly directed story closure.
- [x] Freshly verify the public homepage and its read/search, PDF/eBook, and
      complete-audiobook handoffs before freezing the printed QR destination.
- [x] Update `README.md`, `CHANGELOG.md`, `docs/spec.md`,
      `docs/methodology/state.yaml`, and the coverage matrix only after the
      artifacts and proof checks pass; record the output inventory and reunion
      outreach boundary without treating it as a new canonical book source.
- [x] Check whether the chosen implementation makes any prototype artwork,
      repeated content constants, or manual QR files redundant; remove them or
      create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Focused flyer/QR tests and Python syntax/lint for changed modules.
  - [x] `make build-family-site` and `make validate-family-site RELEASE=1` to
        prove all advertised local format choices still exist.
  - [x] `make methodology-check`; run `make skills-check` only if project skill
        or agent instructions change.
- [x] If evals or goldens changed: not expected; record deterministic artifact,
      decode, physical scan, and visual checks in this story instead of adding
      an AI-model eval.
- [x] Search all docs and update any related to generated/public artifacts that
      the final implementation changes.
- [x] Verify Central Tenets:
  - [x] T0 — Traceability: wording, family names, and destinations trace to the
        accepted book and publication contracts.
  - [x] T1 — AI-First: use AI for bounded design judgment, not exact QR/export
        truth that deterministic tooling handles better.
  - [x] T2 — Eval Before Build: compare actual-scale layouts and scanning proof
        before locking the final composition.
  - [x] T3 — Fidelity: preserve the book title, family-name spellings, and
        published offering without invented claims.
  - [x] T4 — Modular: keep one outreach contract and a focused renderer rather
        than adding flyer concerns to the large site builder.
  - [x] T5 — Inspect Artifacts: render, print, view, decode, and physically scan
        the outputs rather than trusting command exits.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

Resolved. On 2026-07-19 the user printed the final equal-height cover/QR
revision, reported that it `works perfectly`, accepted the final artifact, and
directed Story 006 closure. No implementation or acceptance blocker remains.

## Blocker Evidence

- Resolved on 2026-07-19 by user report: the first PDF was printed and its QR
  scanned successfully; the user judged it `Very good!`.
- Resolved on 2026-07-19 by the user's final report that the revised PDF
  SHA-256 `fca4e010a7b2e4efede1f511d1c3d58b8f7113be0e397872ef3dbd5f930980ab`
  `works perfectly`. The detailed distance/light/device cells were not
  separately enumerated; the user accepted the equivalent real-world result
  and explicitly directed closure.

## Unblock Condition

Satisfied by the user's final print report and explicit acceptance on
2026-07-19. No further unblock action is required.

## Architectural Fit

- **Owning module / area**: A focused outreach contract, renderer, and validator
  own flyer/QR artifacts. The family-site builder remains the owner of the
  public destination and format offerings; the outreach builder consumes those
  stable truths without changing site generation.
- **Methodology reality**: `spec:4` has an `exists` substrate and C4 is on hold.
  Coverage already records the generated/deployed site, searchable PDF,
  complete audiobook, EPUB, and M4B. This story adds two offline discovery
  surfaces and one reusable QR asset, not a new canonical content format.
- **Substrate evidence**: `build/family-site/index.html` declares the canonical
  HTTPS homepage. `docs/infrastructure.md` declares the same production host.
  Stories 003–005 and the coverage matrix record the readable/searchable site,
  PDFs, 52-track/complete audio, and portable EPUB/M4B. Accepted `doc-web`
  headings supply the title and proposed family-name list. Pillow is already
  exercised in the project; final vector/PDF and QR tooling must be checked by
  the build-story dependency preflight rather than assumed.
- **Data contracts / schemas**: Add one small tracked outreach manifest for
  text, canonical/display URLs, surnames, output dimensions, and accessibility
  minimums. No database, source-scan, `doc-web`, audiobook, EPUB, or public API
  schema changes.
- **File sizes**: after the cover revision, `Makefile` is 160 lines, `README.md`
  204, `CHANGELOG.md` 233, `docs/spec.md` 160, and the coverage matrix 144.
  The new builder/validator is 741 lines, deliberately isolated around one
  artifact family; a future shared multi-book implementation should extract
  layout/provenance primitives rather than growing it in place. The added cover
  checks remain tightly coupled to the same five-artifact contract, so splitting
  them during this reunion revision would add a module boundary without reducing
  behavior or risk. Avoid putting outreach logic into
  `scripts/build_family_site.py` (2,930 lines) or
  `scripts/validate_family_site.py` (1,213 lines).
- **Decision context**: Reviewed Ideal/spec/state/graph/coverage, Stories
  003–005, infrastructure and Onward-process guidance, the accepted main-book
  headings, and current generated site. No print/QR ADR or scout exists after
  search. A new ADR would be disproportionate unless outreach becomes a shared
  multi-book publication system or introduces a tracking/redirect service.

## Files to Modify

- `docs/stories/story-006-reunion-book-flyer-and-phone-qr.md` — scope, plan,
  proof record, and final evidence (new)
- `outreach/reunion-flyer.json` — canonical outreach content/design contract
  (new)
- `outreach/reunion-flyer-design-spec.md` — exact cross-book visual and
  reproduction handoff for the Onward AI (new)
- `outreach/README.md` — practical print, mounting, and phone-sharing guidance
  (new)
- `outreach/reunion-flyer-physical-validation.md` — hash-bound printer,
  distance/light, and second-device evidence matrix (new)
- `scripts/build_reunion_flyer.py` — focused PDF/PNG/QR renderer and validator
  (new)
- `scripts/decode_qr_vision.swift` — independent macOS Vision QR decoder (new)
- `tests/test_reunion_flyer.py` — small deterministic artifact/decode fixtures
  (new)
- `output/outreach/` — five reproducible final artifacts and build evidence
  (new)
- `Makefile` — focused build/test/validate targets (160 lines)
- `README.md` and `CHANGELOG.md` — durable build/output and release note (204
  and 233 lines)
- `docs/spec.md`, `docs/methodology/state.yaml`, and
  `tests/fixtures/formats/_coverage-matrix.json` — shipped outreach-artifact
  truth after proof (160, 107, and 144 lines)

## Redundancy / Removal Targets

- Prototype flyer images, manually exported QR screenshots, or duplicate text
  files after one composition is selected.
- Repeated destination, title, and surname constants outside the tracked
  outreach contract.
- Any QR analytics/short-link experiment; the stable public homepage remains
  directly visible and encoded.
- Any temptation to add flyer generation to the already large site builder or
  to publish generated outreach files into the deploy bundle by default.

## Notes

- Recommended content hierarchy: `FREE FAMILY HISTORY` eyebrow; `Alain Lessard`
  title and full subtitle; one short availability line; large QR; large literal
  hostname; four plain actions (`Read online`, `Search the book`, `Download PDF
  or eBook`, `Listen to the complete audiobook`); and the family-name band.
- The full formal title is important, but `Alain Lessard` should carry the
  visual weight. Long explanatory copy, format logos, app instructions, and a
  family-tree diagram would compete with the QR and minimum type size.
- The proposed 12-name band is a source-backed starting point, not a claim that
  no other relatives appear in the book. If the physical proof becomes dense,
  reduce decorative copy before reducing name or action text below the minimum.
- Matte white stock and an outdoor sleeve are preferable around an RV. Mount
  near eye level and avoid a tinted window or reflective laminate directly over
  the QR; glare can defeat an otherwise correct code.
- The approved print background is paper white `#ffffff`, not the website's
  pale canvas `#f7f8f6`. Reuse the site's identity through sparse deep-green,
  red, gold, charcoal, muted-text, and light-rule details. Do not use a dark
  masthead, tinted page field, full-width filled box, background photograph, or
  other large toner-heavy area. This is both a visual distinction from the
  side-by-side Onward flyer and a practical home-laser-printer constraint.
- Keep the artifact reusable after this reunion: no reunion date, event logo,
  personal phone number, or temporary tracking URL is required.
- This is a new Story 006 rather than a reopened Story 003 or 005. Those stories
  closed on web/publication delivery and validation; this work introduces a
  materially distinct physical print/display context, QR decoding boundary,
  older-audience legibility constraint, and physical scan-distance proof.

## Cross-Book Replication Handoff

This section is part of the deliverable, not optional closeout prose. It is
written so the user can give the URL of this story to an AI working on *Onward
to the Unknown* and receive a matching poster/image family.

### Fixed deliverable surfaces

- **Print master**: one-page portrait US Letter PDF, exactly 8.5 × 11 inches
  (`612 × 792` PDF points), intended for printing at 100% scale on a true white
  background with no large solid-color field.
- **Print preview**: portrait PNG at `2550 × 3300` pixels (`300 ppi` equivalent)
  with the same crop and content as the PDF.
- **Phone card**: portrait PNG at `1080 × 1920` pixels with safe space for
  common full-screen photo viewers and no required content near cropped edges.
- **QR master**: standalone lossless PNG, black modules on white, with the full
  quiet zone preserved. Its exact pixel/module dimensions and error-correction
  level are recorded after final selection.
- **Portable recipe**: the completed story section plus
  `outreach/reunion-flyer-design-spec.md`, sufficient to recreate the design
  without the original rendered files.

### Shared visual system — match across both books

The Alain and Onward versions should share the final page/phone grids, content
hierarchy, margins, alignment, white background, type families/weights, QR
treatment, corner/border/decorative treatment, action-list styling,
surname-band styling, spacing rhythm, and export settings. Each book uses
sparse accents derived from its own website rather than sharing the same accent
hex values. `Matching` means clearly belonging to one system when placed side
by side; the book-specific palettes help them remain immediately distinct, and
different title or surname lengths do not need identical line breaks.

The final production record must replace the following placeholders with exact
measured values:

- printable safe margins and every major component's `x`, `y`, width, and
  height in PDF points or inches;
- phone safe margins and every major component's pixel bounds;
- each color as a hex value plus its role and source website token, including
  paper/background, primary text, accent, rules/borders, and QR field; for
  Alain, record white `#ffffff`, ink `#22231f`, deep `#143d3b`, deep-2
  `#1f5b55`, accent `#8d2f23`, accent-2 `#c1912f`, muted `#626861`, and line
  `#d8ddd5`, plus which subset actually appears in the final artifacts;
- exact font family, font file/source, weight, size, line height, tracking, and
  fallback for each text role;
- QR encoder/library and version, encoded URL, QR version/module count,
  error-correction level, module/box size, quiet-zone modules, rendered size,
  and placement;
- line-break and fit rules for title, subtitle, hostname, actions, and family
  names, including the order in which spacing or copy may change and the type
  sizes that must never be crossed;
- PDF/PNG renderer and versions, image color mode/profile, antialiasing or
  rasterization settings, and any font embedding/subsetting behavior;
- exact build, validation, render, QR-decode, and checksum commands.

### Book-specific substitutions — change for Onward

Only these fields should change between books unless an exception is recorded:

- book display title and formal subtitle;
- canonical HTTPS URL and large display hostname;
- source-backed family-name list or equivalent discovery terms;
- canonical front-cover image with its accepted path, dimensions, and hash;
- truthful availability actions based on that book's public site and files;
- sparse accent colors sampled from that book's website, while retaining the
  shared white-background and low-toner-coverage rules;
- optional one-line family/archive descriptor where the books genuinely differ;
- output basenames, artifact hashes, and book-specific validation evidence.

The other AI must verify its own public destination and offerings rather than
copy Alain claims blindly. It should preserve `Free` and the four-action
structure only where those statements are true for Onward.

### Adaptation order for different content lengths

When Onward content does not fit the Alain line breaks, preserve the shared
hierarchy and accessibility floors in this order:

1. Use the approved alternate line break for the book title or subtitle.
2. Tighten only the documented flexible vertical gaps within their recorded
   minimums.
3. Reflow the name band across the allowed row/column variants.
4. Shorten optional descriptive copy while preserving the truthful actions.
5. Never shrink essential text below 18 pt, action text below the selected
   accessible floor, the hostname below its selected floor, or the QR below its
   verified physical/display size; if those would be required, record and use a
   deliberate layout variant instead.

### Final Production Record — required before Done

- **Selected approach and rationale**: Candidate B, a ReportLab vector scene
  graph plus ReportLab QR and Poppler raster derivatives, won because it
  produced exact letter/phone geometry, embedded selectable fonts, clean vector
  QR modules, and deterministic output without a new dependency. HTML/CSS
  retained browser-print variability; SVG lacked a local PDF renderer;
  Pillow-only output lost selectable/vector text. The first bare ReportLab
  preflight proved the geometry, and the user approved the resulting white,
  sparse-accent composition after full-size color/phone review.
- **Source inputs**: `outreach/reunion-flyer.json`; formal title from the
  accepted main-book/publication metadata; family names from accepted `doc-web`
  headings; canonical cover from accepted `doc-web` image
  `input/doc-web-html/alain-lessard-book-r1/images/page-001-000.jpg`;
  destination from `docs/infrastructure.md`, the generated canonical link, and
  fresh HTTPS proof; palette tokens from
  `build/family-site/assets/site.css`. Print deliberately omits the site's
  `#f7f8f6` canvas and large dark hero treatment.
- **Toolchain**: Python 3.12.13, ReportLab 4.4.9, Pillow 12.2.0, Poppler
  25.04.0, pypdf, and macOS Swift/Vision. ReportLab package-relative
  `Vera.ttf`, `VeraBd.ttf`, and `bitstream-vera-license.txt` have SHA-256
  `c4c45690...288d3d`, `cc037385...13b8e9`, and `3361d054...6315d` respectively;
  the full hashes are in `output/outreach/reunion-flyer-build-report.json`.
  Source Sans Pro CFF OTF embedding and ReportLab direct PNG rendering were
  rejected by fresh preflight, so no silent fallback or new package was added.
- **Exact design tokens and geometry**: the print master is 612 × 792 points
  with 36-point safe margins, a 223.305 × 295.2-point cover at
  `(36.003, 272)`, a 21.49-point white gap, and a 295.2-point (4.1-inch) QR at
  `(280.797, 272)`. Cover and QR have the same height; the centered combined
  row is 539.995 points wide within the 540-point safe area. It uses a
  48-point title, 16-17-point two-line subtitle, 21-point free headline,
  18-point instruction/actions/names, and 23-point hostname. The phone surface
  is 1080 × 1920 with 72-pixel safe margins, a 820-pixel QR at `(130, 430)`,
  92-pixel title, 34-38-pixel subtitle, 43-pixel headline, 32-pixel instruction,
  and 52-pixel hostname. Palette and every remaining baseline/rule coordinate
  are recorded in `outreach/reunion-flyer-design-spec.md`.
- **Cover provenance**: the complete, uncropped accepted cover at
  `input/doc-web-html/alain-lessard-book-r1/images/page-001-000.jpg` is 2550 ×
  3371 pixels and has SHA-256
  `ac6d36744370bf7bf09d01de39dc1715cb4227d0bee2a3b308e9334e7d6e24bb`.
  It is embedded as the PDF's only raster image at its native aspect ratio and
  an effective 822.2 ppi. The build fails on path/hash/dimension drift; the phone
  card intentionally remains unchanged and cover-free.
- **QR**: exact URL `https://alain-lessard.copper-dog.com/`, version 4, Q error
  correction, 33 data modules plus four quiet modules on every edge, 41 total
  modules. Print uses exactly 7.2 points/30 preview pixels per total module;
  phone uses 20 pixels/module; standalone uses 40 pixels/module and is 1640 ×
  1640 pure black/white RGB.
- **Commands**: `make test-reunion-flyer`, `make build-reunion-flyer`,
  `make validate-reunion-flyer`, or combined `make reunion-flyer`; supporting
  proof uses `pdfinfo`, `pdffonts`, `pdftotext`, `shasum -a 256`, the tracked
  Swift Vision decoder, strict local site build/validation, and public HTTPS
  HEAD checks. Exact runnable commands are in the design spec and
  `outreach/README.md`.
- **Human/AI judgment and post-processing**: AI judgment selected hierarchy,
  whitespace, palette roles, and balanced name rows after rendering the exact
  artifacts. The user selected the ReportLab direction, white background, and
  restrained website palette, then requested the familiar original cover after
  a successful first print/QR trial. The cover was placed beside rather than
  above the QR so both recognition and scan size remain strong. There was no
  manual image editing or post-build retouching; every final reader-facing
  pixel is generator-owned.
- **Artifacts**:

  | Path | Size | SHA-256 |
  | --- | ---: | --- |
  | `output/outreach/alain-lessard-reunion-flyer-letter.pdf` | 5,493,099 B | `fca4e010a7b2e4efede1f511d1c3d58b8f7113be0e397872ef3dbd5f930980ab` |
  | `output/outreach/alain-lessard-reunion-flyer-letter-preview.png` | 2,737,060 B | `7a4cc11e3c526aeb8941be6baf4c91e4b4a21fb344c9d3b9e4b22dbc6dc1d035` |
  | `output/outreach/alain-lessard-phone-qr.png` | 92,734 B | `e0847c2281c7049c09f25a3018b9a754a7f9c78a91951c0a506bc947ee7b3f50` |
  | `output/outreach/alain-lessard-qr.png` | 11,710 B | `325e476dfea5126979b3ac52a4dc8032f2736afb1e6767ac6548bb86ab0262ba` |
  | `output/outreach/reunion-flyer-build-report.json` | 2,401 B | `08fe898181fbb1a89cf0abed9430c7785b6fce5db6d38576cd5a97d31ef98602` |

- **Digital verification evidence**: exact PDF/page/text/font and PNG dimensions
  pass; print/phone non-white ratios are 25.6722% and 15.8307%; full-size color,
  phone, and grayscale renders have no clipping, overlap, broken glyph, or
  hierarchy defect. The PDF contains exactly one 2550 × 3371 JPEG at 822.2 ppi
  matching the canonical cover contract. macOS Vision independently decoded the three final images,
  50% and 25% flyer reductions, a 25% grayscale reduction, a 50% image with
  0.8-pixel blur plus JPEG quality 55, and phone images at 80% and 65%
  brightness to the exact URL. These variants are now generated automatically
  under `tmp/pdfs/outreach/stress/` on every validation run. The live homepage,
  reader, PDF, EPUB,
  complete MP3, and M4B returned HTTP 200 with the expected MIME types; strict
  local release validation passed 103 HTML pages, 401 references, 59 search
  rows, 53 MP3s, and two portable files.
- **Physical verification evidence**: the user first printed the superseded
  cover-free PDF, successfully tried its QR, and reported `Very good!`. After
  the cover was added and enlarged to the QR's exact height, the user printed
  the final PDF with SHA-256 `fca4e010...980ab`, reported that the revised
  result `works perfectly`, accepted it, and explicitly directed Story 006
  closure. The detailed 3/6-foot, bright/shaded, two-phone and phone-brightness
  cells were not separately enumerated; that limitation is recorded rather
  than backfilled with invented observations in the hash-bound matrix at
  `outreach/reunion-flyer-physical-validation.md`.
- **Onward substitution example**:

  | Replace for Onward | Retain from shared system |
  | --- | --- |
  | Title and subtitle | Letter/phone canvases and component hierarchy |
  | Canonical cover image/path/hash and aspect ratio | Equal 4.1-inch cover/QR height and centered-row rule |
  | Canonical URL and display hostname | White background and low-toner rule |
  | Source-backed family/discovery names | Vera typography and size floors |
  | Truthful format/action copy | QR error correction, quiet zone, and sizes |
  | Sparse accents sampled from the Onward site | Grids, spacing, rules, output formats, and validation |

## Plan

1. **Lock contract, fonts, and failing baseline (S).** Add
   `outreach/reunion-flyer.json` with book-specific copy, canonical/display URL,
   source-backed surnames, website palette, white/low-toner constraints, exact
   output surfaces, minimum type, and QR requirements. Add a portable design-
   spec skeleton and focused tests for schema completeness, missing/invalid
   values, required wording, prohibited no-account copy, URL equality, color/
   type/geometry floors, and the output inventory. Use ReportLab's licensed
   Bitstream Vera regular/bold TTFs by package-relative path and record hashes;
   do not copy opaque font binaries into the repo. Baseline is zero outreach
   contract, targets, tests, or artifacts.
2. **Build deterministic vector masters and raster derivatives (M).** Add a
   focused `scripts/build_reunion_flyer.py` that validates the manifest,
   registers Vera fonts, creates black-on-white ReportLab vector QR widgets at
   error correction Q with four-module quiet zones, and renders the letter
   flyer, phone card, and QR masters. Use Poppler for the exact 2550 × 3300
   print preview, 1080 × 1920 phone PNG, and declared standalone QR PNG because
   ReportLab's optional `renderPM` backend is not installed. Add narrow Makefile
   build/validate/test targets; keep all flyer logic outside the 2,930-line site
   builder and write generated artifacts only under `output/outreach/` with
   temporary vector intermediates under `tmp/pdfs/`.
3. **Prove geometry, content, and portability (M).** Extend the validator/tests
   to inspect PDF page size, embedded fonts, selectable title/URL, PNG pixel
   dimensions, white corner/background samples, palette/toner constraints, QR
   geometry and encoded source value, and fixture adaptability for a longer
   title/hostname/different surname count. Add an independent macOS Vision QR
   decoder helper or validation path using a `/tmp` Swift module cache, then
   decode every final PNG back to the exact canonical HTTPS URL. If Vision is
   unavailable, fail with an actionable message rather than treating source
   equality as decode proof.
4. **Generate and visually inspect real artifacts (M).** Build the Alain
   outputs, render the latest PDF at 300 ppi, inspect the flyer and phone card
   images after every meaningful layout correction, and verify hierarchy,
   clipping, line breaks, white space, QR quiet zone, surname readability,
   grayscale behavior, and low toner coverage. Freshly recheck the public
   homepage and advertised read/search, PDF/EPUB, and audiobook surfaces. Fill
   the story and `outreach/reunion-flyer-design-spec.md` with final geometry,
   tokens, commands, dependency/font versions and hashes, artifact sizes and
   SHA-256 values, approach rationale, manual/AI judgments, and the Onward
   substitution map.
5. **Close implementation truth without pretending physical proof (S).** Add
   the generated outreach rows to the coverage matrix and update README,
   CHANGELOG, spec/state/graph only after digital proof passes. Run the focused
   tests, Python compile/Ruff checks, real flyer build/validation, site build and
   release validation, and methodology check. Mark build tasks and the Build
   complete gate only from fresh evidence; leave formal validation/story closure
   open for the user's 100%-scale home-laser print and two-phone 3/6-foot scan
   check.
6. **Add the source-recognition cover without weakening QR access (S).** Extend
   the tracked contract with the canonical accepted cover path, source hash,
   and letter-only geometry. Embed the unmodified cover at its native aspect
   ratio to the left of the existing 295.2-point QR, leaving the phone card
   unchanged. Add a failing cover contract/artifact baseline (`pdfimages`
   currently reports zero embedded images), then verify exactly one cover image
   is embedded at sufficient effective resolution, the source hash matches, the
   page remains below the toner ceiling, and every final/stress QR still
   decodes. Rerender and inspect color/grayscale output, update all exact
   geometry/hashes and the Onward substitution rule, and reset physical proof
   to the revised PDF hash.
7. **Give the cover equal visual height without shrinking the QR (S).** Replace
   the fixed two-inch cover width with a contract rule that its height equals
   the 295.2-point QR. Derive the 223.305-point width from the canonical aspect
   ratio, tighten the gap to 21.49 points, and center the 539.995-point group
   inside the existing 36-point margins. Add an equality/margin regression
   whose current baseline is 190.362 versus 295.2 points. Because the source
   cover is dark, raise the measured low-toner ceiling only enough to contain
   the expected roughly 25.6% non-white result (27% maximum), retain the true
   white background and ban on decorative fills, then rebuild, visually inspect,
   decode every final/stress QR, refresh hashes/handoff, and require a new print
   against the final PDF hash.

**Impact and structural health**: This adds one small manifest, one focused
renderer/validator module, one test module, and one portable handoff document.
It does not change source scans, canonical book content, website rendering,
publication packages, deployment, or public routes. The principal risks are
font substitution, QR distortion during rasterization/printing, over-dense
copy, excessive toner coverage, and a handoff that silently hardcodes Alain
values; the preflight, fixtures, visual inspection, and explicit substitution
contract address those risks. No ADR, schema migration, new network service, or
new Python dependency is required.

**Human approval/validation boundary**: The user has approved ReportLab, the
website-derived Alain palette, a white background, and implementation start.
This plan asks approval for one evidence-driven adjustment: use embedded
Bitstream Vera Sans rather than Source Sans Pro because ReportLab 4.4.9 cannot
embed the installed CFF-flavoured Source Sans OTF files. Physical printing and
real-device scan-distance checks remain a post-build user validation gate.

## Work Log

20260718-0000 — story created: verified a distinct offline outreach and
physical-validation boundary, grounded the destination/formats in the existing
Story 003–005 substrate, and preserved the source-backed default surname set;
next step is `/build-story` dependency preflight and actual-scale layout eval.

20260718-0000 — direction refined: user approved ReportLab generation with a
white background and requested visual continuity with the Alain website while
avoiding toner-heavy color fields on a home laser printer; recorded the exact
site palette, low-coverage/grayscale gates, and book-specific palette rule for
the matching Onward handoff; next step remains renderer/font preflight.

20260718-2304 — build-story exploration and eval baseline: read Ideal,
`spec:4`/C4, state/graph, coverage rows, dependency Stories 003-005, decisions,
infrastructure, Makefile, tests, generated site CSS, and the live homepage;
verified `spec:4` substrate exists, C4 remains hold, the active site returns
HTTP 200 and visibly offers web reading/search, PDF, EPUB, complete MP3, and
chaptered M4B, while the repo has zero outreach contract/targets/tests/artifacts.
ReportLab 4.4.9 generated an exact 612 × 792 point vector PDF and Poppler
rendered exact 2550 × 3300 and 1080 × 1920 PNGs; embedded Liberation/Vera TTF
and selectable text passed. Source Sans Pro registration failed because its
installed OTF uses unsupported PostScript outlines, and direct `renderPM` PNG
failed because `rlPyCairo`/`_rl_renderPM` is absent, so the no-new-dependency
plan uses ReportLab-bundled licensed Vera TTF plus Poppler. Swift/Vision imports
successfully with a `/tmp` module cache for independent QR decoding. No ADR
applies and no architecture prerequisite is missing; next step is the human
plan/font adjustment gate, then contract/tests-first implementation.

20260718-2310 — human gate passed: user approved the written plan, Bitstream
Vera substitution, active-goal tracking, and continuous execution through
complete validation; promoted Story 006 from Pending to In Progress; next step
is contract/tests-first implementation.

20260718-2342 — implementation complete: added the tracked outreach contract,
ReportLab letter/phone builder, independent Swift/Vision decoder, six focused
tests, Makefile targets, five final outputs, practical print guidance, and the
self-contained Onward reproduction specification. Rendered and inspected the
exact 300 ppi color and grayscale flyer plus 1080 × 1920 phone card; removed no
canonical input and performed no manual pixel edits; next step is the complete
fresh validation sweep.

20260719-0005 — digital validation complete: rebuilt byte-stable artifacts;
all 26 project tests and six focused project-runtime tests pass, Ruff and Python
compile pass, and independent Vision decoding returns the exact canonical URL
from all final and stress-test images. Supplemental scans, active/companion
`doc-web`, the 52-track/complete audiobook, EPUB, M4B, 103-page release site,
methodology graph, JSON, and git whitespace checks pass. The full suite exposed
and fixed compatibility with both old and new Pillow pixel APIs. Final physical
proof remains honestly open because this Mac has no configured printer and no
second phone; next step is the user's 100%-scale print and documented 3/6-foot,
bright/shaded, two-phone scan check.

20260719-0020 — physical-boundary recheck: `lpstat -p -d` still reports no
system default destination and `system_profiler -json SPPrintersDataType`
returns `no_info_found`, confirming that no printer can be exercised from this
Mac. Added a hash-bound physical-validation record with the complete eight-cell
printed-flyer matrix, two-cell phone-display matrix, printer settings, visual
inspection fields, and expected URL so user observations can close the exact
final artifacts without ambiguity; next step remains real printer/two-device
execution.

20260719-0030 — reproducible stress proof: moved the earlier manual reduced,
grayscale, and dim-display simulations into the maintained validator and added
a blurred/JPEG-compressed camera proxy. Fresh `make validate-reunion-flyer`
independently decoded all three final images and all six generated stress
variants to the exact canonical HTTPS URL; both Python runtimes, all 26 tests,
the six focused tests, compile, and Ruff checks remain green. Artifact hashes
are unchanged; next step remains the external physical matrix.

20260719-0035 — third blocker audit: the physical record still contains no user
observations, `lpstat` again reports no default destination, and the macOS
printer inventory again returns `no_info_found`. With every feasible digital
check complete and no honest substitute for paper/two-device evidence, recorded
the blocker, evidence, and exact unblock condition and formally blocked the
active goal pending external physical testing.

20260719-1052 — blocker cleared and cover revision explored: user reported the
first flyer printed and its QR scanned `Very good!`, proving printer access and
positive preliminary physical output. The accepted canonical cover is
`input/doc-web-html/alain-lessard-book-r1/images/page-001-000.jpg` (2550 × 3371,
SHA-256 `ac6d3674...24bb`), also declared as the portable-edition cover source;
the current flyer baseline has zero embedded raster images. No print/QR ADR or
architectural prerequisite is missing. Plan is to preserve the full 4.1-inch
QR and phone card, place the cover at native aspect ratio in the QR row, add
cover provenance/effective-resolution tests, rerender, repeat all digital
checks, and require final physical proof against the new PDF hash.

20260719-1102 — cover revision implemented and digitally validated: extended
the outreach contract with the accepted cover path, 2550 × 3371 dimensions,
full SHA-256, two-inch print width, 24-point QR gap, and 600-ppi floor. The
baseline produced three expected failures (missing cover property/hash guard
and zero PDF images); the implementation now passes seven focused tests and all
27 project tests. The deterministic revised PDF embeds exactly one uncropped
cover at 1275 ppi and places it at `(74.4, 328.419)` beside the unchanged
4.1-inch QR at `(242.4, 276)`. Color and RGB-grayscale renders are clean, toner
coverage is 17.6148%, and Vision decodes the three final plus six stress images
to the exact URL. A byte-stability rebuild preserved all five hashes; the phone
and standalone QR hashes remain unchanged. Ruff, compile, EPUB/M4B, 103-page
release-site, methodology, and whitespace checks pass. Updated the Onward
handoff, README, changelog, spec/state/coverage, and hash-bound physical record;
next step is printing PDF SHA-256 `880424b6...a04c` and confirming cover
recognition plus the remaining physical scan matrix.

20260719-1112 — equal-height revision explored and approved: user asked for the
book cover to be the same height as the QR, allowing a modest QR reduction if
needed. Geometry proves the 4.1-inch QR can remain unchanged: a same-height
cover is 223.305 × 295.2 points, and a 21.49-point gap makes the combined row
539.995 points wide within the 540-point safe area. The current measurable
baseline is only 190.362 points of cover height (64.5% of QR height). Expected
non-white coverage rises from 17.6148% to about 25.6%; recorded the cover as the
sole source-recognition exception and a 27% ceiling while preserving a 74%+
white page. Next step is a failing equality/margin fixture, contract-derived
geometry, render inspection, full decode/regression, and revised physical hash.

20260719-1141 — equal-height revision implemented and digitally validated: the
contract now derives a 223.305 × 295.2-point cover from the canonical 2550 ×
3371 aspect ratio and places it at `(36.003, 272)` beside the unchanged 295.2-
point QR at `(280.797, 272)`. Their 21.49-point gap yields a centered 539.995-
point row inside the 540-point safe area. Focused equality/margin coverage and
all 28 project tests pass. The PDF still embeds one uncropped cover, now at
822.2 ppi; color and grayscale reviews are clean; page coverage is 25.6722%,
leaving 74.3278% white. Vision decoded all three final images and six stress
variants to the exact URL. A repeat build preserved every hash; the final PDF
is SHA-256 `fca4e010...980ab`, while phone and standalone QR artifacts remain
unchanged. Ruff, compile, EPUB/M4B, 103-page release-site, methodology, and
whitespace checks pass. The design spec and Onward handoff now require equal
cover/QR height with aspect-derived width. Only revised-paper and second-phone
physical observations remain open.

20260719-1208 — physical acceptance and `/mark-story-done` closeout: user
printed the final equal-height revision with PDF SHA-256 `fca4e010...980ab`,
reported that it `works perfectly`, accepted the result, and explicitly asked
to record the final design for Onward replication, close Story 006, and push it
to `main`. Recorded acceptance against the exact artifact without inventing
the printer model or unreported distance/light/device cells. Rechecked the
self-contained handoff: it specifies exact 612 × 792-point and 1080 × 1920
surfaces, 36-point print margin, equal 295.2-point cover/QR heights,
aspect-derived 223.305-point cover width, 21.49-point gap, centered 539.995-
point row, white low-toner palette, Vera typography, QR/module geometry,
book-specific substitutions, commands, hashes, and validation procedure.
All acceptance, task, tenet, build, and validation gates are now resolved;
Story 006 is Done. Recommended next step: `/check-in-diff`.
