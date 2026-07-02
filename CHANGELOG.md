# Changelog

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
