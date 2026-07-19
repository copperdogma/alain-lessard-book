# Reunion Flyer Printing and Sharing

## Print the RV flyer

Use:

`output/outreach/alain-lessard-reunion-flyer-letter.pdf`

Recommended print settings:

- US Letter, portrait
- print at **100%** or **Actual size**; turn off `Fit to page`
- color mode if available; the design also remains clear in grayscale
- plain or matte white laser-printer paper
- one-sided printing

After printing, confirm that no text or rules were clipped and scan the QR with
two available phone cameras from about 3 feet and 6 feet. Check once in bright
light and once in shade. Mount the flyer near eye level and avoid placing a
tinted window, glossy laminate, or reflective tape over the QR. A clear outdoor
sleeve is useful if it does not create glare.

The letter flyer intentionally includes the original dark-green 1987 book
cover beside the QR so relatives who already know the physical book can
recognize it immediately. Confirm that the cover remains recognizable on the
actual laser print. The phone image remains QR-dominant and does not include the
cover.

## Show the QR from a phone

Use:

`output/outreach/alain-lessard-phone-qr.png`

Open the image full-screen and raise screen brightness when outdoors. A second
phone should scan it at both normal and high brightness before reunion use.

The reusable QR-only image is:

`output/outreach/alain-lessard-qr.png`

All three QR-bearing images encode:

`https://alain-lessard.copper-dog.com/`

Record the printer, visual inspection, two-phone distance/light matrix, and
phone-screen checks in `outreach/reunion-flyer-physical-validation.md`. That
record is tied to the final PDF and phone-image hashes so a later rebuild cannot
silently inherit an earlier physical pass.

## Rebuild or validate

```bash
make test-reunion-flyer
make reunion-flyer
```

The content and design contract is `outreach/reunion-flyer.json`. Exact
geometry, palette, typography, QR settings, and cross-book substitution rules
are documented in `outreach/reunion-flyer-design-spec.md`.
