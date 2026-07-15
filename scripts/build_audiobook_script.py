#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_family_site import (  # noqa: E402
    Entry,
    companion_doc_web_article_html,
    entry_meta_label,
    load_bundle,
    load_supplemental_documents,
    ordered_entries,
    read_article_html,
)


DEFAULT_OUTPUT_DIR = ROOT / "audiobook" / "script"
MANIFEST_PATH = ROOT / "audiobook" / "manifest.json"
README_PATH = ROOT / "audiobook" / "README.md"
VOICE = {
    "provider": "ElevenLabs",
    "name": "Matilda",
    "voice_id": "XrExE9yKIg1WjnnlVkGX",
}

BLOCK_TAG_PATTERN = re.compile(r"^<([a-z0-9]+)\b", re.IGNORECASE)
BLOCK_PATTERN = re.compile(r"<(?P<tag>h[1-6]|p|li)\b[^>]*>.*?</(?P=tag)>", re.IGNORECASE | re.DOTALL)
BLOCK_ID_PATTERN = re.compile(r'\bid="([^"]+)"', re.IGNORECASE)
HEADING_PATTERN = re.compile(r"<h([1-2])\b[^>]*>.*?</h\1>", re.IGNORECASE | re.DOTALL)
SKIP_BLOCK_PATTERN = re.compile(
    r"<(?P<tag>figure|table|nav|script|style)\b.*?</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")
LINEBREAK_TAG_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
EMPHASIS_TAG_PATTERN = re.compile(r"</?(?:em|i)\b[^>]*>", re.IGNORECASE)
STRONG_TAG_PATTERN = re.compile(r"</?(?:strong|b)\b[^>]*>", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"[^\S\n]+")
GENEALOGY_TITLE_PATTERN = re.compile(r"\b(?:GENEALOGY|FAMILY /|PERSONAL RECORDS|BIBLIOGRAPHY|RECIPES)\b", re.IGNORECASE)
REFERENCE_ONLY_TITLES = {
    "additional",
    "part iv - lessard family stories",
    "part vi - memories",
    "obituaries",
    "lambert township",
}

