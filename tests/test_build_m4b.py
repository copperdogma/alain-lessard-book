from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.audiobook import load_audiobook_catalog
from scripts.build_m4b import build_m4b, m4b_chapters, validate_m4b
from scripts.portable_editions import load_portable_catalog


ROOT = Path(__file__).resolve().parents[1]
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def synthesize_mp3(path: Path, frequency: int, duration_seconds: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-t",
            f"{duration_seconds:g}",
            "-i",
            f"sine=frequency={frequency}:sample_rate=44100",
            "-ac",
            "1",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "64k",
            str(path),
        ],
        check=True,
    )


def write_audio_manifest(root: Path) -> Path:
    for number, title, frequency, duration in ((1, "One", 440, 0.35), (2, "Two", 660, 0.40)):
        synthesize_mp3(root / "script" / f"{number:02d}-{title.lower()}.mp3", frequency, duration)
        (root / "script" / f"{number:02d}-{title.lower()}.md").write_text(f"# {title}\n", encoding="utf-8")
    manifest = root / "audiobook-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "alain_lessard_audiobook_manifest_v4",
                "title": "Fixture Audiobook",
                "mode": "onward-style-narrative-audio",
                "expected_track_count": 2,
                "audio_profile": {"codec": "mp3", "sample_rate_hz": 44100, "channels": 1},
                "full_audiobook": {
                    "title": "Fixture Complete Audiobook",
                    "audio_path": "generated/fixture.mp3",
                    "public_audio_path": "audiobook/fixture.mp3",
                    "silence_between_tracks_seconds": 0.2,
                    "album": "Fixture Audiobook",
                    "artist": "Fixture Family",
                    "narrator": "Fixture Narrator",
                    "duration_seconds": None,
                },
                "tracks": [
                    {
                        "track_number": number,
                        "title": title,
                        "script_path": f"script/{number:02d}-{title.lower()}.md",
                        "audio_path": f"script/{number:02d}-{title.lower()}.mp3",
                        "public_audio_path": f"audiobook/tracks/{number:02d}-{title.lower()}.mp3",
                        "source_ids": [f"fixture:{number}"],
                        "target_entry_ids": [],
                        "source_label": "Fixture",
                        "word_count": 1,
                        "status": "audio-reviewed",
                        "duration_seconds": None,
                    }
                    for number, title in ((1, "One"), (2, "Two"))
                ],
                "skipped_entries": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def write_portable_manifest(root: Path, cover: Path) -> Path:
    relative_cover = cover.relative_to(ROOT).as_posix()
    manifest = root / "portable-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "alain_portable_editions_v1",
                "publication": {
                    "identifier": "urn:uuid:fixture",
                    "title": "Fixture",
                    "subtitle": "Fixture",
                    "language": "en-CA",
                    "author": "Fixture Family",
                    "publisher": "Fixture Family",
                    "original_publication_year": "1987",
                    "modified": "2026-07-17T20:00:00Z",
                    "description": "Fixture",
                    "source_url": "https://example.test/",
                    "cover_source_path": relative_cover,
                    "cover_output_path": f"{root.relative_to(ROOT).as_posix()}/generated-cover.jpg",
                },
                "epub": {
                    "output_path": f"{root.relative_to(ROOT).as_posix()}/fixture.epub",
                    "public_path": "downloads/fixture.epub",
                    "media_type": "application/epub+zip",
                },
                "m4b": {
                    "output_path": f"{root.relative_to(ROOT).as_posix()}/fixture.m4b",
                    "public_path": "audiobook/fixture.m4b",
                    "media_type": "audio/mp4",
                    "codec": "aac",
                    "profile": "AAC Low Complexity",
                    "bit_rate": "64k",
                    "sample_rate_hz": 44100,
                    "channels": 1,
                    "expected_chapter_count": 2,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


@unittest.skipUnless(FFMPEG and FFPROBE, "ffmpeg and ffprobe are required")
class M4BBuildTests(unittest.TestCase):
    def test_build_m4b_has_cover_metadata_and_exact_chapters(self) -> None:
        (ROOT / "tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            root = Path(tmp)
            audiobook_manifest = write_audio_manifest(root)
            cover = root / "cover.jpg"
            Image.new("RGB", (400, 600), "#38584f").save(cover, "JPEG")
            portable_manifest = write_portable_manifest(root, cover)

            output = build_m4b(audiobook_manifest, portable_manifest)
            audiobook = load_audiobook_catalog(audiobook_manifest)
            portable = load_portable_catalog(portable_manifest)
            validation = validate_m4b(output, audiobook, portable)
            chapters = m4b_chapters(audiobook)

            self.assertTrue(validation.ok, validation.errors)
            self.assertEqual([chapter.title for chapter in chapters], ["One", "Two"])
            self.assertEqual(chapters[0].start_ms, 0)
            self.assertEqual(chapters[0].end_ms, chapters[1].start_ms)
            self.assertGreater(output.stat().st_size, 1_000)
            with self.assertRaisesRegex(Exception, "Refusing to overwrite"):
                build_m4b(audiobook_manifest, portable_manifest)


if __name__ == "__main__":
    unittest.main()
