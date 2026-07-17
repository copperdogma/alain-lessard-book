# Infrastructure

Operational truth for hosting, DNS, and deployment. Keep this file current when
the real environment changes.

## Hosting

- **Provider**: DreamHost
- **Plan**: Shared hosting, following the verified *Onward to the Unknown*
  deployment pattern.
- **Primary public target**: `alain-lessard.copper-dog.com`
- **Reference project**:
  `/Users/cam/Documents/Projects/onward-to-the-unknown-website`
- **Deploy helper**: `scripts/deploy_static_site.py`
- **Local deploy command**: `make deploy-static`
- **Static bundle source**: `build/family-site/`
- **Remote site path**:
  `/home/onward_user/alain-lessard.copper-dog.com`
- **Observed SFTP deploy on 2026-07-01**:
  - Created remote directory:
    `/home/onward_user/alain-lessard.copper-dog.com`
  - Uploaded `build/family-site/` over SFTP using the Onward DreamHost account
  - Verified these remote paths via the deploy transcript:
    `index.html`, `chapter-001.html`, `images/`, and `.deploy-manifest.json`

## Local Environment

The local `.env` is copied from the Onward website project and is intentionally
gitignored. It must contain:

- `DREAMHOST_SFTP_HOST`
- `DREAMHOST_SFTP_USERNAME`
- `DREAMHOST_SFTP_PASSWORD`
- `DREAMHOST_SITE_PATH`
- `DREAMHOST_DEPLOY_SOURCE_DIR`

For unusually large bundles, `DREAMHOST_SFTP_TIMEOUT_SECONDS` can be set to a
larger timeout. The deploy helper defaults to 1800 seconds because this project
publishes distribution and archival PDFs plus a large audiobook media set.

Do not commit `.env` or print credential values in logs.

Run `make deploy-deps` before the first deployment. It installs the pinned SFTP
helper dependency into the same Python interpreter selected by the Makefile;
using an unrelated shell Python can leave the deploy interpreter without
`pexpect`.

## DNS

The target hostname is `alain-lessard.copper-dog.com`.

As of 2026-07-01:

- Cloudflare is authoritative for `copper-dog.com`.
- Cloudflare DNS record `alain-lessard.copper-dog.com` exists:
  - type: `A`
  - content: `173.236.136.184`
  - proxied: `true`
  - record id: `4bdf435e1aba643e02f6db6011132dd0`
- Authoritative checks against Cloudflare nameservers resolve the hostname to
  Cloudflare edge IPs.
- DreamHost nameservers return origin `173.236.136.184` for the hosted
  subdomain.
- The DreamHost hosted subdomain maps to
  `/home/onward_user/alain-lessard.copper-dog.com`, and that remote directory
  contains the uploaded static bundle.
- DreamHost issued a Let's Encrypt certificate for
  `alain-lessard.copper-dog.com` expiring on 2026-09-30.
- Public HTTPS serves the generated static site, and public HTTP redirects to
  HTTPS.

Useful deployment verification commands:

```bash
dig +short alain-lessard.copper-dog.com
curl -I https://alain-lessard.copper-dog.com
curl -I https://alain-lessard.copper-dog.com/book.html
```

If the local resolver has a stale NXDOMAIN cache immediately after DNS changes,
verify against Cloudflare directly:

```bash
dig @chelsea.ns.cloudflare.com alain-lessard.copper-dog.com +short
curl -I --resolve alain-lessard.copper-dog.com:443:104.21.43.33 \
  https://alain-lessard.copper-dog.com
```

The Onward project records `onward.copper-dog.com` at DreamHost origin
`208.113.159.28`, but DreamHost assigned this hosted subdomain to
`173.236.136.184`. Cloudflare must keep the proxied `A` record pointed at the
DreamHost nameserver-reported origin for this specific hostname.

DreamHost's public API documentation now lists meta and DNS commands and notes
that formerly available domain-management commands have been removed. Hosted
subdomain creation and certificate setup were completed in the DreamHost panel.

Fresh public verification on 2026-07-01:

```bash
dig @chelsea.ns.cloudflare.com alain-lessard.copper-dog.com +short
curl -I https://alain-lessard.copper-dog.com
curl -I https://alain-lessard.copper-dog.com/book.html
curl -I https://alain-lessard.copper-dog.com/chapter-001.html
curl -I https://alain-lessard.copper-dog.com/downloads/alain-lessard-book-searchable.pdf
curl -I http://alain-lessard.copper-dog.com
```

Observed result: Cloudflare edge IPs resolve; the homepage, book page, chapter
page, and searchable PDF return `HTTP/2 200`; HTTP returns `301` to HTTPS.

Fresh public verification on 2026-07-02 after the `doc-web` rebuild and
supplemental-document archive update:

```bash
make deploy-static
curl -I https://alain-lessard.copper-dog.com/
curl -I https://alain-lessard.copper-dog.com/chapter-001.html
curl -I https://alain-lessard.copper-dog.com/chapter-016.html
curl -I 'https://alain-lessard.copper-dog.com/downloads/alains-song-searchable.pdf?v=20260702-docweb-r8'
curl -I 'https://alain-lessard.copper-dog.com/downloads/growing-up-on-the-farm-searchable.pdf?v=20260702-docweb-r8'
curl -fsSL https://alain-lessard.copper-dog.com/book.html
curl -fsSL 'https://alain-lessard.copper-dog.com/search-index.json?v=20260702-docweb-r8'
```

