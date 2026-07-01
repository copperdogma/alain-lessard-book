# The Ideal

## Product Ideal

The project is the durable digital family-archive edition of the *Alain
Lessard* book and its secondary materials, in the same spirit as the *Onward to
the Unknown* treatment. A reader should be able to open clean searchable PDFs,
browse a warm website, listen to narrative audio, follow scans and notes back to
source material, and trust that no page or archive item was quietly dropped
during processing.

The book scan should feel careful rather than merely assembled. Page images
should be consistently cropped, upright, legible, and normalized to a stable
page size. OCR should make the PDF searchable without damaging the visual scan.
Secondary scans should receive the same archive-first treatment at the scale
appropriate to each item.

The website should make the book and companion materials materially accessible
on the web. It should support chapter-level reading, source downloads, indexes,
companion scans, narrative audio, and later annotations without turning the
archive into a cluttered grab bag.

The audio experience should follow the Onward model: narrative sections,
stories, introductions, poems, and other listenable prose can become audiobook
chapters or audio companions, while dense genealogy tables, indexes, and lists
remain readable and searchable rather than being turned into awkward narration.

The tone should be warm, plainspoken, and family-centered. Reader-facing copy
should talk about the book, the people, the stories, photographs, audio, and
family documents, not the build process.

## Execution Ideal

The project should be easy to resume and verify. Raw inputs stay untouched,
generated artifacts live under clear output paths, and every processing step is
repeatable from repo scripts.

The scan pipeline should emit manifests and review surfaces so future cleanup
can target exact pages rather than guessing. Website and audio work should start
from the same canonical source lineage rather than one-off copies of a PDF,
HTML export, or audio script.

## Vision-Level Preferences

- **Archive-First.** Treat the book and related scans as family-archive
  sources, not disposable website assets.
- **Trustworthy Source Lineage.** Every generated PDF, OCR text, and future web
  page or audio script should be traceable to the source scan or companion file.
- **Deterministic Cleanup.** Prefer scripted image processing with reviewable
  manifests over manual edits that cannot be repeated.
- **One Canon, Many Experiences.** The same core content should feed PDF,
  website, search, indexes, narrative audio, and future derivatives.
- **Narrative Audio, Not Table Narration.** Audio should make stories and prose
  easier to experience; tables and dense genealogical structures should stay
  readable, searchable, and linkable.
- **Accessible Reading.** The final website should be legible, forgiving, and
  usable across desktop and mobile devices.

## Requirements

1. **Clean Searchable PDFs** - Produce cropped, normalized, OCR-backed PDFs of
   the main book and appropriate PDFs for secondary materials.
2. **Preserved Raw Inputs** - Keep original scans unchanged and separate from
   generated artifacts.
3. **Inspectable Processing Manifest** - Record page-level crop decisions,
   dimensions, and output paths.
4. **Companion Archive Intake** - Add supplemental scans honestly when they
   arrive, without implying they are already present.
5. **Website Family Archive** - Publish the book and companion materials as a
   readable, searchable, navigable web experience with source downloads and
   family-centered entry points.
6. **Onward-Style Audio Companion** - Generate reviewed audio scripts and audio
   assets for narrative sections while keeping tables, indexes, and lists in
   readable/searchable form.
