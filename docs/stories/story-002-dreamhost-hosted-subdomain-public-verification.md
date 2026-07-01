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
- Password-based SSH using the same DreamHost user did not expose a usable
  shell/control command for hosted-domain mapping; the available credential path
  remains SFTP upload only.
- DreamHost's current API overview says formerly available domain-management
  commands have been removed; the available documented API surface is meta and
  DNS commands, so hosted-subdomain creation is a panel/support action unless a
  separate internal DreamHost API credential/path is provided.

## DreamHost Panel Action

Use DreamHost's **Manage Websites** flow:

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

- `dig +short alain-lessard.copper-dog.com` returns public IPs after local DNS
  cache expiry.
- `curl -I https://alain-lessard.copper-dog.com` returns success for the site
  homepage and does not serve DreamHost's missing-site page.
- `curl -I https://alain-lessard.copper-dog.com/book.html` returns success.
- `curl -I https://alain-lessard.copper-dog.com/chapter-001.html` returns
  success.
- A browser smoke test confirms the homepage, book search, and audio companion
  page render publicly.