Observed result: the homepage, figure-heavy chapter, and table-heavy personal
records chapter return `HTTP/2 200`; the supplemental reader PDFs for
`Alain's Song` and `Growing Up on the Farm` also return `HTTP/2 200` on the
versioned URLs. The live home page references `assets/site.css?v=20260702-docweb-r8`,
the live book page references `assets/search.js?v=20260702-docweb-r8`, that
script fetches `search-index.json?v=20260702-docweb-r8`, the public search
index has 41 entries and no stale `pages/` URLs, and companion search rows
return the versioned reader PDF URLs. Versioned companion PDF links are required
because Cloudflare can retain stale bare PDF URLs for the cache window.

## Deploy Shape

The deploy helper uploads the static bundle over SFTP and writes a remote
`.deploy-manifest.json` so later deploys can remove stale files. It excludes
`_internal/` maintenance artifacts from publication.

The bundle may include large generated PDFs under `downloads/`. These are
intentionally not committed to GitHub, but are deployable artifacts generated by
the local scan/PDF pipeline.

## Audiobook Delivery

The reviewed audio files are ignored local artifacts, not Git payloads:

- 52 source tracks: `audiobook/script/*.mp3`
- Canonical contract: `audiobook/manifest.json`
- Complete generated file:
  `audiobook/generated/alain-lessard-complete-audiobook.mp3`
- Static release assets: `build/family-site/audiobook/`

The current complete file is 9:00:14 and approximately 494.6 MiB. The strict
site bundle contains 53 MP3 files: the complete audiobook plus all 52 tracks.
Prepare and validate it locally with:

```bash
make build-full-audiobook
make build-family-site RELEASE=1
make validate-family-site RELEASE=1
```

`make deploy-static` now depends on strict release validation, so a missing
track or complete audiobook blocks upload. After deployment, run:

```bash
make validate-family-site RELEASE=1 \
  PUBLIC_BASE=https://alain-lessard.copper-dog.com
```

That command checks all generated pages and local references, then verifies
the 53 public MP3s for `audio/mpeg`, positive `Content-Length`, and working
`206 Partial Content` byte-range requests.

Fresh production deployment and verification on 2026-07-16:

- Uploaded the 2.0 GiB `build/family-site/` bundle to
  `/home/onward_user/alain-lessard.copper-dog.com` over SFTP.
- The remote manifest sync removed two obsolete script filenames and published
  the semantic reading routes, compact listening-bar design, 52 individual
  tracks, and complete audiobook.
- `make validate-family-site RELEASE=1
  PUBLIC_BASE=https://alain-lessard.copper-dog.com` passed across 102 HTML
  pages, 398 local references, 59 search rows, and all 53 public audio assets.
- Browser inspection confirmed asset version `20260716-semantic-reader-r2`,
  homepage reading priority, the 52 track cards, complete-book player, semantic
  Read links, headphones badge, and no console warnings/errors.

## Portable Edition Delivery

Story 005 adds two ignored, reproducible local binaries to the existing release
bundle:

- EPUB source: `output/portable/alain-lessard-family-history.epub`
- EPUB public path: `downloads/alain-lessard-family-history.epub`
- M4B source:
  `audiobook/generated/alain-lessard-complete-audiobook.m4b`
- M4B public path: `audiobook/alain-lessard-complete-audiobook.m4b`
- Shared contract: `portable/manifest.json`

The 2026-07-17 strict release publishes both files and a
`reading-apps.html` help page. The generated `.htaccess` declares
`application/epub+zip` for EPUB and `audio/mp4` for M4B. Local validation passes
across 103 HTML pages and 401 local references; the EPUB is 90.0 MiB and the
chaptered M4B is 257.5 MiB.

Prepare the portable release with:

```bash
make build-portable-editions RELEASE=1
make validate-epub EPUBCHECK=1 EPUBCHECK_JAR=/path/to/epubcheck.jar
make validate-family-site RELEASE=1
```

After deployment, the existing strict public command additionally requires
both portable URLs to return their declared MIME type, exact generated byte
length, and working `206 Partial Content` byte ranges:

```bash
make validate-family-site RELEASE=1 \
  PUBLIC_BASE=https://alain-lessard.copper-dog.com
```

Fresh production deployment and verification on 2026-07-17:

- Uploaded the complete `build/family-site/` bundle over SFTP to
  `/home/onward_user/alain-lessard.copper-dog.com`, including `.htaccess`,
  `reading-apps.html`, the 94,390,319-byte EPUB, and the 269,966,138-byte M4B.
- `make validate-family-site RELEASE=1
  PUBLIC_BASE=https://alain-lessard.copper-dog.com` passed across 103 HTML
  pages, 401 local references, 59 search rows, all 53 MP3 assets, and both
  portable editions. The EPUB/M4B returned the declared MIME types, exact local
  lengths, and valid `206` byte ranges through Cloudflare.
- Browser inspection passed on desktop and at 390×844: the homepage and device
  help expose literal EPUB/M4B/help actions, the audiobook page exposes 52
  track cards and 53 audio players plus both M4B links, the asset version is
  `20260717-portable-editions-r1`, there is no horizontal overflow, and no
  console warnings/errors were recorded.
- The first sandboxed deploy attempt could not resolve DreamHost. That exposed
  and fixed a deploy-helper false-success path: `run_sftp` now waits for and
  requires a real zero child exit, with regression tests for failure and
  success. Never use an upload transcript alone as production proof.
