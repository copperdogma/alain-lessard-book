from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.audiobook import load_audiobook_catalog, probe_audio_file
from scripts.build_full_audiobook import build_full_audiobook


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def synthesize_mp3(path: Path, duration_seconds: float) -> None:
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
            "anullsrc=channel_layout=mono:sample_rate=44100",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "64k",
            str(path),
        ],
        check=True,
    )


@unittest.skipUnless(FFMPEG and FFPROBE, "ffmpeg and ffprobe are required")
class FullAudiobookBuildTests(unittest.TestCase):
    def test_build_merges_mono_tracks_with_silence_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthesize_mp3(root / "script" / "01-one.mp3", 0.25)
            synthesize_mp3(root / "script" / "02-two.mp3", 0.30)
            (root / "script" / "01-one.md").write_text("# One\n", encoding="utf-8")
            (root / "script" / "02-two.md").write_text("# Two\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "alain_lessard_audiobook_manifest_v4",
                        "title": "Fixture Audiobook",
                        "mode": "onward-style-narrative-audio",
                        "expected_track_count": 2,
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
                        "tracks": [
                            {
                                "track_number": number,
                                "title": title,
                                "script_path": f"script/{number:02d}-{title.lower()}.md",
                                "audio_path": f"script/{number:02d}-{title.lower()}.mp3",
                                "public_audio_path": f"audiobook/tracks/{number:02d}-{title.lower()}.mp3",
                                "source_ids": [f"chapter-{number:03d}"],
                                "target_entry_ids": [f"chapter-{number:03d}"],
                                "source_label": "Fixture source",
                                "word_count": 10,
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

            output = build_full_audiobook(manifest_path=manifest)
            probe = probe_audio_file(output)
            catalog = load_audiobook_catalog(manifest)
            expected_duration = (
                sum(track.probe.duration_seconds for track in catalog.tracks if track.probe)
                + catalog.full_audiobook.silence_between_tracks_seconds
            )

            self.assertEqual(probe.channels, 1)
            self.assertEqual(probe.sample_rate_hz, 44100)
            self.assertAlmostEqual(probe.duration_seconds, expected_duration, delta=0.15)
            self.assertEqual(probe.tags.get("title"), "Fixture Complete Audiobook")
            self.assertEqual(probe.tags.get("album"), "Fixture Audiobook")
            self.assertEqual(probe.tags.get("artist"), "Fixture Family")
            self.assertEqual(probe.tags.get("narrator"), "Fixture Narrator")

            with self.assertRaisesRegex(SystemExit, "Refusing to overwrite"):
                build_full_audiobook(manifest_path=manifest)


if __name__ == "__main__":
    unittest.main()
