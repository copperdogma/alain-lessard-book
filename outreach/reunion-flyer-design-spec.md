# Reunion Flyer Design and Reproduction Specification

This is the portable design handoff for Story 006. It describes how to recreate
the Alain Lessard flyer and phone QR card, and how another book project should
make a visibly matching companion without copying Alain-specific content or
colors blindly.

## Deliverables

| Surface | Final format | Exact size | Purpose |
| --- | --- | --- | --- |
| Print master | PDF | 612 x 792 points; one US Letter page | Print at 100% scale |
| Print preview | RGB PNG | 2550 x 3300 pixels | Exact 300 ppi render of the PDF |
| Phone card | RGB PNG | 1080 x 1920 pixels | Full-screen sharing from a phone |
| QR master | RGB PNG | 1640 x 1640 pixels | Reusable black-and-white QR asset |
| Build report | JSON | N/A | Tool, font, QR, path, size, and hash evidence |

The final artifacts live under `output/outreach/`. Temporary vector phone
output lives under `tmp/pdfs/outreach/` and is not a reader-facing deliverable.

## Approved Toolchain

- Python using ReportLab for vector drawing, PDF output, and QR encoding.
- ReportLab-bundled Bitstream Vera Sans regular and bold TrueType fonts. The
  files and license are resolved relative to the installed ReportLab package;
  the PDF embeds subsets of both fonts.
- Poppler `pdftocairo` for the exact print-preview and phone PNG renders.
- Pillow for the standalone integer-module QR PNG and image inspection.
- pypdf and Poppler `pdffonts` for page, selectable-text, and font checks.
- macOS Vision through `scripts/decode_qr_vision.swift` for independent QR
  decoding. Swift's module cache is kept at `/tmp/alain-lessard-qr-swift-cache`.
- The validator generates disposable stress variants under
  `tmp/pdfs/outreach/stress/`: 50% and 25% flyer reductions, a 25% grayscale
  reduction, a 50% camera proxy with 0.8-pixel blur and JPEG quality 55, and
  phone cards at 80% and 65% brightness. These are validation evidence, not
  deliverables.

Source Sans Pro was evaluated but not selected: the locally installed OTF files
use CFF/PostScript outlines, which ReportLab 4.4.9 cannot embed. ReportLab's
optional direct-PNG backend is also absent, so every layout PNG is rendered from
its vector PDF with Poppler instead of adding a new dependency.

## Canonical Contract

`outreach/reunion-flyer.json` owns:

- book title and subtitle;
- canonical HTTPS QR destination and large display hostname;
- reader-facing actions and camera instruction;
- source-backed family names;
- canonical letter-cover path, expected dimensions/hash, and print geometry;
- website-derived palette;
- font, minimum-size, QR, surface, and low-toner constraints;
- stable output paths.

The generator must fail if the display hostname differs from the encoded URL,
the page is not true white, required content is missing, essential type falls
below 18 points, or prohibited wording appears.

## Shared Visual System

Use these values for a matching book flyer unless its content forces the
documented adaptation path.

### Print geometry

Coordinates are PDF points from the bottom-left of a 612 x 792 point page.

| Component | Geometry or baseline | Style |
| --- | --- | --- |
| Safe margin | 36 points | No essential content outside |
| Top red rule | x 36-576; y 766; 2.4 pt | Book accent |
| Top gold rule | x 36-576; y 760; 1.2 pt | Secondary accent |
| Eyebrow | centered; baseline 735 | Vera Bold 15 pt; accent |
| Book title | centered; baseline 685 | Vera Bold 48 pt; deep color |
| Subtitle | centered; first baseline 650; 22 pt leading | Vera 16-17 pt; ink |
| Free headline | centered; baseline 600 | Vera Bold 21 pt; secondary deep |
| Camera instruction | centered; baseline 578 | Vera 18 pt; ink |
| Original cover | x 36.003; y 272; 223.305 × 295.2 pt | Same 4.1-inch height as QR; native aspect ratio |
| QR field | x 280.797; y 272; 295.2 pt square | 4.1 inches; Q correction |
| Display hostname | centered; baseline 241 | Vera Bold 23 pt; accent |
| Action columns | x 49 and 313; baselines 200 and 171 | Vera 18 pt; small gold bullet |
| Family heading | centered; baseline 140 | Vera Bold 13 pt; muted; nonessential label |
| Family-name rows | centered; baselines 110, 82, 54 | Vera 18 pt; deep color |
| Bottom rules | y 27 and 21 | Light line plus short gold rule |

