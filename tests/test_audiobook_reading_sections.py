from __future__ import annotations

import unittest
from types import SimpleNamespace

from scripts.reading_sections import ReadingSource, build_reading_catalog


def source(entry_id: str, title: str, order: int, article_html: str) -> ReadingSource:
    return ReadingSource(
        entry_id=entry_id,
        title=title,
        kind="page" if entry_id.startswith("page-") else "chapter",
        order=order,
        source_pages=(order,),
        printed_pages=(order,),
        article_html=article_html,
    )


def track(number: int, title: str, targets: tuple[str, ...]) -> SimpleNamespace:
    return SimpleNamespace(
        track_number=number,
        title=title,
        target_entry_ids=targets,
    )


class ReadingSectionTests(unittest.TestCase):
    def test_groups_print_pages_splits_shared_stories_and_preserves_reference_html(self) -> None:
        sources = [
            source("page-001", "Page 1", 1, '<h1 id="coat">Part I</h1><p id="coat-copy">Coat of arms.</p>'),
            source("page-002", "Page 2", 2, '<h1 id="intro">Introduction</h1><p id="intro-copy">Opening.</p>'),
            source("page-004", "Page 3", 3, '<p id="history-copy">Family history continued.</p>'),
            source(
                "chapter-001",
                "Louis and Clara",
                4,
                '<h1 id="louis">Louis and Clara (Lessard) Alain</h1><p id="louis-copy">Louis story.</p>'
                '<h2 id="marlyne">Marlyne (Alain) Reindl</h2><p id="marlyne-copy">Marlyne story.</p>'
                '<h1 id="genealogy">Alain Genealogy</h1><table id="family-table"><tr><td>Family</td></tr></table>',
            ),
        ]
        tracks = [
            track(4, "Part I - Alain Family History", ("page-002", "page-004")),
            track(7, "Louis and Clara (Lessard) Alain", ("chapter-001",)),
            track(8, "Marlyne (Alain) Reindl", ("chapter-001",)),
        ]

        catalog = build_reading_catalog(sources, tracks)

        part_i = catalog.section_for_track(4)
        self.assertIsNotNone(part_i)
        self.assertEqual(part_i.source_entry_ids, ("page-001", "page-002", "page-004"))
        self.assertIn("Coat of arms", part_i.article_html)
        self.assertIn("Family history continued", part_i.article_html)
        self.assertEqual(catalog.section_for_track(7).title, "Louis and Clara (Lessard) Alain")
        self.assertEqual(catalog.section_for_track(8).title, "Marlyne (Alain) Reindl")
        self.assertNotEqual(catalog.section_for_track(7).path, catalog.section_for_track(8).path)
        reference_html = "\n".join(section.article_html for section in catalog.sections if not section.track_numbers)
        self.assertIn("Alain Genealogy", reference_html)
        self.assertIn("family-table", reference_html)
        self.assertEqual(catalog.redirects["page-002"], part_i.path)
        self.assertFalse(catalog.unassigned_source_entry_ids)

    def test_each_narrative_track_has_only_one_semantic_read_target(self) -> None:
        sources = [
            source("page-012", "Page 7", 1, '<h1 id="henri">Henri Delphice Alain</h1><p>One.</p>'),
            source("page-013", "Page 8", 2, '<p id="henri-two">Two.</p>'),
            source("page-014", "Page 9", 3, '<p id="henri-three">Three.</p>'),
        ]
        tracks = [track(5, "Part II - Alain Family Stories: Henri Delphice Alain", ("page-012", "page-013", "page-014"))]

        catalog = build_reading_catalog(sources, tracks)

        matches = [section for section in catalog.sections if 5 in section.track_numbers]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].source_entry_ids, ("page-012", "page-013", "page-014"))
        self.assertNotRegex(matches[0].title, r"^Page \d+$")


if __name__ == "__main__":
    unittest.main()
