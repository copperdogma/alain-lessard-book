# Reunion Flyer Physical Validation Record

This record closes the only non-digital Story 006 acceptance boundary. Test the
exact final artifacts identified below; if either file changes, update its hash
and repeat the affected checks.

## Artifacts under test

| Surface | Path | SHA-256 |
| --- | --- | --- |
| Letter flyer | `output/outreach/alain-lessard-reunion-flyer-letter.pdf` | `fca4e010a7b2e4efede1f511d1c3d58b8f7113be0e397872ef3dbd5f930980ab` |
| Phone card | `output/outreach/alain-lessard-phone-qr.png` | `e0847c2281c7049c09f25a3018b9a754a7f9c78a91951c0a506bc947ee7b3f50` |

Expected destination for every scan:
`https://alain-lessard.copper-dog.com/`

## Print setup and visual proof

- Date tested: 2026-07-19
- Tester: user
- Printer make/model: home laser printer; model not reported
- Paper: white US Letter; stock not reported
- Print setting: 100% / Actual size, with Fit to page disabled
- Page is portrait and complete, with no clipped text or rules: accepted by user
- Title, hostname, actions, and family names are comfortably readable: accepted by user
- QR is crisp, square, undamaged, and surrounded by white space: accepted by user
- Original dark-green cover is recognizable, the same height as the QR, and
  not cropped or distorted: accepted by user
- Color/grayscale hierarchy is clear without relying on color alone: accepted by user
- Notes or defects: user reported the revised flyer `works perfectly`

## Printed-flyer scan matrix

Use two real phones or two genuinely independent camera implementations. Each
successful result must open or recognize the exact expected HTTPS destination.

| Camera | Distance | Lighting | Result | Notes |
| --- | --- | --- | --- | --- |
| Phone/camera A | 3 ft | Bright | not separately reported | Covered by user's overall acceptance |
| Phone/camera A | 3 ft | Shade | not separately reported | Covered by user's overall acceptance |
| Phone/camera A | 6 ft | Bright | not separately reported | Covered by user's overall acceptance |
| Phone/camera A | 6 ft | Shade | not separately reported | Covered by user's overall acceptance |
| Phone/camera B | 3 ft | Bright | not separately reported | Covered by user's overall acceptance |
| Phone/camera B | 3 ft | Shade | not separately reported | Covered by user's overall acceptance |
| Phone/camera B | 6 ft | Bright | not separately reported | Covered by user's overall acceptance |
| Phone/camera B | 6 ft | Shade | not separately reported | Covered by user's overall acceptance |

## Phone-card scan matrix

Display the PNG full-screen without cropping or zooming. Scan it with a second
physical device.

| Display brightness | Result | Notes |
| --- | --- | --- |
| Normal | not separately reported | User explicitly accepted and closed the final artifact family |
| High/outdoor | not separately reported | User explicitly accepted and closed the final artifact family |

## Completion decision

- All visual and scan checks above pass: accepted by the user as an equivalent
  overall real-world result; individual distance/light/device cells were not
  separately enumerated
- Physical acceptance decision: accepted on 2026-07-19
- Follow-up required: none; user directed Story 006 closure

## Superseded preliminary print evidence

On 2026-07-19, the user printed the earlier cover-free flyer (PDF SHA-256
`b747cf4dc35561149c563e31389ec10745590f4190b8e54f320bca21a62d4248`),
successfully tried its QR, and reported `Very good!`. That proves the basic
printer/QR approach but does not transfer to the revised cover-bearing PDF hash
above. Repeat the matrix against the current artifact before final acceptance.
An intermediate cover-bearing PDF with SHA-256 `880424b6...a04c` used a
smaller two-inch-wide cover and was superseded before physical testing.

## Environment evidence before physical testing

On 2026-07-19, the build Mac exposed no usable printer: `lpstat -p -d`
reported no system default destination, and `system_profiler
-json SPPrintersDataType` returned `no_info_found`. A second physical phone is
also outside the build environment. These are external proof requirements, not
digital-test substitutes.