The QR size is 41 total modules at 7.2 points per module. At 300 ppi this is
exactly 30 pixels per module and 1230 pixels square, including its quiet zone.
The cover/QR group is centered as one 539.995-point row with a 21.49-point
white gap. Both images share the same baseline and exact 295.2-point height.

### Cover artwork

- Canonical source:
  `input/doc-web-html/alain-lessard-book-r1/images/page-001-000.jpg`
- Source dimensions: 2550 × 3371 pixels
- Source SHA-256:
  `ac6d36744370bf7bf09d01de39dc1715cb4227d0bee2a3b308e9334e7d6e24bb`
- Printed geometry: 223.305 × 295.2 points, or 3.101 × 4.1 inches
- Effective embedded resolution: about 822.2 ppi in both directions
- Treatment: preserve the complete scanned cover, aspect ratio, and color;
  apply no crop, retouch, transparency, tint, shadow, caption, or decorative
  frame
- Scope: letter flyer only. The phone card remains cover-free so its QR stays
  dominant.

This is the accepted `doc-web` cover image and the declared source for the
portable EPUB/M4B cover. The build fails if its path, dimensions, or hash
changes. The PDF validator requires exactly one embedded raster image with the
same 2550 × 3371 pixel dimensions.

### Phone geometry

Coordinates are pixels from the bottom-left of a 1080 x 1920 vector page that
Poppler renders at 72 ppi to an exact 1080 x 1920 PNG.

| Component | Geometry or baseline | Style |
| --- | --- | --- |
| Safe margin | 72 pixels | No essential content outside |
| Top rules | y 1845 and 1827 | 8 px accent; 4 px secondary accent |
| Eyebrow | centered; baseline 1750 | Vera Bold 38 px |
| Book title | centered; baseline 1625 | Vera Bold 92 px |
| Subtitle | centered; first baseline 1540; 48 px leading | Vera 34-38 px |
| Free headline | centered; baseline 1380 | Vera Bold 43 px |
| Camera instruction | centered; baseline 1310 | Vera 32 px |
| QR field | x 130; y 430; 820 px square | Exactly 20 px per total QR module |
| Display hostname | centered; baseline 335 | Vera Bold 52 px |
| Availability line | centered; baseline 255 | Vera Bold 29 px |
| Bottom rules | y 132 and 112 | Light line plus short secondary accent |

The phone card intentionally omits the family-name band. Its job is to present
the book name, a dominant QR, and a typeable URL while the user is moving around
the reunion.

## Alain Color System

The background is always true paper white. Do not reproduce the website's pale
canvas background or its large dark hero treatments on the printed flyer.

| Role | Hex | Use |
| --- | --- | --- |
| Paper | `#ffffff` | Entire background and QR quiet zone |
| Ink | `#22231f` | Main explanatory text |
| Muted | `#626861` | Small nonessential label only |
| Light rule | `#d8ddd5` | Thin separators |
| Deep | `#143d3b` | Title and family names |
| Secondary deep | `#1f5b55` | Free headline |
| Accent | `#8d2f23` | Eyebrow, hostname, thin rule |
| Secondary accent | `#c1912f` | Thin rule and small bullets |
| QR | `#000000` | QR modules only |

Color may appear only in type, thin rules, and small bullets. There is no dark
masthead, tinted panel, background image, or other large toner-heavy field. The
print preview's non-white pixel ratio, including the QR, must remain at or below
27 percent, and all content must remain understandable in grayscale.

The canonical book cover is the only bounded dark image and is a recognition
aid rather than a decorative fill. Its 4.1-inch height deliberately matches the
QR so relatives can recognize it at a glance. The revised flyer measures
25.6722 percent non-white coverage, including the cover and QR, leaving 74.3278
percent of the page white and remaining below the 27 percent ceiling.

## QR Specification

- Encoded value: `https://alain-lessard.copper-dog.com/`
- ReportLab error-correction level: Q
- QR version: 4
- Data matrix: 33 x 33 modules
- Quiet zone: 4 modules on every side
- Total matrix: 41 x 41 modules
- Print size: 295.2 points / 4.1 inches
- Phone size: 820 pixels
- Standalone master: 40 pixels per module / 1640 pixels square
- Colors: pure black modules on pure white only; no logo, texture, rounding,
  transparency, or colored background

The print preview, phone PNG, and standalone QR PNG must each independently
decode to the exact canonical HTTPS URL.

## Book-Specific Substitutions for Onward

Keep the grids, white background, typography, hierarchy, QR treatment, action
structure, spacing, and export settings. Replace only:

