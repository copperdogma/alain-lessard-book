# Scout 001 — eReader and Audiobook Formats

**Source:** `/Users/cam/Documents/Projects/onward-to-the-unknown-website`
plus current official reader/platform documentation
**Scouted:** 2026-07-17
**Scope:** Recheck Onward's audiobook-distribution research, then evaluate
portable reading and listening formats that elderly relatives can add to the
reader or audiobook app they already use
**Previous:** None
**Status:** Complete — Story 005 Built, Deployed, and Publicly Verified

## Decision

Create one story for a portable family edition with two new primary artifacts:

1. a reflowable, accessible EPUB 3 edition for Apple Books, Kindle,
   Kobo, Google Play Books, and other EPUB readers; and
2. a chaptered M4B edition of the existing reviewed audiobook for audiobook
   apps on phones, tablets, and computers.

Keep the existing website, searchable PDFs, individual MP3s, and complete MP3.
The new formats are convenience downloads, not a replacement canon or a
storefront-distribution project.

There is no reliable universal URL that can silently add an arbitrary family
file to every installed reader. The honest website pattern is a direct
standards-based download followed by one short platform-specific instruction:

- Apple Books: download/import the EPUB or audiobook; content imported on a
  Mac can sync through Books/iCloud.
- Kindle: download the EPUB, then use Amazon's Send to Kindle flow.
- Kobo: download the EPUB, then sideload it by USB or, on supported devices,
  through Google Drive or Dropbox.
- Google Play Books: download the EPUB, then choose `Open with Play Books` or
  upload it to the user's library.
- Other audiobook apps: download the chaptered M4B; retain the complete MP3 as
  the universal fallback.

## Onward Recheck

Onward did research audiobook storefronts and app distribution in April 2026,
but it did not build an EPUB or M4B:

- Scout 002 selected the site-hosted MP3 flow as the first family lane.
- Scout 003 again rejected a commercial audiobook storefront as the next move.
- EPUB appeared only as an input ElevenReader could accept for its own
  on-demand narration; it was not evaluated as a downloadable eReader edition.
- Onward's full audiobook builder produced one merged MP3 with pauses, not a
  chaptered M4B.

That decision was reasonable for shipping Onward quickly. Alain now has a
stronger substrate for portable formats: 57 semantic reading/reference
sections, all 1,737 source blocks accounted for, a 52-track reviewed audio
manifest, and a verified complete audiobook.

## Findings

1. **A reflowable EPUB 3 is the missing high-value reading format** — HIGH
   value, story-sized

   What: EPUB 3 provides a reading spine, navigation document, metadata,
   reflowable text, images, and accessibility semantics. Apple Books imports
   EPUB; Amazon accepts EPUB through Send to Kindle; Kobo accepts unprotected
   EPUB; and Google Play Books imports EPUB on computers, Android, iPhone, and
   iPad.

   Us: The accepted doc-web bundle and semantic reading catalog already contain
   the ordered text, headings, tables, figures, captions, and source lineage.
   The bundle's extracted images total about 89 MiB, so an image-conscious EPUB
   can remain below Amazon's 200 MB Send to Kindle limit without embedding the
   full scan set.

   Recommendation: Create a story. Generate a DRM-free EPUB 3 from the same 57
   semantic sections as the website. Include the cover, meaningful figures and
   captions, tables that remain usable on narrow screens, a real table of
   contents, language/author/accessibility metadata, and links back to the
   archive for exact scans and oversized reference material.

   Transfusion:
   - Exemplar: Onward's manifest-first, source-linked distribution approach.
   - Invariant: the portable edition must remain traceable to the same canon
     and must not silently omit source material.
   - Adaptation: Alain's EPUB is generated from semantic reading sections, not
     printed pages or the website chrome.
   - Proof target: EPUBCheck passes; Kindle Previewer, Apple Books, and at least
     one non-Apple EPUB reader preserve order, TOC, text resizing, figures,
     captions, tables, and readable reference sections.