# The accepted HTML faithfully carries a number of print line-break hyphens.
# These are source-verified word breaks, not authored compound words, and they
# need to be joined before the text is handed to a narrator.
OCR_WORD_REPLACEMENTS = {
    "accom-panied": "accompanied",
    "Amster-dam": "Amsterdam",
    "any-way": "anyway",
    "Ari-zona": "Arizona",
    "back-grounds": "backgrounds",
    "Ber-niers": "Berniers",
    "Bran-don": "Brandon",
    "break-fast": "breakfast",
    "bus-tling": "bustling",
    "busi-ness": "business",
    "Cana-dian": "Canadian",
    "carna-tions": "carnations",
    "cham-pagne": "champagne",
    "chang-ing": "changing",
    "Chau-monot": "Chaumonot",
    "Clar-ence": "Clarence",
    "co-ordina-tion": "coordination",
    "Commu-nity": "Community",
    "con-clude": "conclude",
    "con-tinued": "continued",
    "congrega-tion": "congregation",
    "construc-tion": "construction",
    "crit-icizing": "criticizing",
    "daugh-ter": "daughter",
    "Edmon-ton": "Edmonton",
    "experi-enced": "experienced",
    "fam-ily": "family",
    "feel-ing": "feeling",
    "fif-teenth": "fifteenth",
    "fol-lowing": "following",
    "For-tunately": "Fortunately",
    "for-ward": "forward",
    "garden-ing": "gardening",
    "Govern-ment": "Government",
    "grad-uated": "graduated",
    "grand-children": "grandchildren",
    "high-way": "highway",
    "How-ever": "However",
    "Hud-son": "Hudson",
    "imag-ine": "imagine",
    "impres-sions": "impressions",
    "informa-tion": "information",
    "inheri-tance": "inheritance",
    "insep-arable": "inseparable",
    "inter-ests": "interests",
    "interna-tional": "international",
    "involve-ment": "involvement",
    "Janu-ary": "January",
    "Jean-nine": "Jeannine",
    "jour-nalists": "journalists",
    "Lor-raine": "Lorraine",
    "lumber-jacks": "lumberjacks",
    "Man-itoba": "Manitoba",
    "mar-riages": "marriages",
    "mar-ried": "married",
    "match-ing": "matching",
    "Mor-rison": "Morrison",
    "morn-ing": "morning",
    "Natu-rally": "Naturally",
    "new-lyweds": "newlyweds",
    "oppor-tunity": "opportunity",
    "out-side": "outside",
    "per-formed": "performed",
    "pleas-ant": "pleasant",
    "pop-corn": "popcorn",
    "promi-nent": "prominent",
    "respon-sible": "responsible",
    "roll-erskating": "roller-skating",
    "run-ning": "running",
    "Shan-non": "Shannon",
    "situ-ated": "situated",
    "Smelt-ing": "Smelting",
    "spe-cial": "special",
    "sub-divided": "subdivided",
    "suc-cessive": "successive",
    "taf-feta": "taffeta",
    "tend-ing": "tending",
    "trans-fer": "transfer",
    "trans-ferred": "transferred",
    "Van-couver": "Vancouver",
    "vege-tables": "vegetables",
    "Veillard-ville": "Veillardville",
    "vis-ited": "visited",
    "volun-teers": "volunteers",
    "warn-ings": "warnings",
    "Wash-ington": "Washington",
    "wed-ding": "wedding",
    "Win-nipeg": "Winnipeg",
    "base- ball": "baseball",
    "com- pany": "company",
    "cous- ins": "cousins",
    "differ- ent": "different",
    "dis- trict": "district",
    "eve- ning": "evening",
    "expect- ing": "expecting",
    "fol- lowed": "followed",
    "har- vest": "harvest",
    "high- low": "high-low",
    "Know- ing": "Knowing",
    "look- ing": "looking",
    "mid- night": "midnight",
    "move- ment": "movement",
    "neigh- bour": "neighbour",
    "occa- sion": "occasion",
    "store- keeper": "storekeeper",
    "two- room": "two-room",
    "commu-nity": "community",
    "crib-bage": "cribbage",
    "gradu\nated": "graduated",
    "hav-ing": "having",
    "meet-ing": "meeting",
    "chil dren": "children",
    "fol lowing": "following",
    "jump ing": "jumping",
    "stook ing": "stooking",
    "throw ing": "throwing",
    "five hundred and thirty-three. 1.": "five hundred and thirty-three.",
}

AUDIO_EXCLUDED_BLOCK_IDS = {
    "blk-chapter-005-0052",  # Footnote interrupting the Joseph Déridé narrative.
}

CONTINUATION_BLOCKS = {
    ("chapter-005", "joseph déridé lessard"): (
        "chapter-006",
        ("blk-chapter-006-0002",),
    ),
    ("chapter-007", "martin alphonse lessard"): (
        "chapter-008",
        (
            "blk-chapter-008-0001",
            "blk-chapter-008-0002",
            "blk-chapter-008-0003",
            "blk-chapter-008-0004",
        ),
    ),
    ("chapter-008", "joseph roland donald lessard"): (
        "chapter-009",
        ("blk-chapter-009-0001", "blk-chapter-009-0002"),
    ),
}


@dataclass(frozen=True)
class HtmlTrack:
    title: str
    html: str
    source_ids: tuple[str, ...]
    source_label: str


@dataclass(frozen=True)
class ScriptTrack:
    title: str
    filename: str
    source_ids: tuple[str, ...]
    source_label: str
    word_count: int


@dataclass(frozen=True)
class HtmlSection:
    title: str
    html: str
    heading_level: int