- display title and formal subtitle;
- canonical URL and display hostname;
- family names or equivalent source-backed discovery terms;
- canonical front-cover source, dimensions, hash, and aspect ratio;
- truthful format/action wording;
- accent palette, sampled from the Onward website;
- output basenames and book-specific verification evidence.

The accent colors should be different for the two books so side-by-side flyers
remain easy to distinguish. Onward must still use white as the page background
and avoid large solid fills for the same home-laser-printer constraint.

If content does not fit, first use an approved alternate line break, then reduce
only flexible gaps, then rebalance the family-name rows, then shorten optional
descriptive copy. Never reduce essential print text below 18 points, the display
hostname below 23 points, or the verified QR size.

For a matching Onward flyer, keep the cover and QR at the same 295.2-point
height, derive the cover width from Onward's canonical aspect ratio, preserve
the full-size QR, and center the combined row. Start with a 21.49-point gap. If
the other cover makes the row wider than the 540-point safe area, reduce only
that gap to the documented minimum before considering a deliberate QR-size
variant; never crop or stretch the cover.

## Reproduction Commands

```bash
make test-reunion-flyer
make build-reunion-flyer
make validate-reunion-flyer
```

The combined build-and-validate command is:

```bash
make reunion-flyer
```

Additional inspection commands:

```bash
pdfinfo output/outreach/alain-lessard-reunion-flyer-letter.pdf
pdffonts output/outreach/alain-lessard-reunion-flyer-letter.pdf
pdftotext output/outreach/alain-lessard-reunion-flyer-letter.pdf -
shasum -a 256 output/outreach/*
```

## Final Artifact Evidence

`output/outreach/reunion-flyer-build-report.json` records the exact tool
versions, font/license hashes, QR geometry, artifact dimensions, byte sizes,
and SHA-256 hashes produced by the final build.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `alain-lessard-reunion-flyer-letter.pdf` | 5,493,099 | `fca4e010a7b2e4efede1f511d1c3d58b8f7113be0e397872ef3dbd5f930980ab` |
| `alain-lessard-reunion-flyer-letter-preview.png` | 2,737,060 | `7a4cc11e3c526aeb8941be6baf4c91e4b4a21fb344c9d3b9e4b22dbc6dc1d035` |
| `alain-lessard-phone-qr.png` | 92,734 | `e0847c2281c7049c09f25a3018b9a754a7f9c78a91951c0a506bc947ee7b3f50` |
| `alain-lessard-qr.png` | 11,710 | `325e476dfea5126979b3ac52a4dc8032f2736afb1e6767ac6548bb86ab0262ba` |
| `reunion-flyer-build-report.json` | 2,401 | `08fe898181fbb1a89cf0abed9430c7785b6fce5db6d38576cd5a97d31ef98602` |

Final local tool versions are Python 3.12.13, ReportLab 4.4.9, Pillow 12.2.0,
and Poppler/pdftocairo 25.04.0. The embedded font hashes are recorded in the
build report.

Digital verification on 2026-07-18 proved:

- one exact 612 x 792 point PDF page with selectable title, hostname, and
  action text plus embedded/subset Bitstream Vera regular and bold fonts;
- exact 2550 x 3300, 1080 x 1920, and 1640 x 1640 RGB PNG surfaces;
- 25.6722 percent non-white print-preview coverage and 15.8307 percent phone
  coverage, both well inside the declared toner limits;
- exactly one embedded 2550 × 3371 JPEG cover, matching the accepted source
  path/hash at an effective 822.2 ppi with no crop or aspect-ratio change;
- a pure black-and-white QR master with version 4, 33 data modules, four quiet
  modules per edge, and Q error correction;
- exact URL decoding from the full print preview, phone card, standalone QR,
  50-percent and 25-percent print-preview reductions, a 25-percent grayscale
  reduction, a blurred/JPEG-compressed camera proxy, and phone simulations at
  80 and 65 percent brightness;
- clean full-resolution color, phone, and grayscale visual inspection with no
  clipping, overlap, broken glyph, or low-contrast hierarchy defect;
- public HTTP 200 responses for the canonical homepage, book reader, searchable
  PDF, EPUB, complete MP3, and M4B with the expected MIME types.

The remaining physical validation is intentionally not inferred from digital
proof. The user printed and successfully scanned the prior cover-free PDF and
judged it `Very good!`, but that evidence is superseded by this cover-bearing
PDF and its new hash. Print the revised PDF at 100 percent on the intended home
laser printer, inspect the paper result, and scan it with two real phones at 3
and 6 feet in bright and shaded conditions. Record those results in
`outreach/reunion-flyer-physical-validation.md` and Story 006 before marking it
Done.
