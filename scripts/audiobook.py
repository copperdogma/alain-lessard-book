#!/usr/bin/env python3
"""Canonical audiobook manifest loading, probing, mapping, and validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = ROOT / "audiobook" / "manifest.json"
SCHEMA_VERSION = "alain_lessard_audiobook_manifest_v4"
ASCII_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class AudiobookManifestError(ValueError):
    """Raised when the canonical audiobook manifest is invalid."""


@dataclass(frozen=True)
class AudioProfile:
    codec: str
    sample_rate_hz: int
    channels: int


@dataclass(frozen=True)
class AudioProbe:
    path: Path
    duration_seconds: float
    size_bytes: int
    codec: str
    sample_rate_hz: int
    channels: int
    bit_rate: int | None
    tags: dict[str, str]


@dataclass(frozen=True)
class AudiobookTrack:
    track_number: int
    title: str
    script_source_path: Path
    script_manifest_path: str
    audio_source_path: Path
    audio_manifest_path: str
    public_audio_path: str
    source_ids: tuple[str, ...]
    target_entry_ids: tuple[str, ...]
    source_label: str
    word_count: int
    status: str
    configured_duration_seconds: float | None
    probe: AudioProbe | None

    @property
    def duration_seconds(self) -> float | None:
        return self.probe.duration_seconds if self.probe else self.configured_duration_seconds

    @property
    def is_available(self) -> bool:
        return self.audio_source_path.is_file()


@dataclass(frozen=True)
class FullAudiobook:
    title: str
    audio_source_path: Path
    audio_manifest_path: str
    public_audio_path: str
    silence_between_tracks_seconds: float
    album: str
    artist: str
    narrator: str
    configured_duration_seconds: float | None
    probe: AudioProbe | None

    @property
    def duration_seconds(self) -> float | None:
        return self.probe.duration_seconds if self.probe else self.configured_duration_seconds

    @property
    def is_available(self) -> bool:
        return self.audio_source_path.is_file()


@dataclass(frozen=True)
class AudiobookCatalog:
    title: str
    mode: str
    manifest_path: Path
    expected_track_count: int
    profile: AudioProfile
    tracks: tuple[AudiobookTrack, ...]
    full_audiobook: FullAudiobook
    preferred_voice: dict[str, str]
    note: str
    skipped_entries: tuple[dict[str, object], ...]


@dataclass
class AudiobookValidation:
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)


def required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` must be a non-empty string.")
    return value.strip()


def optional_duration(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or float(value) < 0:
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` must be a number >= 0 or null.")
    return float(value)


def string_list(value: object, field_name: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list) or (not allow_empty and not value):
        qualifier = "a non-empty array" if not allow_empty else "an array"
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` must be {qualifier} of strings.")
    normalized: list[str] = []
    for index, item in enumerate(value):
        normalized.append(required_string(item, f"{field_name}[{index}]"))
    if len(normalized) != len(set(normalized)):
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` contains duplicate values.")
    return tuple(normalized)


def relative_manifest_path(value: object, field_name: str) -> str:
    normalized = required_string(value, field_name).replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` must be a safe relative path.")
    return path.as_posix()


def public_audio_path(value: object, field_name: str, *, tracks_only: bool = False) -> str:
    normalized = relative_manifest_path(value, field_name)
    path = PurePosixPath(normalized)
    if any(not ASCII_PATH_SEGMENT.fullmatch(segment) for segment in path.parts):
        raise AudiobookManifestError(
            f"Audiobook manifest `{field_name}` must use stable ASCII path segments containing only letters, numbers, dots, underscores, or hyphens."
        )
    required_prefix = ("audiobook", "tracks") if tracks_only else ("audiobook",)
    if path.parts[: len(required_prefix)] != required_prefix:
        expected = "/".join(required_prefix) + "/"
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` must stay within `{expected}`.")
    if path.suffix.lower() != ".mp3":
        raise AudiobookManifestError(f"Audiobook manifest `{field_name}` must point to an MP3 file.")
    return normalized


def probe_audio_file(path: Path, *, ffprobe_bin: str | None = None) -> AudioProbe:
    executable = ffprobe_bin or shutil.which("ffprobe")
    if not executable:
        raise AudiobookManifestError("Missing required `ffprobe` binary.")
    if not path.is_file():
        raise AudiobookManifestError(f"Audio file does not exist: {path}")
    result = subprocess.run(
        [
            executable,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise AudiobookManifestError(f"ffprobe could not read {path}: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AudiobookManifestError(f"ffprobe returned invalid JSON for {path}: {exc}") from exc
    stream = next(
        (row for row in payload.get("streams", []) if row.get("codec_type") == "audio"),
        None,
    )
    if not isinstance(stream, dict):
        raise AudiobookManifestError(f"No audio stream found in {path}")
    format_row = payload.get("format") or {}
    try:
        duration_seconds = float(format_row["duration"])
        size_bytes = int(format_row.get("size") or path.stat().st_size)
        sample_rate_hz = int(stream["sample_rate"])
        channels = int(stream["channels"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AudiobookManifestError(f"Incomplete audio metadata for {path}: {exc}") from exc
    bit_rate_value = stream.get("bit_rate") or format_row.get("bit_rate")
    try:
        bit_rate = int(bit_rate_value) if bit_rate_value is not None else None
    except (TypeError, ValueError):
        bit_rate = None
    tags = {
        str(key).lower(): str(value)
        for key, value in (format_row.get("tags") or {}).items()
        if value is not None
    }
    return AudioProbe(
        path=path,
        duration_seconds=duration_seconds,
        size_bytes=size_bytes,
        codec=str(stream.get("codec_name") or ""),
        sample_rate_hz=sample_rate_hz,
        channels=channels,
        bit_rate=bit_rate,
        tags=tags,
    )


def load_audiobook_catalog(
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    *,
    probe_audio: bool = True,
) -> AudiobookCatalog:
    resolved_manifest = Path(manifest_path).expanduser().resolve()
    if not resolved_manifest.is_file():
        raise AudiobookManifestError(f"Audiobook manifest not found: {resolved_manifest}")
    try:
        payload = json.loads(resolved_manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AudiobookManifestError(f"Invalid audiobook manifest JSON: {exc}") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise AudiobookManifestError(f"Audiobook manifest must use schema_version `{SCHEMA_VERSION}`.")

    title = required_string(payload.get("title"), "title")
    mode = required_string(payload.get("mode"), "mode")
    expected_track_count = payload.get("expected_track_count")
    if not isinstance(expected_track_count, int) or expected_track_count < 1:
        raise AudiobookManifestError("Audiobook manifest `expected_track_count` must be an integer greater than 0.")
    profile_payload = payload.get("audio_profile")
    if not isinstance(profile_payload, dict):
        raise AudiobookManifestError("Audiobook manifest `audio_profile` must be an object.")
    codec = required_string(profile_payload.get("codec"), "audio_profile.codec")
    sample_rate_hz = profile_payload.get("sample_rate_hz")
    channels = profile_payload.get("channels")
    if not isinstance(sample_rate_hz, int) or sample_rate_hz < 1:
        raise AudiobookManifestError("Audiobook manifest `audio_profile.sample_rate_hz` must be a positive integer.")
    if not isinstance(channels, int) or channels < 1:
        raise AudiobookManifestError("Audiobook manifest `audio_profile.channels` must be a positive integer.")
    profile = AudioProfile(codec=codec, sample_rate_hz=sample_rate_hz, channels=channels)

    full_payload = payload.get("full_audiobook")
    if not isinstance(full_payload, dict):
        raise AudiobookManifestError("Audiobook manifest `full_audiobook` must be an object.")
    full_audio_manifest_path = relative_manifest_path(full_payload.get("audio_path"), "full_audiobook.audio_path")
    full_source_path = (resolved_manifest.parent / full_audio_manifest_path).resolve()
    full_public_path = public_audio_path(full_payload.get("public_audio_path"), "full_audiobook.public_audio_path")
    silence_seconds = full_payload.get("silence_between_tracks_seconds")
    if not isinstance(silence_seconds, (int, float)) or float(silence_seconds) < 0:
        raise AudiobookManifestError(
            "Audiobook manifest `full_audiobook.silence_between_tracks_seconds` must be a number >= 0."
        )
    full_probe = probe_audio_file(full_source_path) if probe_audio and full_source_path.is_file() else None
    full_audiobook = FullAudiobook(
        title=required_string(full_payload.get("title"), "full_audiobook.title"),
        audio_source_path=full_source_path,
        audio_manifest_path=full_audio_manifest_path,
        public_audio_path=full_public_path,
        silence_between_tracks_seconds=float(silence_seconds),
        album=required_string(full_payload.get("album"), "full_audiobook.album"),
        artist=required_string(full_payload.get("artist"), "full_audiobook.artist"),
        narrator=required_string(full_payload.get("narrator"), "full_audiobook.narrator"),
        configured_duration_seconds=optional_duration(
            full_payload.get("duration_seconds"),
            "full_audiobook.duration_seconds",
        ),
        probe=full_probe,
    )

    tracks_payload = payload.get("tracks")
    if not isinstance(tracks_payload, list) or not tracks_payload:
        raise AudiobookManifestError("Audiobook manifest `tracks` must be a non-empty array.")
    tracks: list[AudiobookTrack] = []
    script_paths: set[str] = set()
    audio_paths: set[str] = set()
    public_paths: set[str] = {full_public_path}
    for index, raw_track in enumerate(tracks_payload, start=1):
        if not isinstance(raw_track, dict):
            raise AudiobookManifestError(f"Audiobook manifest `tracks[{index - 1}]` must be an object.")
        number = raw_track.get("track_number")
        if number != index:
            raise AudiobookManifestError(
                f"Audiobook track numbers must be sequential and listed in order; expected {index}, found {number}."
            )
        script_manifest_path = relative_manifest_path(raw_track.get("script_path"), f"tracks[{index}].script_path")
        audio_manifest_path = relative_manifest_path(raw_track.get("audio_path"), f"tracks[{index}].audio_path")
        track_public_path = public_audio_path(
            raw_track.get("public_audio_path"),
            f"tracks[{index}].public_audio_path",
            tracks_only=True,
        )
        for seen, value, label in (
            (script_paths, script_manifest_path, "script_path"),
            (audio_paths, audio_manifest_path, "audio_path"),
            (public_paths, track_public_path, "public_audio_path"),
        ):
            if value in seen:
                raise AudiobookManifestError(f"Duplicate audiobook track `{label}`: {value}")
            seen.add(value)
        script_source_path = (resolved_manifest.parent / script_manifest_path).resolve()
        if not script_source_path.is_file():
            raise AudiobookManifestError(f"Audiobook script file not found for track {index:02d}: {script_source_path}")
        audio_source_path = (resolved_manifest.parent / audio_manifest_path).resolve()
        audio_probe = probe_audio_file(audio_source_path) if probe_audio and audio_source_path.is_file() else None
        word_count = raw_track.get("word_count")
        if not isinstance(word_count, int) or word_count < 0:
            raise AudiobookManifestError(f"Audiobook manifest `tracks[{index}].word_count` must be an integer >= 0.")
        tracks.append(
            AudiobookTrack(
                track_number=index,
                title=required_string(raw_track.get("title"), f"tracks[{index}].title"),
                script_source_path=script_source_path,
                script_manifest_path=script_manifest_path,
                audio_source_path=audio_source_path,
                audio_manifest_path=audio_manifest_path,
                public_audio_path=track_public_path,
                source_ids=string_list(raw_track.get("source_ids"), f"tracks[{index}].source_ids", allow_empty=False),
                target_entry_ids=string_list(raw_track.get("target_entry_ids"), f"tracks[{index}].target_entry_ids"),
                source_label=required_string(raw_track.get("source_label"), f"tracks[{index}].source_label"),
                word_count=word_count,
                status=required_string(raw_track.get("status"), f"tracks[{index}].status"),
                configured_duration_seconds=optional_duration(
                    raw_track.get("duration_seconds"),
                    f"tracks[{index}].duration_seconds",
                ),
                probe=audio_probe,
            )
        )
    if len(tracks) != expected_track_count:
        raise AudiobookManifestError(
            f"Audiobook manifest expected {expected_track_count} tracks but declares {len(tracks)}."
        )

    voice_payload = payload.get("preferred_voice") or {}
    if not isinstance(voice_payload, dict):
        raise AudiobookManifestError("Audiobook manifest `preferred_voice` must be an object.")
    preferred_voice = {str(key): str(value) for key, value in voice_payload.items()}
    skipped_payload = payload.get("skipped_entries") or []
    if not isinstance(skipped_payload, list) or any(not isinstance(row, dict) for row in skipped_payload):
        raise AudiobookManifestError("Audiobook manifest `skipped_entries` must be an array of objects.")
    return AudiobookCatalog(
        title=title,
        mode=mode,
        manifest_path=resolved_manifest,
        expected_track_count=expected_track_count,
        profile=profile,
        tracks=tuple(tracks),
        full_audiobook=full_audiobook,
        preferred_voice=preferred_voice,
        note=str(payload.get("note") or ""),
        skipped_entries=tuple(dict(row) for row in skipped_payload),
    )


def tracks_by_target_entry_id(catalog: AudiobookCatalog) -> dict[str, tuple[AudiobookTrack, ...]]:
    mapping: dict[str, list[AudiobookTrack]] = defaultdict(list)
    for track in catalog.tracks:
        for entry_id in track.target_entry_ids:
            mapping[entry_id].append(track)
    return {entry_id: tuple(tracks) for entry_id, tracks in mapping.items()}


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_audio_file(path: Path, *, ffmpeg_bin: str | None = None) -> str | None:
    executable = ffmpeg_bin or shutil.which("ffmpeg")
    if not executable:
        return "Missing required `ffmpeg` binary."
    result = subprocess.run(
        [
            executable,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    return result.stderr.strip() or f"ffmpeg exited with status {result.returncode}"


def validate_probe(profile: AudioProfile, probe: AudioProbe, label: str, validation: AudiobookValidation) -> None:
    validation.require(probe.codec == profile.codec, f"{label} codec is {probe.codec}, expected {profile.codec}.")
    validation.require(
        probe.sample_rate_hz == profile.sample_rate_hz,
        f"{label} sample rate is {probe.sample_rate_hz}, expected {profile.sample_rate_hz}.",
    )
    validation.require(probe.channels == profile.channels, f"{label} has {probe.channels} channels, expected {profile.channels}.")
    validation.require(probe.duration_seconds > 0, f"{label} has no positive duration.")
    validation.require(probe.size_bytes > 0, f"{label} is empty.")


def validate_audiobook_catalog(
    catalog: AudiobookCatalog,
    *,
    release: bool = False,
    decode: bool = False,
) -> AudiobookValidation:
    validation = AudiobookValidation()
    probes: dict[int, AudioProbe] = {}
    hashes: dict[str, AudiobookTrack] = {}
    for track in catalog.tracks:
        label = f"Track {track.track_number:02d}"
        validation.require(track.script_source_path.is_file(), f"{label} script is missing: {track.script_source_path}")
        validation.require(
            track.script_source_path.stem == track.audio_source_path.stem,
            f"{label} script/audio filename stems do not match.",
        )
        if not track.audio_source_path.is_file():
            if release:
                validation.errors.append(f"{label} audio file is missing: {track.audio_source_path}")
            continue
        try:
            probe = track.probe or probe_audio_file(track.audio_source_path)
        except AudiobookManifestError as exc:
            validation.errors.append(f"{label} cannot be probed: {exc}")
            continue
        probes[track.track_number] = probe
        validate_probe(catalog.profile, probe, label, validation)
        if track.configured_duration_seconds is not None:
            validation.require(
                abs(probe.duration_seconds - track.configured_duration_seconds) <= 0.25,
                f"{label} duration {probe.duration_seconds:.3f}s differs from manifest {track.configured_duration_seconds:.3f}s.",
            )
        if release:
            digest = hash_file(track.audio_source_path)
            duplicate = hashes.get(digest)
            validation.require(
                duplicate is None,
                f"{label} duplicates track {duplicate.track_number:02d} byte-for-byte." if duplicate else "",
            )
            hashes[digest] = track
        if decode:
            decode_error = decode_audio_file(track.audio_source_path)
            validation.require(decode_error is None, f"{label} decode failed: {decode_error}")

    full = catalog.full_audiobook
    if not full.audio_source_path.is_file():
        if release:
            validation.errors.append(f"Complete audiobook is missing: {full.audio_source_path}")
    else:
        try:
            full_probe = full.probe or probe_audio_file(full.audio_source_path)
        except AudiobookManifestError as exc:
            validation.errors.append(f"Complete audiobook cannot be probed: {exc}")
            full_probe = None
        if full_probe:
            validate_probe(catalog.profile, full_probe, "Complete audiobook", validation)
            expected_duration = sum(probe.duration_seconds for probe in probes.values())
            if len(probes) == len(catalog.tracks):
                expected_duration += full.silence_between_tracks_seconds * max(0, len(catalog.tracks) - 1)
                tolerance = max(2.0, len(catalog.tracks) * 0.1)
                validation.require(
                    abs(full_probe.duration_seconds - expected_duration) <= tolerance,
                    "Complete audiobook duration "
                    f"{full_probe.duration_seconds:.3f}s differs from expected {expected_duration:.3f}s "
                    f"by more than {tolerance:.1f}s.",
                )
            if full.configured_duration_seconds is not None:
                validation.require(
                    abs(full_probe.duration_seconds - full.configured_duration_seconds) <= 0.25,
                    "Complete audiobook duration differs from its manifest value.",
                )
            for key, expected in (
                ("title", full.title),
                ("album", full.album),
                ("artist", full.artist),
                ("narrator", full.narrator),
            ):
                validation.require(
                    full_probe.tags.get(key) == expected,
                    f"Complete audiobook `{key}` metadata is {full_probe.tags.get(key)!r}, expected {expected!r}.",
                )
        if decode:
            decode_error = decode_audio_file(full.audio_source_path)
            validation.require(decode_error is None, f"Complete audiobook decode failed: {decode_error}")

    available_duration = sum(probe.duration_seconds for probe in probes.values())
    available_size = sum(probe.size_bytes for probe in probes.values())
    validation.notes.append(
        f"Tracks: {len(probes)}/{len(catalog.tracks)} available; "
        f"duration {format_audio_duration(available_duration)}; size {format_file_size(available_size)}."
    )
    validation.notes.append(
        "Complete audiobook: "
        + (
            f"{format_audio_duration(full.duration_seconds)}; {format_file_size(full.probe.size_bytes) if full.probe else 'available'}."
            if full.is_available
            else "not built."
        )
    )
    return validation


def format_audio_duration(duration_seconds: float | None) -> str:
    if duration_seconds is None:
        return "unknown"
    total_seconds = max(0, int(round(duration_seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_file_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024 / 1024:.2f} GiB"
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f} MiB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KiB"
    return f"{size_bytes} bytes"


def catalog_inventory(catalog: AudiobookCatalog) -> dict[str, object]:
    probes = [track.probe for track in catalog.tracks if track.probe]
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest": str(catalog.manifest_path),
        "expected_track_count": catalog.expected_track_count,
        "available_track_count": len(probes),
        "total_track_duration_seconds": round(sum(probe.duration_seconds for probe in probes), 3),
        "total_track_size_bytes": sum(probe.size_bytes for probe in probes),
        "full_audiobook_available": catalog.full_audiobook.is_available,
        "full_audiobook_duration_seconds": (
            round(catalog.full_audiobook.duration_seconds, 3)
            if catalog.full_audiobook.duration_seconds is not None
            else None
        ),
    }


def cli_main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="Print the current audiobook inventory as JSON.")
    inspect_parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    validate_parser = subparsers.add_parser("validate", help="Validate the audiobook manifest and local media.")
    validate_parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    validate_parser.add_argument("--release", action="store_true", help="Require all track and complete-book MP3s.")
    validate_parser.add_argument("--decode", action="store_true", help="Decode every available MP3 with ffmpeg.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        catalog = load_audiobook_catalog(args.manifest)
    except AudiobookManifestError as exc:
        print(f"FAILED: {exc}")
        return 1
    if args.command == "inspect":
        print(json.dumps(catalog_inventory(catalog), indent=2, sort_keys=True))
        return 0
    result = validate_audiobook_catalog(catalog, release=args.release, decode=args.decode)
    for note in result.notes:
        print(f"NOTE: {note}")
    if result.errors:
        print(f"FAILED: {len(result.errors)} audiobook issue(s)")
        for error in result.errors:
            print(f"- {error}")
        return 1
    print("PASS: audiobook validation is clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
