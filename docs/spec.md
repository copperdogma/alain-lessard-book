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

### C1 Main-book scans exist, but supplemental materials are not all present

- Ideal: all book and companion source material arrives with complete metadata
- Constraint: begin with the 153 main-book JPG scans in `input/raw scans/main book/`
- Limitation: the user noted that a couple of minor companion items still need
  to be scanned
- Limitation type: source availability
- Evolution signal: all supplemental items have source files and inventory rows
- Residual form: keep a thin source manifest and delete temporary notes

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

### C4 Website content model does not exist yet

- Ideal: cleaned scans and OCR feed a structured book/site canon
- Constraint: first establish the PDF and source lineage before building the
  website
- Limitation: this repo is brand new and has not chosen its site runtime
- Limitation type: execution
- Evolution signal: the first website slice renders real book content from
  source-backed artifacts
- Residual form: keep only the site shell and adapters that prove reusable

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
