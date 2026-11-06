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

## Current Studio GIFs and screenshots

The front page keeps seven images: banner, avatar hero, combined dark/light Studio GIF,
approved original/green-screen comparison pair and two full-width theme screenshots.
Separate dark/light GIFs and the former recorded-motion avatar animation live in the gallery.
The approved comparison files are not regenerated or replaced by this refresh.

```powershell
.\.venv312\Scripts\python.exe scripts\capture_readme_media.py
```

The capture helper runs the real synthetic Studio demo, reusing the complete reference's
safe example paths and diagnostic fixtures. It disables physical-device discovery and grabs
only owned native widgets, never the desktop or a camera. Before each capture it verifies
that the Demo worker and expected page are still active, without a helper job or visible error.
The two PNGs are 1440x810; GIFs are 1200x675, loop indefinitely and cover eye controls,
output controls and the optional Logs drawer. Dark/light loops are 7.6 seconds each;
the combined front clip is 15.2 seconds. On-screen labels explicitly distinguish
synthetic diagnostic fixtures from live data.

Generated public files are `docs\images\kardboardcode-studio-dark.png`,
`kardboardcode-studio-light.png` and the three `kardboardcode-studio-walkthrough*.gif` files.
The ignored `build\readme-media` receipt records frame/timing/byte/source hashes, actual
changed demo frames and unchanged approved-media hashes. Review bounded keyframes rather
than decoding/reviewing every frame; inspect additional frames only for an unresolved issue.
PNG source size is retained; GIFs are proportionally resized and palette-encoded, not cropped.
This is documentation media, not new runtime, camera or privacy qualification.

README changes also change application-wheel metadata. Refresh the dependent handbook,
source ZIP and online unsigned MSI through the existing build commands, preserving explicit
model/OBS prerequisites and honest uncommitted provenance. Do not publish or commit automatically.

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