def slug_title(index: int, title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return f"{index:02d}-{slug or 'chapter'}.md"


def plain_title(title: str) -> str:
    return re.sub(r"[*_`]", "", title).strip()


def normalize_title_key(title: str) -> str:
    title = plain_title(title)
    return re.sub(r"\s+", " ", title.replace("\u2013", "-").replace("\u2014", "-")).strip().lower()


def display_title(title: str) -> str:
    title = re.sub(r"\s+", " ", plain_title(title)).strip()
    if not title:
        return title
    if any(char.islower() for char in title):
        return title
    words = title.title().split()
    small_words = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to"}
    fixed = []
    for index, word in enumerate(words):
        if index > 0 and word.lower() in small_words:
            fixed.append(word.lower())
        else:
            fixed.append(word)
    return " ".join(fixed)


def strip_audio_skips(html: str) -> str:
    return SKIP_BLOCK_PATTERN.sub("", html)


def block_tag(block_html: str) -> str | None:
    match = BLOCK_TAG_PATTERN.match(block_html.lstrip())
    if not match:
        return None
    return match.group(1).lower()


def inner_html(block_html: str) -> str:
    stripped = block_html.strip()
    opening_end = stripped.find(">")
    closing_start = stripped.rfind("</")
    if opening_end == -1 or closing_start == -1 or closing_start <= opening_end:
        return stripped
    return stripped[opening_end + 1 : closing_start]


def block_id(block_html: str) -> str | None:
    match = BLOCK_ID_PATTERN.search(block_html)
    return match.group(1) if match else None


def blocks_by_id(html: str, wanted_ids: set[str] | tuple[str, ...]) -> str:
    wanted = set(wanted_ids)
    found: set[str] = set()
    selected: list[str] = []
    for match in BLOCK_PATTERN.finditer(html):
        candidate = match.group(0)
        candidate_id = block_id(candidate)
        if candidate_id in wanted:
            selected.append(candidate)
            found.add(candidate_id)
    missing = wanted - found
    if missing:
        raise SystemExit(f"Missing expected audiobook source blocks: {', '.join(sorted(missing))}")
    return "\n".join(selected)


def without_blocks(html: str, excluded_ids: set[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        return "" if block_id(match.group(0)) in excluded_ids else match.group(0)

    return BLOCK_PATTERN.sub(replace, html)


def truncate_before_block(html: str, stop_id: str) -> str:
    selected: list[str] = []
    for match in BLOCK_PATTERN.finditer(html):
        candidate = match.group(0)
        if block_id(candidate) == stop_id:
            return "\n".join(selected)
        selected.append(candidate)
    raise SystemExit(f"Missing expected audiobook cutoff block: {stop_id}")


def normalize_markdown_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    for source, replacement in OCR_WORD_REPLACEMENTS.items():
        text = text.replace(source, replacement)
    normalized_lines: list[str] = []
    for line in text.splitlines():
        collapsed = WHITESPACE_PATTERN.sub(" ", line).strip()
        collapsed = re.sub(r"\s+([,.;:!?])", r"\1", collapsed)
        normalized_lines.append(collapsed)
    normalized_lines = [line for line in normalized_lines if line]
    return "\n".join(normalized_lines)


def markdown_inline(fragment_html: str) -> str:
    text = LINEBREAK_TAG_PATTERN.sub("\n", fragment_html)
    text = STRONG_TAG_PATTERN.sub("**", text)
    text = EMPHASIS_TAG_PATTERN.sub("*", text)
    text = TAG_PATTERN.sub("", text)
    return normalize_markdown_text(unescape(text))


def markdown_from_block(block_html: str) -> str | None:
    tag = block_tag(block_html)
    if tag is None:
        return None
    content = markdown_inline(inner_html(block_html))
    if not content:
        return None
    if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
        level = int(tag[1])
        return f"{'#' * min(level, 6)} {display_title(content)}"
    if tag == "p":
        return content
    if tag == "li":
        content = re.sub(r"^[\s\-–—]+", "", content)
        if content:
            content = content[0].upper() + content[1:]
        return content
    return None


def merge_fragmented_markdown_blocks(blocks: list[str]) -> list[str]:
    merged: list[str] = []
    for block in blocks:
        if not merged or block.startswith("#") or merged[-1].startswith("#"):
            merged.append(block)
            continue

        previous = merged[-1].rstrip()
        spoken = re.sub(r"^[*_>`\s]+", "", block)
        first_letter = re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", spoken)
        starts_lowercase = bool(first_letter and first_letter.group(0).islower())
        ends_with_linker = bool(
            re.search(r"(?:,|;|\b(?:and|or|the|of|to|in|with|for|from|at|by))$", previous, re.IGNORECASE)
        )
        if previous.endswith("-"):
            merged[-1] = previous[:-1] + block.lstrip()
        elif (starts_lowercase and not re.search(r"[.!?][\"')\]]?$", previous)) or ends_with_linker:
            merged[-1] = previous + " " + block.lstrip()
        else:
            merged.append(block)
    return merged


def word_count(markdown: str) -> int:
    text = re.sub(r"^#+\s+", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"[*_>`#-]", " ", text)
    return len(re.findall(r"\b[\w']+\b", text))


def render_markdown(title: str, html: str) -> str:
    clean_html = strip_audio_skips(html)
    markdown_blocks = [
        markdown
        for match in BLOCK_PATTERN.finditer(clean_html)
        if (markdown := markdown_from_block(match.group(0)))
    ]
    if not markdown_blocks:
        raise SystemExit(f"No audiobook Markdown content was produced for: {title}")

    first_heading_index = next((index for index, block in enumerate(markdown_blocks) if block.startswith("#")), None)
    if first_heading_index is None:
        markdown_blocks.insert(0, f"# {title}")
    else:
        pre_heading_blocks = markdown_blocks[:first_heading_index]
        heading_and_rest = markdown_blocks[first_heading_index:]
        heading_and_rest[0] = f"# {title}"
        markdown_blocks = [heading_and_rest[0], *pre_heading_blocks, *heading_and_rest[1:]]

    for index, block in enumerate(markdown_blocks[1:], start=1):
        if block.startswith("# "):
            markdown_blocks[index] = "## " + block[2:]

    markdown_blocks = merge_fragmented_markdown_blocks(markdown_blocks)
    return "\n\n".join(markdown_blocks).rstrip() + "\n"


def split_heading_sections(html: str) -> list[HtmlSection]:
    matches = list(HEADING_PATTERN.finditer(html))
    sections: list[HtmlSection] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(html)
        heading_html = match.group(0)
        title = markdown_inline(inner_html(heading_html))
        sections.append(HtmlSection(title=title, html=html[match.start() : end], heading_level=int(match.group(1))))
    return sections


def remove_heading_blocks(html: str, titles: set[str]) -> str:
    normalized_titles = {normalize_title_key(title) for title in titles}

    def replace(match: re.Match[str]) -> str:
        title = markdown_inline(inner_html(match.group(0)))
        if normalize_title_key(title) in normalized_titles:
            return ""
        return match.group(0)

    return HEADING_PATTERN.sub(replace, html)


def section_is_audio_candidate(section: HtmlSection) -> bool:
    title_key = normalize_title_key(section.title)
    if title_key in REFERENCE_ONLY_TITLES:
        return False
    if GENEALOGY_TITLE_PATTERN.search(section.title):
        return False
    if word_count(render_markdown(display_title(section.title), section.html)) < 50:
        return False
    return True


def combine_source_labels(entries: list[Entry]) -> str:
    labels = [entry_meta_label(entry) for entry in entries if entry_meta_label(entry)]
    if not labels:
        return ""
    return "; ".join(labels)


def entry_track(title: str, bundle, entries_by_id: dict[str, Entry], entry_ids: list[str], *, remove_headings: set[str] | None = None) -> HtmlTrack:
    entries = [entries_by_id[entry_id] for entry_id in entry_ids]
    html = "\n".join(read_article_html(bundle, entry) for entry in entries)
    if remove_headings:
        html = remove_heading_blocks(html, remove_headings)
    return HtmlTrack(
        title=title,
        html=html,
        source_ids=tuple(entry_ids),
        source_label=combine_source_labels(entries),
    )


def edouard_audio_html(section_html: str) -> str:
    narrative_ids = {
        *(f"blk-chapter-005-{index:04d}" for index in range(1, 11)),
        *(f"blk-chapter-005-{index:04d}" for index in range(23, 31)),
        "blk-chapter-005-0034",
    }
    html = blocks_by_id(section_html, narrative_ids)
    html = re.sub(
        r'(<(?:p|li)\b[^>]*>)(?:7|8|9|10|11)\.\s*',
        r"\1",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'(<p\b[^>]*id="blk-chapter-005-0030"[^>]*>).*?</p>',
        r"\1So my girlfriend became my aunt.</p>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html


def therese_audio_track(bundle, entries_by_id: dict[str, Entry]) -> HtmlTrack:
    chapter_009 = entries_by_id["chapter-009"]
    chapter_010 = entries_by_id["chapter-010"]
    opening = (
        '<h2 id="audio-source-scan-121-therese">THERESE (LESSARD) MacFARLANE</h2>\n'
        "<p>My full name is Marie Jeanne Therese. I was named after St. Therese. "
        "I was born in Delmas, Saskatchewan, on November 16, 1924.</p>\n"
        "<p>Our family moved to Hudson Bay when I was three and a half. I took grades one to eight in "
        "Veillardville where I attended the White Poplar School District #4269.</p>\n"
        "<p>Then our whole family moved to Tillsonburg, Ontario, in 1938, the year before war broke out. "
        "After taking my high school in Tillsonburg, I took a business course there.</p>\n"
        "<p>In 1939 the family moved again, this time to Hamilton, Ontario, where several of us were employed "
        "in war work. I started to work for Westinghouse for 25 cents an hour making little radios for aircraft. "
        "Then I heard that National Steel Car and Shell Shop was paying 33 and one-third cents an hour so I went "
        "there where I inspected shells for the Government.</p>\n"
        "<p>Then I heard that Otis Fenson was paying 50 cents an hour so I decided to work there. However, this "
        "job meant working eleven-hour days, six days a week and, as I was only seventeen, I became very tired "
        "physically. About this time, I decided to join up as soon as I was eighteen, which I did.</p>"
    )
    chapter_009_html = read_article_html(bundle, chapter_009)
    chapter_010_html = read_article_html(bundle, chapter_010)
    body = blocks_by_id(
        chapter_009_html,
        tuple(
            f"blk-chapter-009-{index:04d}"
            for index in (*range(43, 44), *range(45, 60), *range(61, 64))
        ),
    )
    closing = blocks_by_id(
        chapter_010_html,
        ("blk-chapter-010-0001", "blk-chapter-010-0002"),
    )
    return HtmlTrack(
        title="Therese (Lessard) MacFarlane",
        html="\n".join((opening, body, closing)),
        source_ids=("chapter-009", "chapter-010"),
        source_label=combine_source_labels([chapter_009, chapter_010]),
    )


def preamble() -> str:
    return (
        "# Preamble\n\n"
        "*Alain-Lessard* was prepared in 1987 as a family history of the Alain and Lessard lines, "
        "bringing together early family history, biography, community memory, poems, reunion notes, "
        "and records preserved by descendants.\n\n"
        "For this audiobook script, the listening edition focuses on narrative family history, stories, "
        "introductions, poems, memories, and the companion pieces found with the book. Genealogy tables, "
        "personal-record forms, source lists, recipes, and other reference-first material have been left "
        "in the readable archive so the spoken version can move clearly from story to story.\n\n"
        "What follows begins with the book's own introductory material, then moves through the Alain and "
        "Lessard family histories, family stories, Veillardville memories, reunion notes, obituaries, "
        "and the two companion documents found tucked inside the book.\n"
    )


def build_html_tracks() -> tuple[list[HtmlTrack], list[dict[str, object]]]:
    bundle = load_bundle()
    entries_by_id = {entry.entry_id: entry for entry in ordered_entries(bundle)}
    skipped: list[dict[str, object]] = [
        {"title": "Cover, title pages, copyright, and table of contents", "reason": "opening reference material"},
        {"title": "Acknowledgements", "reason": "source acknowledgements"},
        {"title": "Personal records", "reason": "personal records tables"},
        {"title": "Bibliography", "reason": "bibliography"},
    ]

    part_i = entry_track(
        "Part I - Alain Family History",
        bundle,
        entries_by_id,
        ["page-002", "page-004", "page-006", "page-008", "page-010"],
    )
    part_i = HtmlTrack(
        title=part_i.title,
        html=without_blocks(
            part_i.html,
            {
                "blk-page-008-0005",
                "blk-page-008-0006",
                "blk-page-008-0007",
                "blk-page-008-0008",
            },
        ),
        source_ids=part_i.source_ids,
        source_label=part_i.source_label,
    )

    tracks: list[HtmlTrack] = [
        entry_track("Dedication and Introduction", bundle, entries_by_id, ["page-007"]),
        entry_track("Preface", bundle, entries_by_id, ["page-011"]),
        part_i,
        entry_track(
            "Henri Delphice Alain",
            bundle,
            entries_by_id,
            ["page-012", "page-013", "page-014", "page-015", "page-016", "page-017", "page-018"],
            remove_headings={"Part II - Alain Family Stories", "Part II – Alain Family Stories"},
        ),
        entry_track("Moise (Smokey) Alain", bundle, entries_by_id, ["page-019", "page-020", "page-021"]),
    ]

    for entry_id in ("chapter-001",):
        entry = entries_by_id[entry_id]
        for section in split_heading_sections(read_article_html(bundle, entry)):
            title_key = normalize_title_key(section.title)
            if title_key == "berthe (alain) marsollier":
                section = HtmlSection(
                    title=section.title,
                    html=truncate_before_block(section.html, "blk-chapter-001-0536"),
                    heading_level=section.heading_level,
                )
            elif title_key == "paul emile alain":
                section = HtmlSection(
                    title=section.title,
                    html=truncate_before_block(section.html, "blk-chapter-001-0572"),
                    heading_level=section.heading_level,
                )
            if not section_is_audio_candidate(section):
                skipped.append({"title": section.title, "reason": "genealogy/reference section", "source_id": entry_id})
                continue
            tracks.append(
                HtmlTrack(
                    title=display_title(section.title),
                    html=section.html,
                    source_ids=(entry_id,),
                    source_label=entry_meta_label(entry),
                )
            )

    part_iii = entry_track("Part III - Lessard Family History", bundle, entries_by_id, ["chapter-004"])
    tracks.append(
        HtmlTrack(
            title=part_iii.title,
            html=without_blocks(
                part_iii.html,
                {"blk-chapter-004-0042", "blk-chapter-004-0045"},
            ),
            source_ids=part_iii.source_ids,
            source_label=part_iii.source_label,
        )
    )

    for entry_id in ("chapter-005", "chapter-006", "chapter-007", "chapter-008", "chapter-009", "chapter-010", "chapter-011"):
        entry = entries_by_id[entry_id]
        for section in split_heading_sections(read_article_html(bundle, entry)):
            section = HtmlSection(
                title=section.title,
                html=without_blocks(section.html, AUDIO_EXCLUDED_BLOCK_IDS),
                heading_level=section.heading_level,
            )
            title_key = normalize_title_key(section.title)
            if entry_id == "chapter-005" and title_key == "edouard lessard":
                section = HtmlSection(
                    title=section.title,
                    html=edouard_audio_html(section.html),
                    heading_level=section.heading_level,
                )
            elif entry_id == "chapter-009" and title_key == "paulette mary lessard":
                skipped.append(
                    {
                        "title": display_title(section.title),
                        "reason": "short reference profile",
                        "source_id": entry_id,
                    }
                )
                tracks.append(therese_audio_track(bundle, entries_by_id))
                continue
            elif entry_id == "chapter-011" and title_key == "simeon bernier":
                section = HtmlSection(
                    title=section.title,
                    html=truncate_before_block(section.html, "blk-chapter-011-0012"),
                    heading_level=section.heading_level,
                )

            continuation = CONTINUATION_BLOCKS.get((entry_id, title_key))
            source_ids = (entry_id,)
            source_label = entry_meta_label(entry)
            if continuation:
                continuation_entry_id, continuation_ids = continuation
                continuation_entry = entries_by_id[continuation_entry_id]
                section = HtmlSection(
                    title=section.title,
                    html="\n".join(
                        (
                            section.html,
                            blocks_by_id(read_article_html(bundle, continuation_entry), continuation_ids),
                        )
                    ),
                    heading_level=section.heading_level,
                )
                source_ids = (entry_id, continuation_entry_id)
                source_label = combine_source_labels([entry, continuation_entry])

            if not section_is_audio_candidate(section):
                skipped.append({"title": section.title, "reason": "genealogy/reference section", "source_id": entry_id})
                continue
            tracks.append(
                HtmlTrack(
                    title=display_title(section.title),
                    html=section.html,
                    source_ids=source_ids,
                    source_label=source_label,
                )
            )

    tracks.extend(
        [
            entry_track("Part V - Veillardville", bundle, entries_by_id, ["chapter-014"]),
            entry_track("Part VI - Memories", bundle, entries_by_id, ["chapter-015"]),
        ]
    )

    for document in load_supplemental_documents():
        tracks.append(
            HtmlTrack(
                title=document.title,
                html=companion_doc_web_article_html(document),
                source_ids=(f"companion:{document.slug}",),
                source_label=f"{document.page_count} source pages",
            )
        )

    skipped.extend(
        [
            {"title": "The Alain name and coat of arms", "reason": "heraldic/reference material", "source_id": "page-001"},
            {"title": "Salted Lard Cake", "reason": "recipe material", "source_id": "page-008"},
            {"title": "The Lessard name and coat of arms", "reason": "heraldic/reference material", "source_id": "chapter-002"},
            {"title": "Lessard source citation", "reason": "bibliographic reference", "source_id": "chapter-004"},
            {"title": "Berthe and Paul Marsollier family register", "reason": "genealogy/reference section", "source_id": "chapter-001"},
            {"title": "Paul Emile and Reine Alain family register", "reason": "genealogy/reference section", "source_id": "chapter-001"},
            {"title": "Edouard Lessard descendant register", "reason": "genealogy/reference section", "source_id": "chapter-005"},
            {"title": "Simeon Bernier descendant register", "reason": "genealogy/reference section", "source_id": "chapter-011"},
            {"title": "Lessard Genealogy", "reason": "genealogy/reference section", "source_id": "chapter-012"},
            {"title": "Strasser Family", "reason": "genealogy/reference section", "source_id": "chapter-013"},
            {"title": "Recipes", "reason": "recipe/table material", "source_id": "chapter-010"},
        ]
    )
    return tracks, skipped


def write_track(output_dir: Path, index: int, title: str, markdown: str, html_track: HtmlTrack | None = None) -> ScriptTrack:
    filename = slug_title(index, title)
    (output_dir / filename).write_text(markdown, encoding="utf-8")
    return ScriptTrack(
        title=title,
        filename=filename,
        source_ids=html_track.source_ids if html_track else ("manual:preamble",),
        source_label=html_track.source_label if html_track else "Manual listening preamble",
        word_count=word_count(markdown),
    )


def build(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.md"):
        old.unlink()

    manifest_tracks: list[ScriptTrack] = []
    manifest_tracks.append(write_track(output_dir, 1, "Preamble", preamble()))

    html_tracks, skipped_entries = build_html_tracks()
    for index, html_track in enumerate(html_tracks, start=2):
        markdown = render_markdown(html_track.title, html_track.html)
        manifest_tracks.append(write_track(output_dir, index, html_track.title, markdown, html_track))

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "schema_version": "alain_lessard_audiobook_manifest_v3",
                "title": "Alain Lessard Audio Companion",
                "mode": "onward-style-narrative-audio",
                "preferred_voice": VOICE,
                "note": "Scripts are clean Markdown chapters prepared for recording; tables, genealogy lists, personal records, recipes, bibliography, and source lists remain in the readable archive.",
                "tracks": [
                    {
                        "track_number": index,
                        "title": track.title,
                        "script_path": f"script/{track.filename}",
                        "source_ids": list(track.source_ids),
                        "source_label": track.source_label,
                        "word_count": track.word_count,
                        "status": "script-ready",
                        "audio_path": None,
                    }
                    for index, track in enumerate(manifest_tracks, start=1)
                ],
                "skipped_entries": skipped_entries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    README_PATH.write_text(
        "# Alain Lessard Audio Companion\n\n"
        "This folder contains final Onward-style Markdown scripts prepared for recording in ElevenLabs using the voice "
        "\"Matilda\" (voiceId: XrExE9yKIg1WjnnlVkGX).\n\n"
        "Each script is a clean recording chapter. The scripts include narrative family history, stories, poems, memories, "
        "obituaries, and the two companion documents found with the book. Genealogy tables, personal-record forms, recipes, "
        "bibliography, and source lists remain in the readable website and PDFs instead of being narrated.\n\n"
        "When reviewed MP3 files are ready, add their public paths to `manifest.json` and rebuild the site.\n",
        encoding="utf-8",
    )
    print(f"built audiobook scripts: {output_dir}")
    print(f"scripts: {len(manifest_tracks)}")
    print(f"skipped reference entries: {len(skipped_entries)}")
    print(f"manifest: {MANIFEST_PATH}")


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Build final Onward-style audiobook Markdown scripts.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    build(Path(args.output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
