# README artwork and typography

The front README is a visual product showcase, not the operating manual. It uses the official
supplied KC artwork, actual Studio screenshots, existing approved demos and face-free render
sheets. Setup, feature explanations and troubleshooting belong in the named user guides.

Gallery layout is borderless: no HTML/Markdown image tables. Images stack at full width with
captions. The user-approved original-background / green-screen GIF comparison is the sole
side-by-side pair, using plain HTML images in a paragraph, without table borders or frames.

## Art direction

- **Silkscreen:** real pixel lettering for the identity, numbered stamps and shipping-label details.
- **Barlow Condensed:** narrow industrial typography for headings and readable supporting text.
- **Kraft paper + deep green ink:** the cardboard material and the Studio's dark/mint palette.
- **Packing-slip rules and corrugation:** the top banner and runtime-avatar hero share a palette.
  The avatar hero sits immediately below the top banner. Decorative barcodes are not functional.
- **No milestone image cards:** that section is short text. Decorative section labels/footer
  use transparent SVG with outlined font glyphs, not raster UI cards or a solid paper canvas.

GitHub does not provide custom README stylesheets. The top banner/real-render hero use local PNG;
section/footer lettering is real SVG paths with no raster embedding or canvas background.
No web font service, external image host or viewer-installed font is required. Ordinary headings,
navigation and alt text preserve a usable text path. These colors also define both GUI themes.

The supplied logo is composed without redrawing it. Its canonical master stays unchanged.
Screenshots remain actual widgets; banners are explicitly designed branding graphics, not UI
mockups or runtime measurements.

## Rebuild

Install the project's development extra, then run from the repository root:

```powershell
.\.venv312\Scripts\python.exe scripts\build_readme_art.py --avatar-hero
```

The generator reads the package version for the top banner. PNG/SVG outputs are under
`docs\images\readme`; the real runtime-avatar hero is `docs\images\kardboardcode-hero.png`.
The optional hero rebuild uses the actual GPU renderer, not a camera. After public changes,
refresh the tracked source-release export. Pillow and fontTools are development dependencies.

## Font provenance and licenses

Unmodified font files are pinned to Google Fonts commit
`6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec`:

- [Silkscreen](https://github.com/google/fonts/tree/6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec/ofl/silkscreen):
  Regular and Bold; [included SIL Open Font License](fonts/Silkscreen-OFL.txt).
- [Barlow Condensed](https://github.com/google/fonts/tree/6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec/ofl/barlowcondensed):
  Regular and SemiBold; [included SIL Open Font License](fonts/BarlowCondensed-OFL.txt).

Both families are redistributed under their included OFL 1.1 terms. No font files were modified.
