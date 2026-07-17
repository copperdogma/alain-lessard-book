from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audiobook import (
    AudioProbe,
    AudiobookManifestError,
    load_audiobook_catalog,
    tracks_by_target_entry_id,
    validate_audiobook_catalog,
)
from scripts.build_family_site import (
    AUDIO_JS,
    copy_audiobook_assets,
    render_audiobook,
    render_entry_audio_section,
)


def write_manifest(root: Path, tracks: list[dict[str, object]]) -> Path:
    for track in tracks:
        script_path = root / str(track["script_path"])
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(f"# {track['title']}\n", encoding="utf-8")
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "alain_lessard_audiobook_manifest_v4",
                "title": "Fixture Audiobook",
                "mode": "onward-style-narrative-audio",
                "expected_track_count": len(tracks),
                "audio_profile": {
                    "codec": "mp3",
                    "sample_rate_hz": 44100,
                    "channels": 1,
                },
                "full_audiobook": {
                    "title": "Fixture Complete Audiobook",
                    "audio_path": "generated/fixture-complete.mp3",
                    "public_audio_path": "audiobook/fixture-complete.mp3",
                    "silence_between_tracks_seconds": 0.2,
                    "album": "Fixture Audiobook",
                    "artist": "Fixture Family",
                    "narrator": "Fixture Narrator",
                    "duration_seconds": None,
                },
                "tracks": tracks,
                "skipped_entries": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def track(
    number: int,
    title: str,
    *,
    targets: list[str],
    public_audio_path: str | None = None,
) -> dict[str, object]:
    slug = f"{number:02d}-{title.lower().replace(' ', '-')}"
    return {
        "track_number": number,
        "title": title,
        "script_path": f"script/{slug}.md",
        "audio_path": f"script/{slug}.mp3",
        "public_audio_path": public_audio_path or f"audiobook/tracks/{slug}.mp3",
        "source_ids": targets or ["manual:preamble"],
        "target_entry_ids": targets,
        "source_label": "Fixture source",
        "word_count": 10,
        "status": "audio-reviewed",
        "duration_seconds": 1.0,
    }


