# Alain Lessard Audio Companion

This folder contains final Onward-style Markdown scripts and reviewed MP3 tracks generated with ElevenLabs Multilingual v2 using the voice "Matilda" (voiceId: XrExE9yKIg1WjnnlVkGX).

Each script is a clean recording chapter. The scripts include narrative family history, stories, poems, memories, obituaries, and the two companion documents found with the book. Genealogy tables, personal-record forms, recipes, bibliography, and source lists remain in the readable website and PDFs instead of being narrated.

The reviewed chapter MP3s stay beside these scripts as ignored local media. `manifest.json` records their source and public paths, durations, reading-page mappings, and complete-audiobook settings.

Run `make build-full-audiobook` to create the complete MP3 and
`make build-m4b` to create the app-friendly chaptered edition. The M4B is one
44.1 kHz mono AAC-LC encoding pass over the 52 reviewed tracks, with the
manifest's two-second gaps, compact cover, publication/narrator metadata, and
exactly 52 named chapters; `portable/manifest.json` owns its format and output
contract.

Use `make validate-audiobook` to probe/hash/decode the source and complete MP3,
`make validate-m4b` for chapter/codec/cover/metadata checks, and
`make build-family-site RELEASE=1` plus `make validate-family-site RELEASE=1`
before deployment. The generated MP3 and M4B remain ignored local artifacts.
