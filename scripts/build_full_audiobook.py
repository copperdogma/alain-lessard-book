#!/usr/bin/env python3
"""Build one complete mono MP3 from the ordered audiobook manifest tracks."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

try:
    from scripts.audiobook import (
        DEFAULT_MANIFEST_PATH,
        AudiobookValidation,
        AudiobookManifestError,
        hash_file,
        load_audiobook_catalog,
        probe_audio_file,
        validate_probe,
    )
except ModuleNotFoundError:  # Direct `python scripts/...` execution.
    from audiobook import (  # type: ignore[no-redef]
        DEFAULT_MANIFEST_PATH,
        AudiobookValidation,
        AudiobookManifestError,
        hash_file,
        load_audiobook_catalog,
        probe_audio_file,
        validate_probe,
    )


DEFAULT_MP3_BIT_RATE = "128k"


def build_full_audiobook(
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    *,
    output: str | Path | None = None,
    force: bool = False,
    ffmpeg_bin: str | None = None,
) -> Path:
    try:
        catalog = load_audiobook_catalog(manifest_path)
    except AudiobookManifestError as exc:
        raise SystemExit(str(exc)) from exc
    missing = [track.audio_source_path for track in catalog.tracks if not track.is_available]
    if missing:
        raise SystemExit(
            "Cannot build the complete audiobook; missing track MP3s:\n"
            + "\n".join(f"- {path}" for path in missing)
        )
    output_path = (
        Path(output).expanduser().resolve()
        if output is not None
        else catalog.full_audiobook.audio_source_path
    )
    if output_path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing complete audiobook without --force: {output_path}")
    preflight = AudiobookValidation()
    hashes: dict[str, int] = {}
    expected_duration = 0.0
    for track in catalog.tracks:
        label = f"Track {track.track_number:02d}"
        preflight.require(
            track.script_source_path.stem == track.audio_source_path.stem,
            f"{label} script/audio filename stems do not match.",
        )
        if track.probe is None:
            preflight.errors.append(f"{label} could not be probed before assembly.")
            continue
        validate_probe(catalog.profile, track.probe, label, preflight)
        expected_duration += track.probe.duration_seconds
        if track.configured_duration_seconds is not None:
            preflight.require(
                abs(track.probe.duration_seconds - track.configured_duration_seconds) <= 0.25,
                f"{label} duration differs from its manifest value.",
            )
        digest = hash_file(track.audio_source_path)
        duplicate_number = hashes.get(digest)
        preflight.require(
            duplicate_number is None,
            f"{label} duplicates track {duplicate_number:02d} byte-for-byte."
            if duplicate_number is not None
            else "",
        )
        hashes[digest] = track.track_number
    expected_duration += catalog.full_audiobook.silence_between_tracks_seconds * max(
        0,
        len(catalog.tracks) - 1,
    )
    if preflight.errors:
        raise SystemExit(
            "Cannot build the complete audiobook; track preflight failed:\n"
            + "\n".join(f"- {error}" for error in preflight.errors)
        )
    executable = ffmpeg_bin or shutil.which("ffmpeg")
    if not executable:
        raise SystemExit("Missing required `ffmpeg` binary.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_rate = catalog.profile.sample_rate_hz
    channel_layout = "mono" if catalog.profile.channels == 1 else "stereo"
    command = [executable, "-hide_banner", "-loglevel", "error", "-y" if force else "-n"]
    filter_parts: list[str] = []
    concat_inputs: list[str] = []
    input_index = 0
    silence_seconds = catalog.full_audiobook.silence_between_tracks_seconds
    for track_index, track in enumerate(catalog.tracks):
        command.extend(["-i", str(track.audio_source_path)])
        filter_parts.append(
            f"[{input_index}:a]aresample={sample_rate},"
            f"aformat=sample_fmts=fltp:channel_layouts={channel_layout}[a{input_index}]"
        )
        concat_inputs.append(f"[a{input_index}]")
        input_index += 1
        if track_index == len(catalog.tracks) - 1 or silence_seconds <= 0:
            continue
        command.extend(
            [
                "-f",
                "lavfi",
                "-t",
                f"{silence_seconds:g}",
                "-i",
                f"anullsrc=channel_layout={channel_layout}:sample_rate={sample_rate}",
            ]
        )
        filter_parts.append(
            f"[{input_index}:a]aformat=sample_fmts=fltp:channel_layouts={channel_layout}[a{input_index}]"
        )
        concat_inputs.append(f"[a{input_index}]")
        input_index += 1
    filter_parts.append(f"{''.join(concat_inputs)}concat=n={len(concat_inputs)}:v=0:a=1[outa]")
    full = catalog.full_audiobook
    command.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[outa]",
            "-ar",
            str(sample_rate),
            "-ac",
            str(catalog.profile.channels),
            "-c:a",
            "libmp3lame",
            "-b:a",
            DEFAULT_MP3_BIT_RATE,
            "-id3v2_version",
            "3",
            "-metadata",
            f"title={full.title}",
            "-metadata",
            f"album={full.album}",
            "-metadata",
            f"artist={full.artist}",
            "-metadata",
            f"narrator={full.narrator}",
            "-metadata",
            "genre=Audiobook",
            str(output_path),
        ]
    )
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg failed while building the complete audiobook: {exc}") from exc
    try:
        probe = probe_audio_file(output_path)
    except AudiobookManifestError as exc:
        raise SystemExit(f"Built complete audiobook could not be verified: {exc}") from exc
    if probe.channels != catalog.profile.channels or probe.sample_rate_hz != sample_rate:
        raise SystemExit(
            "Built complete audiobook has an unexpected format: "
            f"{probe.sample_rate_hz} Hz / {probe.channels} channels"
        )
    tolerance = max(2.0, len(catalog.tracks) * 0.1)
    if abs(probe.duration_seconds - expected_duration) > tolerance:
        raise SystemExit(
            "Built complete audiobook has an unexpected duration: "
            f"{probe.duration_seconds:.3f}s, expected {expected_duration:.3f}s "
            f"within {tolerance:.1f}s"
        )
    for key, expected in (
        ("title", catalog.full_audiobook.title),
        ("album", catalog.full_audiobook.album),
        ("artist", catalog.full_audiobook.artist),
        ("narrator", catalog.full_audiobook.narrator),
    ):
        if probe.tags.get(key) != expected:
            raise SystemExit(
                f"Built complete audiobook metadata `{key}` is {probe.tags.get(key)!r}, expected {expected!r}."
            )
    return output_path


def cli_main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--output", help="Override the manifest complete-audiobook output path.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    args = parser.parse_args()
    output_path = build_full_audiobook(
        manifest_path=args.manifest,
        output=args.output,
        force=args.force,
    )
    probe = probe_audio_file(output_path)
    print(f"Built complete audiobook: {output_path}")
    print(f"Duration: {probe.duration_seconds:.3f} seconds")
    print(f"Size: {probe.size_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