class AudiobookCatalogTests(unittest.TestCase):
    def test_catalog_supports_shared_and_multiple_entry_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(
                root,
                [
                    track(1, "One", targets=["chapter-001"]),
                    track(2, "Two", targets=["chapter-001", "chapter-002"]),
                    track(3, "Three", targets=[]),
                ],
            )

            catalog = load_audiobook_catalog(manifest, probe_audio=False)
            mapping = tracks_by_target_entry_id(catalog)

            self.assertEqual([row.track_number for row in mapping["chapter-001"]], [1, 2])
            self.assertEqual([row.track_number for row in mapping["chapter-002"]], [2])
            self.assertNotIn("manual:preamble", mapping)

    def test_catalog_rejects_non_sequential_track_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(
                root,
                [track(1, "One", targets=[]), track(3, "Three", targets=[])],
            )

            with self.assertRaisesRegex(AudiobookManifestError, "sequential"):
                load_audiobook_catalog(manifest, probe_audio=False)

    def test_catalog_rejects_unsafe_public_audio_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(
                root,
                [
                    track(
                        1,
                        "One",
                        targets=[],
                        public_audio_path="audiobook/tracks/01-café track.mp3",
                    )
                ],
            )

            with self.assertRaisesRegex(AudiobookManifestError, "ASCII"):
                load_audiobook_catalog(manifest, probe_audio=False)

    def test_release_validation_requires_tracks_and_complete_audiobook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(root, [track(1, "One", targets=[])])
            catalog = load_audiobook_catalog(manifest, probe_audio=False)

            result = validate_audiobook_catalog(catalog, release=True, decode=False)

            self.assertFalse(result.ok)
            self.assertTrue(any("track 01" in error.lower() for error in result.errors))
            self.assertTrue(any("complete audiobook" in error.lower() for error in result.errors))

    def test_release_validation_rejects_duplicate_track_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(
                root,
                [track(1, "One", targets=[]), track(2, "Two", targets=[])],
            )
            duplicate_bytes = b"fixture-audio"
            for relative_path in (
                "script/01-one.mp3",
                "script/02-two.mp3",
                "generated/fixture-complete.mp3",
            ):
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(duplicate_bytes)
            catalog = load_audiobook_catalog(manifest, probe_audio=False)

            def fixture_probe(path: Path) -> AudioProbe:
                is_full = path.name == "fixture-complete.mp3"
                return AudioProbe(
                    path=path,
                    duration_seconds=2.2 if is_full else 1.0,
                    size_bytes=path.stat().st_size,
                    codec="mp3",
                    sample_rate_hz=44100,
                    channels=1,
                    bit_rate=64000,
                    tags=(
                        {
                            "title": "Fixture Complete Audiobook",
                            "album": "Fixture Audiobook",
                            "artist": "Fixture Family",
                            "narrator": "Fixture Narrator",
                        }
                        if is_full
                        else {}
                    ),
                )

            with patch("scripts.audiobook.probe_audio_file", side_effect=fixture_probe):
                result = validate_audiobook_catalog(catalog, release=True, decode=False)

            self.assertFalse(result.ok)
            self.assertTrue(any("duplicates track 01" in error.lower() for error in result.errors))

    def test_asset_copy_uses_public_paths_once_and_keeps_manifest_internal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(
                root,
                [track(1, "One", targets=[]), track(2, "Two", targets=[])],
            )
            expected_bytes = 0
            for relative_path, payload in (
                ("script/01-one.mp3", b"one"),
                ("script/02-two.mp3", b"two-two"),
                ("generated/fixture-complete.mp3", b"complete"),
            ):
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                expected_bytes += len(payload)
            catalog = load_audiobook_catalog(manifest, probe_audio=False)
            output = root / "site"

            copied_count, copied_bytes = copy_audiobook_assets(catalog, output)

            self.assertEqual(copied_count, 3)
            self.assertEqual(copied_bytes, expected_bytes)
            self.assertEqual((output / "audiobook/tracks/01-one.mp3").read_bytes(), b"one")
            self.assertEqual((output / "audiobook/tracks/02-two.mp3").read_bytes(), b"two-two")
            self.assertEqual((output / "audiobook/fixture-complete.mp3").read_bytes(), b"complete")
            self.assertTrue((output / "_internal/audiobook/manifest.json").is_file())
            self.assertFalse(any((output / "script").glob("*.mp3")))

    def test_site_rendering_keeps_shared_and_multi_entry_tracks_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_manifest(
                root,
                [
                    track(1, "One", targets=["chapter-001"]),
                    track(2, "Two", targets=["chapter-001", "chapter-002"]),
                ],
            )
            for filename in ("01-one.mp3", "02-two.mp3"):
                (root / "script" / filename).write_bytes(filename.encode("ascii"))
            catalog = load_audiobook_catalog(manifest, probe_audio=False)
            mapping = tracks_by_target_entry_id(catalog)

            page = render_audiobook(
                catalog,
                {
                    1: ("read-01-one.html", "One"),
                    2: ("read-02-two.html", "Two"),
                },
            )
            entry_panel = render_entry_audio_section(mapping["chapter-001"])

            self.assertEqual(page.count('class="audio-track-card"'), 2)
            self.assertEqual(page.count('class="button" href="read-'), 2)
            self.assertIn('href="read-01-one.html"', page)
            self.assertIn('href="read-02-two.html"', page)
            self.assertNotIn("Download complete audiobook", page)
            self.assertIn("has not been assembled for this local preview", page)
            self.assertEqual(entry_panel.count('class="listen-bar"'), 2)
            self.assertEqual(entry_panel.count("<audio"), 2)
            self.assertNotIn("<details", entry_panel)
            self.assertIn("Track 02", entry_panel)
            self.assertIn('class="listen-icon-mark"', entry_panel)
            self.assertNotIn("&#9654;", entry_panel)
            self.assertIn("localStorage", AUDIO_JS)
            self.assertIn('addEventListener("loadedmetadata"', AUDIO_JS)
            self.assertIn('addEventListener("play"', AUDIO_JS)
            self.assertIn("other.pause()", AUDIO_JS)


if __name__ == "__main__":
    unittest.main()
