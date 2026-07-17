#!/usr/bin/env python3
"""Derive semantic website reading sections from doc-web entries and audio tracks."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from html import unescape
from typing import Iterable, Protocol, Sequence


HEADING_RE = re.compile(r"<h[12]\b[^>]*>.*?</h[12]>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


class TrackLike(Protocol):
    track_number: int
    title: str
    target_entry_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReadingSource:
    entry_id: str
    title: str
    kind: str
    order: int
    source_pages: tuple[int, ...]
    printed_pages: tuple[int, ...]
    article_html: str


@dataclass(frozen=True)
class ReadingSection:
    section_id: str
    title: str
    path: str
    kind: str
    part_id: str
    order_key: tuple[int, int]
    source_entry_ids: tuple[str, ...]
    source_pages: tuple[int, ...]
    printed_pages: tuple[int, ...]
    article_html: str
    track_numbers: tuple[int, ...]


@dataclass(frozen=True)
class ReadingCatalog:
    sections: tuple[ReadingSection, ...]
    redirects: dict[str, str]
    track_paths: dict[int, str]
    unassigned_source_entry_ids: tuple[str, ...]
    unassigned_track_numbers: tuple[int, ...]

    def section_for_track(self, track_number: int) -> ReadingSection | None:
        path = self.track_paths.get(track_number)
        return next((section for section in self.sections if section.path == path), None)


@dataclass(frozen=True)
class HeadingFragment:
    title: str | None
    html: str
    index: int


WHOLE_TRACK_EXTRA_ENTRIES: dict[int, tuple[str, ...]] = {
    2: (),
    3: (),
    4: ("page-001",),
    5: (),
    6: (),
    35: ("chapter-002", "chapter-003"),
    49: (),
    50: (),
}

REFERENCE_GROUPS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "opening-pages-and-contents",
        "Opening Pages and Contents",
        "front",
        ("chapter-018", "page-003", "page-005"),
    ),
    ("acknowledgements", "Acknowledgements", "front", ("page-009",)),
    (
        "lessard-and-strasser-genealogy",
        "Lessard and Strasser Genealogy",
        "part-iv",
        ("chapter-012", "chapter-013"),
    ),
    ("personal-records", "Personal Records", "part-vii", ("chapter-016",)),
    ("bibliography", "Bibliography", "back", ("chapter-017",)),
)

REFERENCE_FRAGMENT_TITLES = {
    "chapter-001": "Alain and Folley Genealogy",
    "chapter-010": "Recipes",
    "chapter-011": "Lambert Township",
}

REFERENCE_FRAGMENT_PARTS = {
    "chapter-001": "part-ii",
    "chapter-010": "part-iv",
    "chapter-011": "part-iv",
}

STRUCTURAL_HEADINGS = {
    "additional",
    "part iv lessard family stories",
}

TRACK_HEADING_ALIASES = {
    46: ("Paulette Mary Lessard",),
}


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-") or "section"


def visible_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", fragment))).strip()


def normalized_title(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", visible_text(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def split_heading_fragments(article_html: str) -> list[HeadingFragment]:
    matches = list(HEADING_RE.finditer(article_html))
    if not matches:
        return [HeadingFragment(None, article_html.strip(), 0)] if article_html.strip() else []
    fragments: list[HeadingFragment] = []
    leading = article_html[: matches[0].start()].strip()
    if leading:
        fragments.append(HeadingFragment(None, leading, 0))
    for offset, match in enumerate(matches, start=1):
        end = matches[offset].start() if offset < len(matches) else len(article_html)
        fragments.append(
            HeadingFragment(
                visible_text(match.group(0)),
                article_html[match.start() : end].strip(),
                offset,
            )
        )
    return fragments


def track_part(track_number: int) -> str:
    if track_number <= 3:
        return "front"
    if track_number == 4:
        return "part-i"
    if 5 <= track_number <= 34:
        return "part-ii"
    if track_number == 35:
        return "part-iii"
    if 36 <= track_number <= 48:
        return "part-iv"
    if track_number == 49:
        return "part-v"
    if track_number == 50:
        return "part-vi"
    return "front"


def ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    return tuple(value for value in values if not (value in seen or seen.add(value)))


def union_numbers(sources: Iterable[ReadingSource], field_name: str) -> tuple[int, ...]:
    values = {
        number
        for source in sources
        for number in getattr(source, field_name)
    }
    return tuple(sorted(values))


def make_section(
    *,
    section_id: str,
    title: str,
    kind: str,
    part_id: str,
    order_key: tuple[int, int],
    sources: Sequence[ReadingSource],
    article_html: str,
    track_numbers: tuple[int, ...] = (),
) -> ReadingSection:
    return ReadingSection(
        section_id=section_id,
        title=title,
        path=f"{section_id}.html",
        kind=kind,
        part_id=part_id,
        order_key=order_key,
        source_entry_ids=ordered_unique(source.entry_id for source in sources),
        source_pages=union_numbers(sources, "source_pages"),
        printed_pages=union_numbers(sources, "printed_pages"),
        article_html=article_html.strip(),
        track_numbers=track_numbers,
    )


def track_title_variants(track: TrackLike) -> set[str]:
    return {
        normalized_title(title)
        for title in (track.title, *TRACK_HEADING_ALIASES.get(track.track_number, ()))
    }


def main_target_ids(track: TrackLike) -> tuple[str, ...]:
    return tuple(
        target
        for target in track.target_entry_ids
        if not target.startswith("companion:") and not target.startswith("manual:")
    )


def build_reading_catalog(
    sources: Sequence[ReadingSource],
    tracks: Sequence[TrackLike],
) -> ReadingCatalog:
    source_by_id = {source.entry_id: source for source in sources}
    main_tracks = [track for track in tracks if main_target_ids(track)]
    track_by_number = {track.track_number: track for track in main_tracks}
    sections: list[ReadingSection] = []
    consumed_entries: set[str] = set()
    source_paths: dict[str, list[str]] = defaultdict(list)
    track_paths: dict[int, str] = {}

    def add_section(section: ReadingSection) -> None:
        sections.append(section)
        for entry_id in section.source_entry_ids:
            source_paths[entry_id].append(section.path)
        for track_number in section.track_numbers:
            if track_number in track_paths:
                raise ValueError(f"Track {track_number:02d} maps to more than one reading section.")
            track_paths[track_number] = section.path

    for track_number, extra_entry_ids in WHOLE_TRACK_EXTRA_ENTRIES.items():
        track = track_by_number.get(track_number)
        if not track:
            continue
        wanted_ids = ordered_unique((*extra_entry_ids, *main_target_ids(track)))
        selected = sorted(
            (source_by_id[entry_id] for entry_id in wanted_ids if entry_id in source_by_id),
            key=lambda source: source.order,
        )
        if not selected:
            continue
        section_id = f"read-{track.track_number:02d}-{slugify(track.title)}"
        add_section(
            make_section(
                section_id=section_id,
                title=track.title,
                kind="narrative",
                part_id=track_part(track.track_number),
                order_key=(min(source.order for source in selected), 0),
                sources=selected,
                article_html="\n".join(source.article_html for source in selected),
                track_numbers=(track.track_number,),
            )
        )
        consumed_entries.update(source.entry_id for source in selected)

    for slug, title, part_id, entry_ids in REFERENCE_GROUPS:
        selected = sorted(
            (
                source_by_id[entry_id]
                for entry_id in entry_ids
                if entry_id in source_by_id and entry_id not in consumed_entries
            ),
            key=lambda source: source.order,
        )
        if not selected:
            continue
        add_section(
            make_section(
                section_id=f"read-reference-{slug}",
                title=title,
                kind="reference",
                part_id=part_id,
                order_key=(min(source.order for source in selected), 0),
                sources=selected,
                article_html="\n".join(source.article_html for source in selected),
            )
        )
        consumed_entries.update(source.entry_id for source in selected)

    shared_tracks = [
        track
        for track in main_tracks
        if track.track_number not in WHOLE_TRACK_EXTRA_ENTRIES
    ]
    tracks_by_entry: dict[str, list[TrackLike]] = defaultdict(list)
    for track in shared_tracks:
        for entry_id in main_target_ids(track):
            if entry_id in source_by_id:
                tracks_by_entry[entry_id].append(track)

    track_fragments: dict[int, list[tuple[ReadingSource, HeadingFragment]]] = defaultdict(list)
    reference_fragments: dict[str, list[HeadingFragment]] = defaultdict(list)
    for entry_id in sorted(tracks_by_entry, key=lambda value: source_by_id[value].order):
        source = source_by_id[entry_id]
        entry_tracks = sorted(tracks_by_entry[entry_id], key=lambda track: track.track_number)
        variants = {
            variant: track
            for track in entry_tracks
            for variant in track_title_variants(track)
        }
        continuation_track = next(
            (
                track
                for track in entry_tracks
                if main_target_ids(track).index(entry_id) > 0
            ),
            None,
        )
        pending_structural: list[HeadingFragment] = []
        fragments = split_heading_fragments(source.article_html)
        for fragment in fragments:
            if fragment.title is None:
                target_track = continuation_track or entry_tracks[0]
                track_fragments[target_track.track_number].append((source, fragment))
                continue
            normalized = normalized_title(fragment.title)
            target_track = variants.get(normalized)
            if target_track:
                for pending in pending_structural:
                    track_fragments[target_track.track_number].append((source, pending))
                pending_structural = []
                track_fragments[target_track.track_number].append((source, fragment))
            elif normalized in STRUCTURAL_HEADINGS:
                pending_structural.append(fragment)
            else:
                reference_fragments[entry_id].extend(pending_structural)
                pending_structural = []
                reference_fragments[entry_id].append(fragment)
        reference_fragments[entry_id].extend(pending_structural)
        consumed_entries.add(entry_id)

    for track in shared_tracks:
        fragments = track_fragments.get(track.track_number, [])
        if not fragments:
            continue
        selected_sources = [source for source, _fragment in fragments]
        first_source, first_fragment = min(
            fragments,
            key=lambda row: (row[0].order, row[1].index),
        )
        section_id = f"read-{track.track_number:02d}-{slugify(track.title)}"
        add_section(
            make_section(
                section_id=section_id,
                title=track.title,
                kind="narrative",
                part_id=track_part(track.track_number),
                order_key=(first_source.order, first_fragment.index),
                sources=selected_sources,
                article_html="\n".join(fragment.html for _source, fragment in fragments),
                track_numbers=(track.track_number,),
            )
        )

    for entry_id, fragments in reference_fragments.items():
        if not fragments:
            continue
        source = source_by_id[entry_id]
        title = REFERENCE_FRAGMENT_TITLES.get(entry_id) or fragments[0].title or f"{source.title} Reference Material"
        add_section(
            make_section(
                section_id=f"read-reference-{slugify(title)}",
                title=title,
                kind="reference",
                part_id=REFERENCE_FRAGMENT_PARTS.get(entry_id, "back"),
                order_key=(source.order, min(fragment.index for fragment in fragments)),
                sources=[source],
                article_html="\n".join(fragment.html for fragment in fragments),
            )
        )

    for source in sources:
        if source.entry_id in consumed_entries:
            continue
        fragments = split_heading_fragments(source.article_html)
        heading_title = next((fragment.title for fragment in fragments if fragment.title), None)
        title = heading_title or source.title
        if re.fullmatch(r"(?:Page|Image)\s+\w+", title, flags=re.IGNORECASE):
            title = "Illustrated Reference Material"
        add_section(
            make_section(
                section_id=f"read-reference-{slugify(title)}-{slugify(source.entry_id)}",
                title=title,
                kind="reference",
                part_id="back",
                order_key=(source.order, 0),
                sources=[source],
                article_html=source.article_html,
            )
        )
        consumed_entries.add(source.entry_id)

    ordered_sections = tuple(sorted(sections, key=lambda section: section.order_key))
    order_by_path = {section.path: index for index, section in enumerate(ordered_sections)}
    redirects = {
        entry_id: min(paths, key=lambda path: order_by_path[path])
        for entry_id, paths in source_paths.items()
        if paths
    }
    unassigned_sources = tuple(sorted(set(source_by_id) - set(redirects)))
    unassigned_tracks = tuple(sorted(set(track_by_number) - set(track_paths)))
    return ReadingCatalog(
        sections=ordered_sections,
        redirects=redirects,
        track_paths=track_paths,
        unassigned_source_entry_ids=unassigned_sources,
        unassigned_track_numbers=unassigned_tracks,
    )
