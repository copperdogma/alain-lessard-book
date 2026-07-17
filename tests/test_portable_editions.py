from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from lxml import etree
from PIL import Image

from scripts.build_family_site import (
    render_portable_handoff,
    render_reading_apps,
    require_portable_artifacts,
    write_site_assets,
)

from scripts.portable_editions import (
    EpubDocument,
    PortableArtifact,
    PortableCatalog,
    PortableEditionError,
    Publication,
    build_epub_package,
    copy_portable_artifacts,
    validate_epub,
)


def fixture_catalog(root: Path, cover: Path) -> PortableCatalog:
    publication = Publication(
        identifier="urn:uuid:26c825db-e424-47aa-82f0-559d0f899c84",
        title="Fixture Family Book",
        subtitle="A fixture subtitle",
        language="en-CA",
        author="Fixture Family",
        publisher="Fixture Family",
        original_publication_year="1987",
        modified="2026-07-17T20:00:00Z",
        description="Fixture description.",
        source_url="https://example.test/",
        cover_source_path=cover,
        cover_output_path=root / "generated-cover.jpg",
    )
    return PortableCatalog(
        manifest_path=root / "manifest.json",
        publication=publication,
        epub=PortableArtifact(
            output_path=root / "fixture.epub",
            public_path="downloads/fixture.epub",
            media_type="application/epub+zip",
            settings={"maximum_bytes": 2_000_000},
        ),
        m4b=PortableArtifact(
            output_path=root / "fixture.m4b",
            public_path="audiobook/fixture.m4b",
            media_type="audio/mp4",
            settings={},
        ),
    )


