# README artwork and typography

The front README is a visual product showcase, not the operating manual. It uses the official
supplied KC artwork, actual Studio screenshots, existing approved demos and face-free render
sheets. Setup, feature explanations and troubleshooting belong in the named user guides.

## Art direction

- **Silkscreen:** real pixel lettering for the identity, numbered stamps and shipping-label details.
- **Barlow Condensed:** narrow industrial typography for headings and readable supporting text.
- **Kraft paper + deep green ink:** the cardboard material and the Studio's dark/mint palette.
- **Packing-slip rules, decorative barcodes and corrugation:** a consistent visual vocabulary,
  rather than unrelated stock banners. Barcodes are decorative, not machine-readable identifiers.

GitHub does not provide custom README stylesheets. Fonts are rendered into local PNG banners,
so no web font service, CSS, external image host or viewer-installed font is required. Alt text,
ordinary headings and navigation links preserve a usable text path.

The supplied logo is composed without redrawing it. Its canonical master stays unchanged.
Screenshots remain actual widgets; banners are explicitly designed branding graphics, not UI
mockups or runtime measurements.

## Rebuild

Install the project's development extra, then run from the repository root:

```powershell
.\.venv312\Scripts\python.exe scripts\build_readme_art.py
```

The generator reads the package version for the hero label. Outputs are tracked under
`docs\images\readme`. After changing the README, guides, fonts or artwork, refresh the tracked
release source export too.

## Font provenance and licenses

Unmodified font files are pinned to Google Fonts commit
`6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec`:

- [Silkscreen](https://github.com/google/fonts/tree/6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec/ofl/silkscreen):
  Regular and Bold; [included SIL Open Font License](fonts/Silkscreen-OFL.txt).
- [Barlow Condensed](https://github.com/google/fonts/tree/6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec/ofl/barlowcondensed):
  Regular and SemiBold; [included SIL Open Font License](fonts/BarlowCondensed-OFL.txt).

Both families are redistributed under their included OFL 1.1 terms. No font files were modified.
