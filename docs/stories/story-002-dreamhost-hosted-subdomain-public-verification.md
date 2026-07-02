---
title: "DreamHost hosted subdomain public verification"
status: "Done"
---

# DreamHost Hosted Subdomain Public Verification

## Context

The main book PDFs, Onward-style static site, and audio-script surface have been
built. The generated static bundle has been uploaded over SFTP to:

`/home/onward_user/alain-lessard.copper-dog.com`

Cloudflare DNS now has a proxied `A` record for
`alain-lessard.copper-dog.com` pointing at the DreamHost origin IP assigned to
this hosted subdomain.

Public HTTPS now serves the uploaded static archive.

## Goal

Make `https://alain-lessard.copper-dog.com` publicly serve the uploaded static
family archive.

## Scope

- Keep the existing Cloudflare DNS record pointed at DreamHost's assigned origin
  IP for this hosted subdomain.
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
- DreamHost nameservers returned `173.236.136.184` for
  `alain-lessard.copper-dog.com`; Cloudflare was updated to that origin with
  proxying enabled.
- DreamHost issued a Let's Encrypt certificate for
  `alain-lessard.copper-dog.com` expiring on 2026-09-30.
- `curl -I https://alain-lessard.copper-dog.com` returned `HTTP/2 200`.
- `curl -I https://alain-lessard.copper-dog.com/book.html` returned
  `HTTP/2 200`.
- `curl -I https://alain-lessard.copper-dog.com/chapter-001.html` returned
  `HTTP/2 200`.
- `curl -I https://alain-lessard.copper-dog.com/downloads/alain-lessard-book-searchable.pdf`
  returned `HTTP/2 200`.
- `curl -I http://alain-lessard.copper-dog.com` returned `301` to HTTPS.
- Body checks for `/`, `/book.html`, and `/chapter-001.html` matched Alain
  Lessard site content and did not match DreamHost's missing-site page.
- Public browser smoke checks confirmed the homepage, book/search page, and
  audio companion page render over HTTPS without the missing-site page.
- No local `DREAMHOST_API`/panel API credential or DreamHost CLI was found in
  the repo environment.
- Password-based SSH using the same DreamHost user did not expose a usable
  shell/control command for hosted-domain mapping; the available credential path
  remains SFTP upload only.
- DreamHost's current API overview says formerly available domain-management
  commands have been removed; the available documented API surface is meta and
  DNS commands, so hosted-subdomain creation is a panel/support action unless a
  separate internal DreamHost API credential/path is provided.

## DreamHost Panel Action Completed

Used DreamHost's **Manage Websites** flow:

1. Click **Add Website**.
2. Choose **Create a Subdomain** for `alain-lessard.copper-dog.com`.
3. Choose **Custom Setup**.
4. Select the existing file-management user used by the Onward deploy path
   (`onward_user`) unless DreamHost requires a different user.
5. Open **Advanced Settings** and set the web directory to:

   `alain-lessard.copper-dog.com`

   DreamHost treats this as the directory under the selected user's home. The
   folder already exists and contains the uploaded static bundle.
6. Complete setup, then allow DreamHost's hosting configuration time to update.
7. Check DreamHost's own nameservers for the assigned origin IP:
   `173.236.136.184`.
8. Update Cloudflare's proxied `A` record to that origin.
9. Add a free Let's Encrypt certificate in DreamHost's certificate flow and
   wait for the HTTPS vhost to present the issued certificate.

If the domain is already present but mapped to the wrong directory, open the
site in **Manage Websites**, go to **Settings**, modify **Directories**, and set
the web directory to `alain-lessard.copper-dog.com`.

Sources:

- DreamHost, "Adding a website and hosting":
  https://help.dreamhost.com/hc/en-us/articles/360049378932-Adding-a-website-and-hosting
- DreamHost, "Adding a subdomain":
  https://help.dreamhost.com/hc/en-us/articles/215457827-Adding-a-subdomain
- DreamHost, "Changing the web directory assigned to a domain":
  https://help.dreamhost.com/hc/en-us/articles/360041534491-Changing-the-web-directory-assigned-to-a-domain
- DreamHost, "Application programming interface overview":
  https://help.dreamhost.com/hc/en-us/articles/217560167-Application-programming-interface-overview

## Acceptance

- [x] `dig +short alain-lessard.copper-dog.com` returns public IPs after local DNS
  cache expiry.
- [x] `curl -I https://alain-lessard.copper-dog.com` returns success for the site
  homepage and does not serve DreamHost's missing-site page.
- [x] `curl -I https://alain-lessard.copper-dog.com/book.html` returns success.
- [x] `curl -I https://alain-lessard.copper-dog.com/chapter-001.html` returns
  success.
- [x] A browser smoke test confirms the homepage, book search, and audio
  companion page render publicly.
