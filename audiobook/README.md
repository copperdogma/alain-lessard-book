# Alain Lessard Audio Companion

This folder contains final Onward-style Markdown scripts and reviewed MP3 tracks generated with ElevenLabs Multilingual v2 using the voice "Matilda" (voiceId: XrExE9yKIg1WjnnlVkGX).

Each script is a clean recording chapter. The scripts include narrative family history, stories, poems, memories, obituaries, and the two companion documents found with the book. Genealogy tables, personal-record forms, recipes, bibliography, and source lists remain in the readable website and PDFs instead of being narrated.

The reviewed chapter MP3s stay beside these scripts as ignored local media. `manifest.json` records their source and public paths, durations, reading-page mappings, and complete-audiobook settings.

Run `make build-full-audiobook` to create the complete listening file, `make validate-audiobook` to probe/hash/decode the whole set, and `make build-family-site RELEASE=1` plus `make validate-family-site RELEASE=1` before deployment.
