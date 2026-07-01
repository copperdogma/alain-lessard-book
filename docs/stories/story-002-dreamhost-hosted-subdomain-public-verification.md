---
title: "DreamHost hosted subdomain public verification"
status: "Blocked"
---

# DreamHost Hosted Subdomain Public Verification

## Context

The main book PDFs, Onward-style static site, and audio-script surface have been
built. The generated static bundle has been uploaded over SFTP to:

`/home/onward_user/alain-lessard.copper-dog.com`

Cloudflare DNS now has a proxied `A` record for
`alain-lessard.copper-dog.com` pointing at the same DreamHost origin IP used by
the Onward site.

Public requests still return DreamHost's `Site Not Found` page, which means the
DreamHost hosted subdomain or virtual host has not been created/mapped to the
uploaded directory yet.

## Goal

Make `https://alain-lessard.copper-dog.com` publicly serve the uploaded static
family archive.

## Scope

- Keep the existing Cloudflare DNS record unless DreamHost assigns a different
  origin IP for this hosted subdomain.
- Create or update the DreamHost hosted subdomain so
  `alain-lessard.copper-dog.com` maps to
  `/home/onward_user/alain-lessard.copper-dog.com`.
- Do not reprocess scans or rebuild PDFs unless the site bundle changes.
- Do not expose or commit DreamHost or Cloudflare credentials.

## Current Evidence

- `dig @chelsea.ns.cloudflare.com alain-lessard.copper-dog.com +short`
  returned Cloudflare edge IPs.
- Cloudflare DNS record id:
  `4bdf435e1aba643e02f6db6011132dd0`.
- `curl --resolve alain-lessard.copper-dog.com:443:104.21.43.33
  https://alain-lessard.copper-dog.com` returned `HTTP/2 200`, but the body was
  DreamHost's `Site Not Found` page.
- `curl --resolve alain-lessard.copper-dog.com:443:104.21.43.33
  https://alain-lessard.copper-dog.com/book.html` returned `HTTP/2 404`.
- No local `DREAMHOST_API`/panel API credential or DreamHost CLI was found in
  the repo environment.

## Acceptance

- `dig +short alain-lessard.copper-dog.com` returns public IPs after local DNS
  cache expiry.
- `curl -I https://alain-lessard.copper-dog.com` returns success for the site
  homepage and does not serve DreamHost's missing-site page.
- `curl -I https://alain-lessard.copper-dog.com/book.html` returns success.
- `curl -I https://alain-lessard.copper-dog.com/chapter-001.html` returns
  success.
- A browser smoke test confirms the homepage, book search, and audio companion
  page render publicly.
