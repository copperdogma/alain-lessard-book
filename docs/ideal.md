# The Ideal

## Product Ideal

The project is the durable digital edition of the *Alain Lessard* family book
and its companion materials. A reader should be able to open a clean searchable
PDF, browse a future website, follow scans and notes back to source material,
and trust that no page or archive item was quietly dropped during processing.

The book scan should feel careful rather than merely assembled. Page images
should be consistently cropped, upright, legible, and normalized to a stable
page size. OCR should make the PDF searchable without damaging the visual scan.

The future website should make the book materially accessible on the web. It
should support chapter-level reading, source downloads, indexes, companion
materials, and later annotations without turning the archive into a cluttered
grab bag.

The tone should be warm, plainspoken, and family-centered. Reader-facing copy
should talk about the book, the people, the stories, photographs, and family
documents, not the build process.

## Execution Ideal

The project should be easy to resume and verify. Raw inputs stay untouched,
generated artifacts live under clear output paths, and every processing step is
repeatable from repo scripts.

The scan pipeline should emit manifests and review surfaces so future cleanup
can target exact pages rather than guessing. Website work should start from the
same canonical source lineage rather than a one-off copy of a PDF.

## Vision-Level Preferences

- **Archive-First.** Treat the book and related scans as family-archive
  sources, not disposable website assets.
- **Trustworthy Source Lineage.** Every generated PDF, OCR text, and future web
  page should be traceable to the source scan or companion file.
- **Deterministic Cleanup.** Prefer scripted image processing with reviewable
  manifests over manual edits that cannot be repeated.
- **One Canon, Many Experiences.** The same core content should feed PDF,
  website, search, indexes, audio, and future derivatives.
- **Accessible Reading.** The final website should be legible, forgiving, and
  usable across desktop and mobile devices.

## Requirements

1. **Clean Searchable PDF** - Produce a cropped, normalized, OCR-backed PDF of
   the main book.
2. **Preserved Raw Inputs** - Keep original scans unchanged and separate from
   generated artifacts.
3. **Inspectable Processing Manifest** - Record page-level crop decisions,
   dimensions, and output paths.
4. **Companion Archive Intake** - Add supplemental scans honestly when they
   arrive, without implying they are already present.
5. **Future Website Canon** - Prepare the source lineage and repo surface for a
   website built from durable book/source artifacts.