2. **A chaptered M4B is the missing high-value audiobook download** — HIGH
   value, story-sized

   What: A single AAC audiobook container can carry embedded cover art,
   title/author/narrator metadata, and 52 chapter markers. It gives compatible
   audiobook apps a much better experience than a nine-hour undivided MP3:
   chapter navigation, remembered position, playback speed, sleep timers, and
   a single library item.

   Us: The canonical audio manifest already owns ordering, titles, durations,
   source paths, and full-book metadata. `ffmpeg` and `ffprobe` are installed.
   At 64 kbps mono AAC, the nine-hour book would be roughly 247 MiB; quality and
   size must be listening-tested rather than assumed. The reviewed source MP3s
   remain unchanged.

   Recommendation: Create a story. Add a deterministic M4B builder with cover
   art and manifest-derived chapters. Keep the existing full MP3 as the broad
   fallback because Apple explicitly supports importing MP3 audiobooks and not
   every app handles M4B the same way.

   Transfusion:
   - Exemplar: Onward and Alain's manifest-ordered full-audiobook builders.
   - Invariant: the 52 reviewed tracks remain in exact order, with no narration
     edits or missing boundaries.
   - Adaptation: emit mono AAC with embedded chapter metadata instead of one
     stereo or undivided MP3.
   - Proof target: `ffprobe` reports 52 correctly named chapters, duration and
     boundaries match the manifest, cover/metadata are embedded, and the file
     imports and resumes correctly in representative Apple and Android
     audiobook apps.

3. **The website should use a small device-oriented handoff, not one magical
   button** — HIGH value, story-sized with the formats

   What: Apple and Google can open imported files in their reader apps, while
   Kindle requires Send to Kindle and most Kobo devices require USB or a linked
   cloud service. Browsers cannot safely bypass these account/app boundaries.

   Us: The homepage and archive already expose reader-friendly download cards.

   Recommendation: Add a `Read or listen in another app` panel with large,
   literal choices:

   - `Download for eReaders (EPUB)`
   - `Send this book to Kindle` (a short two-step guide plus Amazon's official
     Send to Kindle link)
   - `Download chaptered audiobook (M4B)`
   - `Download audiobook as MP3` (existing fallback)
   - `Need help?` with four compact Apple / Kindle / Kobo / Google instructions

   Avoid user-agent sniffing and platform deep links that only work on some
   devices. Direct downloads must stay available without JavaScript.

4. **Do not create MOBI, AZW3, or a fixed-layout EPUB as primary outputs** —
   MEDIUM value, skip

   EPUB is the supported source format for modern Kindle conversion, while a
   reflowable layout gives older readers adjustable type, margins, contrast,
   and line spacing. The existing PDF already preserves the exact printed-page
   experience when visual fidelity matters.

5. **Do not combine the nine-hour audiobook into the first EPUB** — MEDIUM
   value, skip

   EPUB media overlays can synchronize text and prerecorded audio, but that
   would create a very large, compatibility-sensitive package and require
   paragraph- or sentence-level timing data that the project does not yet own.
   Apple's read-aloud guidance is oriented toward fixed-layout books, and
   Amazon does not accept full read-along audio as ordinary Kindle content.
   Keep EPUB and M4B separate for the first portable release.

6. **Do not prioritize LPF/W3C Audiobook packaging or a storefront** — LOW
   immediate value, skip

   The W3C Audiobooks manifest is a sound open standard and resembles the
   repo's existing manifest, but familiar consumer-app ingestion is much weaker
   than EPUB and M4B today. Spotify/Audible/retail publishing would also
   reintroduce account, payment, rights, and purchase-flow friction without
   improving private family access.

## Proposed Story Boundary

The follow-up story should own:

