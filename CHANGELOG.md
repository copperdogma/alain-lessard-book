# Changelog

## [2026-07-02-02] - Add supplemental documents to archive

### Added
- Added deterministic processing for the two supplemental scan folders,
  producing reader and archival searchable PDFs for each document.
- Added the companion documents to the family-site Archive page, download
  bundle, and search index.
- Added readable HTML pages for each companion document from accepted
  `doc-web` bundles, with source page images and links to the reader and
  archival PDFs.

### Changed
- Updated source inventory, methodology state, and validation to treat the
  supplemental scan set as complete.
- Simplified home-page Start Reading cards by removing printed-page and
  source-scan metadata labels.
- Added home-page companion-document links and tightened supplemental cleanup:
  folded song sheets now get adaptive background normalization, while typed
  pages get black/white normalization with deskew.
- Versioned companion PDF links in the home page, archive page, and search
  index so refreshed PDFs bypass stale CDN caches immediately.
- Updated companion-document search rows to open the new HTML pages instead of
  the PDF downloads.
- Added a companion `doc-web` recipe and Make targets for running and
  validating the two accepted companion-document HTML bundles.

## [2026-07-02-01] - Improve book website navigation

### Added
- Added a family-site validator for local and public static-site checks.

### Changed
- Reworked the book page contents around source-order parts and heading links
  from the accepted `doc-web` bundle.
- Removed per-heading page labels from the book contents so the TOC stays
  focused on section and family-entry headings.

### Fixed
- Added sticky-header-safe hash navigation so deep links land with their
  headings visible.

## 2026-07-02

- Added the Alain `doc-web` runtime config, image-HTML recipe, import wrapper,
  and Make targets for contract, run, import, and active-bundle validation.
- Ran `doc-web` against `output/processed-pages/` and accepted
  `input/doc-web-html/alain-lessard-book-r1/` with 39 entries, 1,738
  provenance rows, and 155 extracted image crops.
- Rebuilt the family site generator around the accepted `doc-web` bundle so
  chapters preserve tables, figures, captions, source scan links, search, TOC,
  archive downloads, and audio-script links.
- Rebuilt the audiobook script generator from the `doc-web` HTML bundle and
  kept table-heavy records, bibliography, cover/title pages, and page-level
  reference material out of the audio lane.
- Deployed the doc-web-powered site to DreamHost and verified the public host,
  figure/caption pages, table pages, versioned search assets, and live search
  results over HTTPS.

## 2026-07-01

- Bootstrapped the project repo from the Onward methodology surface.
- Added the first scan-to-PDF story and deterministic processing pipeline.
- Documented the raw main-book scan set as the current input contract.
- Built the cleaned 153-page distribution and archival searchable PDFs.
- Added reusable future-book intake documentation and scan-report tooling.
- Added Onward-style narration script generation for narrative sections while
  keeping genealogy tables, indexes, and dense lists out of the audio lane.
- Added the static family archive generator and built `build/family-site/` with
  searchable page OCR, page images, PDF downloads, archive notes, and audio
  script links.
- Copied the Onward DreamHost deploy helper, widened the SFTP timeout for this
  larger bundle, created the DreamHost remote directory, and uploaded the
  generated static bundle to `/home/onward_user/alain-lessard.copper-dog.com`.
- Created the Cloudflare DNS record for `alain-lessard.copper-dog.com` pointing
  at the Onward DreamHost origin.
- Recorded the interim DreamHost `Site Not Found` failure while the hosted
  subdomain still needed to be mapped to the uploaded directory.
- Created the DreamHost hosted subdomain, updated Cloudflare to DreamHost's
  assigned origin `173.236.136.184`, issued a Let's Encrypt certificate, and
  verified public HTTPS for the homepage, book page, first chapter, and
  searchable PDF download.
