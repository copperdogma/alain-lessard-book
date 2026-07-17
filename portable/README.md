# Portable Editions

`manifest.json` is the tracked contract for the app-friendly reading and
listening editions. It owns publication metadata, stable generated/public
paths, cover sources, size limits, EPUB content expectations, and M4B codec and
chapter settings.

Build and validate both formats with:

```bash
make build-portable-editions RELEASE=1
make validate-portable-editions
```

To include the official EPUBCheck jar in the maintained validation command:

```bash
make validate-epub EPUBCHECK=1 EPUBCHECK_JAR=/path/to/epubcheck.jar
```

Generated files are intentionally ignored:

- `output/portable/alain-lessard-family-history.epub`
- `audiobook/generated/alain-lessard-complete-audiobook.m4b`

The static site copies them to their manifest-declared paths only when present;
release mode requires both and validates their structure. Source scans,
accepted HTML, narration scripts, and reviewed MP3 tracks remain the canonical
inputs.