- deterministic EPUB 3 and M4B builders;
- cover art and portable-publication metadata;
- EPUBCheck, Kindle Previewer, structural M4B, and representative app/device
  validation;
- strict build/deploy validation and correct static MIME types;
- a family-facing format chooser with direct downloads and short platform help;
- coverage/spec/state/runbook updates after the artifacts actually pass.

It should not own commercial storefront publication, podcast feeds, DRM,
account creation, synchronized word highlighting, or narration regeneration.

## Approved

- [x] 1. Create the portable EPUB/M4B story — Story 005
- [x] 2. Build the artifacts and site handoff — local build and validation complete
- [x] 3. Deploy and publicly validate the artifacts — Story 005 closeout

## Skipped / Rejected

- MOBI/AZW3 as maintained outputs — Amazon's current path accepts EPUB and
  converts it for Kindle.
- Fixed-layout EPUB — inferior resizing/accessibility for this audience; the
  scanned PDF remains the fidelity artifact.
- Audio-embedded read-along EPUB — too large and synchronization-heavy for the
  first portable release.
- W3C Audiobook/LPF as the primary download — standards-correct but not the
  familiar-app path the user asked for.
- Audiobook storefront distribution — unnecessary account and commercial
  friction for a no-charge family archive.

## Verification

- Re-read Onward Stories 008 and 009 plus Scouts 002 and 003.
- Confirmed Onward has no EPUB or M4B builder/output.
- Confirmed Alain's 57-section reading manifest and 52-track v4 audiobook
  manifest are present.
- Confirmed the source audio decodes as 44.1 kHz mono MP3 and the complete file
  is 9:00:14 / 518,630,750 bytes.
- Confirmed `pandoc`, `ffmpeg`, and `ffprobe` are installed locally; Story 005
  invoked the official EPUBCheck 5.3.0 jar and used Apple Books plus epub.js for
  representative app/independent rendering. Kindle Previewer was not required
  for the local build gate.
- Deployed the release to `alain-lessard.copper-dog.com`; strict production
  validation passed all 103 HTML pages, 401 references, 59 search rows, all 53
  MP3s, and both portable files with correct MIME, exact length, and `206`
  ranges, followed by clean desktop/mobile browser smoke checks.
- Reviewed current official platform documentation on 2026-07-17.

## Evidence

### Local

- `/Users/cam/Documents/Projects/onward-to-the-unknown-website/docs/scout/scout-002-audiobook-distribution-and-elder-friendly-listening.md`
- `/Users/cam/Documents/Projects/onward-to-the-unknown-website/docs/scout/scout-003-audiobook-and-podcast-distribution-and-elder-friendly-listening.md`
- `input/doc-web-html/alain-lessard-book-r1/manifest.json`
- `build/family-site/_internal/reading-sections.json`
- `audiobook/manifest.json`

### Current official sources

- W3C, EPUB 3.3: https://www.w3.org/TR/epub-33/
- W3C, EPUB Accessibility 1.1: https://www.w3.org/TR/epub-a11y-11/
- W3C/DAISY, EPUBCheck: https://github.com/w3c/epubcheck
- W3C, Audiobooks: https://www.w3.org/TR/audiobooks/
- Apple, import books and audiobooks:
  https://support.apple.com/en-ae/guide/books/ibkseed72068/mac
- Amazon, Send to Kindle transfer formats and 200 MB limit:
  https://digprjsurvey.amazon.com/csad/help/node/TCUBEdEkbIhK07ysFu
- Amazon, Kindle Previewer:
  https://kdp.amazon.com/en_US/help/topic/G202131170
- Kobo, add non-protected EPUB/PDF files:
  https://help.kobo.com/hc/en-us/articles/360024775093
- Kobo, add EPUB/PDF files through Google Drive on supported devices:
  https://help.kobo.com/hc/en-us/articles/15335985512983
- Google, upload EPUB/PDF to Play Books:
  https://support.google.com/googleplay/answer/11012086