class PortableEditionTests(unittest.TestCase):
    def test_epub_package_preserves_source_ids_images_and_ocf_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / "cover-source.jpg"
            figure = root / "figure.jpg"
            Image.new("RGB", (400, 600), "#38584f").save(cover, "JPEG")
            Image.new("RGB", (120, 80), "#b8a67c").save(figure, "JPEG")
            catalog = fixture_catalog(root, cover)
            catalog.manifest_path.write_text("{}\n", encoding="utf-8")
            documents = [
                EpubDocument(
                    slug="first-story",
                    title="First Story",
                    part_id="part-i",
                    content_html='<p id="blk-first">A story.</p><figure><img src="images/doc-web/figure.jpg" alt="Fixture family"/><figcaption>A caption.</figcaption></figure>',
                    image_sources={"images/doc-web/figure.jpg": figure},
                ),
                EpubDocument(
                    slug="companion-note",
                    title="Companion Note",
                    part_id="companions",
                    content_html='<p id="blk-first">A companion with a source-local id.</p>',
                    image_sources={},
                    is_main_book=False,
                ),
            ]

            output = build_epub_package(
                catalog,
                documents,
                expected_main_source_ids=["blk-first"],
            )
            validation = validate_epub(
                output,
                expected_document_count=2,
                expected_main_source_ids=["blk-first"],
                maximum_bytes=2_000_000,
            )

            self.assertTrue(validation.ok, validation.errors)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist()[0], "mimetype")
                self.assertEqual(archive.getinfo("mimetype").compress_type, zipfile.ZIP_STORED)
                first = archive.read("EPUB/text/001-first-story.xhtml").decode("utf-8")
                companion = archive.read("EPUB/text/002-companion-note.xhtml").decode("utf-8")
                self.assertIn('id="blk-first"', first)
                self.assertIn('id="companion-note-blk-first"', companion)
                self.assertIn("Fixture family", first)
                self.assertIn("About this digital family edition", first)
                self.assertIn("https://example.test/", first)
                package = archive.read("EPUB/package.opf").decode("utf-8")
                self.assertIn("A fixture subtitle", package)
                self.assertIn("<dc:source>https://example.test/</dc:source>", package)

    def test_epub_does_not_repeat_matching_source_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / "cover.jpg"
            Image.new("RGB", (40, 60), "green").save(cover, "JPEG")
            catalog = fixture_catalog(root, cover)
            catalog.manifest_path.write_text("{}\n", encoding="utf-8")
            document = EpubDocument(
                slug="first-story",
                title="First Story",
                part_id="part-i",
                content_html='<h1 id="story-heading">First Story</h1><p id="blk-first">A story.</p>',
                image_sources={},
            )

            output = build_epub_package(catalog, [document], expected_main_source_ids=["blk-first"])

            with zipfile.ZipFile(output) as archive:
                xhtml = archive.read("EPUB/text/001-first-story.xhtml").decode("utf-8")
            root = etree.fromstring(xhtml.encode("utf-8"))
            headings = root.xpath("//*[local-name()='h1']")
            self.assertEqual(["".join(heading.itertext()) for heading in headings], ["First Story"])
            self.assertIn('aria-label="First Story"', xhtml)

    def test_epub_builder_rejects_image_without_alt_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / "cover.jpg"
            figure = root / "figure.jpg"
            Image.new("RGB", (40, 60), "green").save(cover, "JPEG")
            Image.new("RGB", (40, 40), "blue").save(figure, "JPEG")
            catalog = fixture_catalog(root, cover)
            catalog.manifest_path.write_text("{}\n", encoding="utf-8")
            document = EpubDocument(
                slug="story",
                title="Story",
                part_id="part-i",
                content_html='<p id="blk-one">Text</p><img src="figure.jpg"/>',
                image_sources={"figure.jpg": figure},
            )

            with self.assertRaisesRegex(PortableEditionError, "alternative text"):
                build_epub_package(catalog, [document], expected_main_source_ids=["blk-one"])

    def test_copy_portable_artifacts_keeps_one_declared_public_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / "cover.jpg"
            Image.new("RGB", (40, 60), "green").save(cover, "JPEG")
            catalog = fixture_catalog(root, cover)
            catalog.manifest_path.write_text(json.dumps({"schema_version": "fixture"}), encoding="utf-8")
            catalog.epub.output_path.write_bytes(b"fixture epub")
            catalog.m4b.output_path.write_bytes(b"fixture m4b")
            site = root / "site"

            count, size = copy_portable_artifacts(catalog, site)

            self.assertEqual(count, 2)
            self.assertEqual(size, len(b"fixture epub") + len(b"fixture m4b"))
            self.assertEqual((site / catalog.epub.public_path).read_bytes(), b"fixture epub")
            self.assertEqual((site / catalog.m4b.public_path).read_bytes(), b"fixture m4b")
            self.assertTrue((site / "_internal" / "portable" / "manifest.json").is_file())

    def test_release_requires_both_declared_portable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / "cover.jpg"
            Image.new("RGB", (40, 60), "green").save(cover, "JPEG")
            catalog = fixture_catalog(root, cover)
            catalog.epub.output_path.write_bytes(b"fixture epub")

            with self.assertRaisesRegex(SystemExit, "requires portable editions"):
                require_portable_artifacts(catalog)

            catalog.m4b.output_path.write_bytes(b"fixture m4b")
            require_portable_artifacts(catalog)

    def test_device_help_has_literal_no_javascript_downloads_and_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / "cover.jpg"
            Image.new("RGB", (40, 60), "green").save(cover, "JPEG")
            catalog = fixture_catalog(root, cover)
            catalog.epub.output_path.write_bytes(b"fixture epub")
            catalog.m4b.output_path.write_bytes(b"fixture m4b")
            audiobook = SimpleNamespace(
                full_audiobook=SimpleNamespace(
                    public_audio_path="audiobook/fixture-complete.mp3",
                    is_available=True,
                )
            )

            handoff = render_portable_handoff(catalog)
            help_html = render_reading_apps(catalog, audiobook)

            for path in (
                catalog.epub.public_path,
                catalog.m4b.public_path,
                audiobook.full_audiobook.public_audio_path,
            ):
                self.assertIn(f'href="{path}"', handoff + help_html)
            self.assertIn("Send to Kindle", help_html)
            self.assertIn("Apple Books", help_html)
            self.assertIn("Kobo", help_html)
            self.assertIn("Google Play Books", help_html)
            self.assertNotIn("navigator.userAgent", help_html)

    def test_site_assets_declare_portable_mime_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"

            write_site_assets(site)

            mime_config = (site / ".htaccess").read_text(encoding="utf-8")
            self.assertIn("AddType application/epub+zip .epub", mime_config)
            self.assertIn("AddType audio/mp4 .m4b", mime_config)


if __name__ == "__main__":
    unittest.main()
