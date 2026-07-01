---
name: deploy
description: Deploy the current static site bundle to DreamHost over SFTP with lightweight public verification
user-invocable: true
---

# /deploy

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Deploy the current static site bundle to `onward.copper-dog.com` using the
verified DreamHost shared-hosting SFTP path.

## References

- `docs/infrastructure.md` — hosting, DNS, and remote path truth
- `docs/RUNBOOK.md` — current command surface
- `scripts/deploy_static_site.py` — backing upload command
- local `.env` (gitignored) — DreamHost credentials and default source path

## Expected Duration

Usually under 2 minutes: upload time depends on the bundle size and DreamHost
responsiveness.

## Steps

1. **Preflight**
   - Confirm `docs/infrastructure.md` still matches the target host/path.
   - Confirm `python -m pip install -r requirements-deploy.txt` has been run in
     the local environment.
   - Confirm the local `.env` contains:
     - `DREAMHOST_SFTP_HOST`
     - `DREAMHOST_SFTP_USERNAME`
     - `DREAMHOST_SFTP_PASSWORD`
     - `DREAMHOST_SITE_PATH`
     - optionally `DREAMHOST_DEPLOY_SOURCE_DIR`
   - Confirm the deploy source directory exists and contains `index.html`.
   - If the deploy source is `build/family-site/`, remember that `_internal/`
     is treated as a local maintenance surface and is intentionally excluded
     from the published payload.

2. **Upload**
   - Run:
     - `python scripts/deploy_static_site.py`
   - Or override the source explicitly:
     - `python scripts/deploy_static_site.py --source /absolute/path/to/static-bundle`

3. **Verify**
   - `curl -I https://onward.copper-dog.com`
   - `curl -s https://onward.copper-dog.com | head`
   - `curl -I https://onward.copper-dog.com/chapter-001.html`
   - If browser-style public page inspection is available, open the homepage and
     one chapter page and confirm expected content rendered from the uploaded
     bundle.

4. **Report**
   - Source directory uploaded
   - Remote DreamHost path used
   - Whether upload completed without SFTP errors
   - Public verification results and any known gaps

## On Failure

1. Report the exact failing command and output.
2. Re-check the `.env` credentials and source directory.
3. Verify the public DNS/host/path facts in `docs/infrastructure.md`.
4. Do not claim a deploy succeeded unless the public site is freshly verified.

## Guardrails

- Never expose or commit the DreamHost password.
- Never claim success from a local upload log alone; verify the public hostname.
- Never widen this into build/runtime work; this skill only ships an existing
  static bundle.
