# Spec

This spec records the active constraints between the ideal and current repo
reality. Categories use stable `spec:N` ids so stories, decisions, and evals
can point at them without depending on heading wording.

## spec:1 Source Intake & Inventory

The repo needs a clear inventory of raw scans, supplemental scans, source PDFs,
and generated artifacts.

### spec:1.1 Upstream truth

The project should consume named, inspectable upstream inputs rather than a
folder of undocumented local files.

### C1 Source inventory now includes all known supplemental materials

- Ideal: all book and companion source material arrives with complete metadata
- Constraint: begin with the 153 main-book JPG scans in
  `input/raw scans/main book/`
- Constraint: the complete known supplemental set is now present as
  `input/raw scans/Alain's Song/` and
  `input/raw scans/Growing Up on the Farm/`
- Limitation: future unknown family materials may still arrive outside this
  edition's current source contract
- Limitation type: source inventory
- Evolution signal: any newly discovered item receives its own intake report,
  manifest row, PDF, and website archive entry
- Residual form: keep the source manifest and intake reports as the handoff
  record

## spec:2 Scan Cleanup & PDF Construction

The main book should become a clean, consistent, searchable PDF without losing
visual source fidelity.

### spec:2.1 Page image normalization

Every page should have the scanner platen removed, remain upright, and land on
a common page canvas.

### C2 The raw scans alternate top and bottom scanner-platen bands

- Ideal: scans arrive already page-cropped and consistently aligned
- Constraint: the current JPGs include scanner platen bands at alternating page
  edges
- Limitation: the scanner exported full-platen captures rather than clean page
  crops
- Limitation type: input quality
- Evolution signal: processed pages pass visual spot checks and OCR validation
- Residual form: keep the deterministic crop script and manifest for rebuilds

## spec:3 OCR, Text, & Provenance

OCR should make the book searchable while preserving an inspectable relationship
to scanned page images.

### spec:3.1 OCR layer

The PDF should retain the page image as the visual source while adding a hidden
text layer.

### C3 OCR quality needs reviewable evidence before it can be treated as final

- Ideal: OCR text is accurate enough for search and future web indexing
- Constraint: OCR is machine-generated from scanned pages and needs validation
- Limitation: the first pass can verify searchability and sample legibility but
  cannot guarantee every character is correct
- Limitation type: OCR quality
- Evolution signal: sample extracted text and page renders pass review; later
  corrections can target exact source pages
- Residual form: keep OCR manifests and page-level source anchors

## spec:4 Website & Digital Edition

The website should eventually make the book and companion materials readable,
searchable, and navigable outside the PDF.

### spec:4.1 Website substrate

The chosen site stack should support chapter reading, indexes, source downloads,
and companion archive materials.

### C4 Website and audiobook are live and verified

- Ideal: cleaned scans and OCR feed a structured, public, Onward-style book site
- Constraint: the static site is generated from the accepted `doc-web`
  HTML/provenance bundle, copied processed page images, generated PDF
  downloads, supplemental-document PDFs, and audio-script manifest, then
  uploaded over the Onward DreamHost SFTP path
- Constraint: DreamHost assigned this hosted subdomain to origin
  `173.236.136.184`, not the older Onward origin IP
- Constraint: all 52 reviewed chapter MP3s and the generated 9:00:14 complete
  audiobook exist locally; the strict static bundle now exposes native players,
  direct downloads, semantic reading-section mappings, and local resume
  behavior
- Constraint: the main-book reader derives 57 meaningful sections from the 39
  canonical `doc-web` entries: 49 narrative sections aligned one-to-one with
  tracks 02–50 plus 8 named reference sections. All 1,737 source block ids are
  retained exactly once, while legacy printed-page URLs redirect into the new
  section routes
- Constraint: the audio-enabled bundle was deployed to DreamHost on 2026-07-16;
  all 53 MP3 paths passed public HTTPS, `audio/mpeg`, positive-length, and `206`
  byte-range verification through Cloudflare
- Constraint: production closeout verified native playback, saved-position
  resume, single-player behavior, MP3 download, and the native player/source/
  download fallback with JavaScript disabled
- Limitation: future hosting, CDN, or browser changes could regress byte-range
  delivery or native media behavior after this verified release
- Limitation type: operational durability
- Evolution signal: rerun strict public validation and the focused browser smoke
  after future audiobook or hosting changes
- Residual form: keep the static generator, deploy helper, and infrastructure
  note plus the canonical audio manifest/full-book builder; delete only
  temporary DNS workaround notes

## spec:5 Planning Infrastructure

The repo needs enough structure to survive long gaps and handoffs without
turning into process theater.

### spec:5.1 Methodology package

Ideal, spec, state, graph, stories, evals, and decisions should stay aligned.

### B1 Planning continuity still depends on explicit methodology artifacts

- Ideal: project context would stay coherent without scaffolding
- Constraint: keep methodology state, compiled graph, checklist, and aligned
  runbooks while the repo is forming
- Limitation: long-running archival work still benefits from stable repo memory
- Limitation type: AI capability
- Evolution signal: the project settles into a smaller stable workflow
- Residual form: keep only the pieces that still pay for themselves
