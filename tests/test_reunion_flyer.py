from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from scripts.build_reunion_flyer import (
    DEFAULT_MANIFEST,
    FlyerCatalog,
    FlyerError,
    PHONE_PIXELS,
    PRINT_PREVIEW_PIXELS,
    balanced_rows,
    build_outputs,
    cover_record,
    flattened_pixels,
    load_catalog,
    make_letter_drawing,
    qr_metadata,
    register_fonts,
    sha256,
    validate_manifest_data,
    validate_outputs,
)


ROOT = Path(__file__).resolve().parents[1]
PDFTOCAIRO = shutil.which("pdftocairo")
PDFFONTS = shutil.which("pdffonts")


def base_data() -> dict:
    return json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))


def fixture_catalog(root: Path, mutate=None) -> FlyerCatalog:
    data = base_data()
    if mutate:
        mutate(data)
    manifest = root / "outreach" / "reunion-flyer.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    cover_source = ROOT / data["artwork"]["cover_source_path"]
    cover_destination = root / data["artwork"]["cover_source_path"]
    cover_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cover_source, cover_destination)
    validate_manifest_data(data)
    return FlyerCatalog(manifest_path=manifest, root=root, data=data)


class ReunionFlyerContractTests(unittest.TestCase):
    def test_canonical_manifest_is_valid_and_has_expected_qr_geometry(self) -> None:
        catalog = load_catalog()
        metadata = qr_metadata(catalog)

        self.assertEqual(catalog.canonical_url, "https://alain-lessard.copper-dog.com/")
        self.assertEqual(catalog.display_url, "alain-lessard.copper-dog.com")
        self.assertEqual(metadata["version"], 4)
        self.assertEqual(metadata["data_modules"], 33)
        self.assertEqual(metadata["total_modules"], 41)
        self.assertEqual(catalog.cover_path, ROOT / "input/doc-web-html/alain-lessard-book-r1/images/page-001-000.jpg")
        self.assertEqual(sha256(catalog.cover_path), catalog.data["artwork"]["cover_expected_sha256"])

    def test_letter_cover_matches_qr_height_and_group_stays_inside_safe_margins(self) -> None:
        catalog = load_catalog()
        cover = cover_record(catalog)
        qr_size = float(catalog.data["qr"]["print_size_points"])
        gap = float(catalog.data["artwork"]["letter_gap_to_qr_points"])
        safe_margin = float(catalog.data["surfaces"]["letter"]["safe_margin_points"])

        self.assertAlmostEqual(float(cover["letter_points"][1]), qr_size, places=3)
        self.assertLessEqual(float(cover["letter_points"][0]) + gap + qr_size, 612 - 2 * safe_margin)

    def test_cover_source_hash_must_match_before_layout(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            def mutate(data: dict) -> None:
                data["artwork"]["cover_expected_sha256"] = "0" * 64

            catalog = fixture_catalog(Path(tmp), mutate)
            with self.assertRaisesRegex(FlyerError, "cover SHA-256"):
                make_letter_drawing(catalog)

    def test_reader_copy_rejects_forbidden_no_account_language(self) -> None:
        data = base_data()
        data["copy"]["headline"] = "No account needed"

        with self.assertRaisesRegex(FlyerError, "forbidden phrase"):
            validate_manifest_data(data)

    def test_display_hostname_must_match_encoded_https_url(self) -> None:
        data = base_data()
        data["publication"]["display_url"] = "example.test"

        with self.assertRaisesRegex(FlyerError, "display_url"):
            validate_manifest_data(data)

    def test_family_names_fit_three_balanced_rows_at_accessible_size(self) -> None:
        register_fonts()
        catalog = load_catalog()
        rows = balanced_rows(catalog.data["family_names"], "AlainFlyerVera", 18, 520, 3)

        self.assertEqual(len(rows), 3)
        self.assertIn("Alain / Allain", rows[0])
        self.assertIn("Folley", rows[-1])

    def test_longer_cross_book_fixture_keeps_the_shared_layout_buildable(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            root = Path(tmp)

            def mutate(data: dict) -> None:
                data["publication"]["display_title"] = "Onward to the Unknown"
                data["publication"]["formal_subtitle"] = "The remarkable story of a family journey across generations"
                data["publication"]["canonical_url"] = "https://onward.copper-dog.com/"
                data["publication"]["display_url"] = "onward.copper-dog.com"
                data["family_names"] = [
                    "Alexander",
                    "Beauchamp",
                    "Christensen",
                    "Desrochers",
                    "Fournier",
                    "Gauthier",
                    "Henderson",
                    "MacDonald",
                    "Richardson",
                    "Thompson",
                    "Williams",
                    "Young",
                ]

            catalog = fixture_catalog(root, mutate)
            drawing = make_letter_drawing(catalog)

            self.assertEqual((drawing.width, drawing.height), (612, 792))


@unittest.skipUnless(PDFTOCAIRO and PDFFONTS, "Poppler is required for flyer artifact tests")
class ReunionFlyerArtifactTests(unittest.TestCase):
    def test_build_outputs_have_exact_surfaces_fonts_copy_and_low_toner_ratio(self) -> None:
        (ROOT / "tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp:
            catalog = fixture_catalog(Path(tmp))

            outputs = build_outputs(catalog)
            validation = validate_outputs(catalog, decode_qr=False)

            self.assertTrue(validation.ok, validation.errors)
            self.assertEqual(set(outputs), {"letter_pdf", "letter_preview_png", "phone_png", "qr_png", "build_report_json"})
            embedded_images = list(PdfReader(str(outputs["letter_pdf"])).pages[0].images)
            self.assertEqual(len(embedded_images), 1)
            self.assertEqual(embedded_images[0].image.size, (2550, 3371))
            with Image.open(outputs["letter_preview_png"]) as image:
                self.assertEqual(image.size, PRINT_PREVIEW_PIXELS)
                self.assertEqual(image.convert("RGB").getpixel((0, 0)), (255, 255, 255))
            with Image.open(outputs["phone_png"]) as image:
                self.assertEqual(image.size, PHONE_PIXELS)
            with Image.open(outputs["qr_png"]) as image:
                self.assertEqual(image.size, (1640, 1640))
                self.assertEqual(set(flattened_pixels(image.convert("RGB"))), {(0, 0, 0), (255, 255, 255)})
            self.assertLessEqual(
                validation.metrics["letter_non_white_ratio"],
                catalog.data["constraints"]["maximum_non_white_preview_ratio"],
            )
            self.assertEqual(
                set(validation.metrics["stress_variants"]),
                {
                    "letter_50_percent",
                    "letter_25_percent",
                    "letter_25_percent_grayscale",
                    "letter_camera_proxy",
                    "phone_80_percent_brightness",
                    "phone_65_percent_brightness",
                },
            )


if __name__ == "__main__":
    unittest.main()
