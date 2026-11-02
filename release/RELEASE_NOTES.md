# v1.2.0 - Preview-First Studio

A quieter, preview-first native workspace with every operating option retained. Online Windows
setup, cardboard-brown dark sliders, Live/Video processing and automatic playback remain included.
v1.0.0 remains the first official version; v0.2.0 was unpublished local staging.

## 2026-11-03

### More preview, less clutter

- Owner-selected **left settings inspector / large right preview**, with a compact header and
  non-collapsible workspace splitter. The complete fitted image remains visible rather than
  being clipped by a smaller ancestor.
- Labelled expandable sections retain all 45 runtime options and nine live fields. Basic eye
  tuning stays near compact anatomical OPEN/CLOSED decisions; additional timing/avatar/capture
  settings remain accessible without filling the default view.
- **Tools / Ctrl+J** opens a bounded, scrollable Logs/CLI/Diagnostics drawer, closed by default.
  Logs continue collecting when closed. Raw face, mesh and body views never occupy the program
  image or create competing preview columns.
- Video file setup is a scrollable inspector category; export progress stays beside the viewer
  across category changes. Long error messages remain complete in a bounded plain-text surface.
- Presets use a labelled menu. Load/Reset/model jobs visibly disable during work. Existing
  clean output, consent, redaction, helper, default-player and shared-pipeline behaviour remains.
- Explicit headless mode still suppresses local frames intentionally and leaves an explanatory
  workspace. Window layout changes do not crop/recolour/export different video pixels.
- Native containment checks cover compact windows, tools/errors/diagnostics, portrait and
  landscape frames, splitter attempts and controlled 100%/125%/150% Qt scaling. Other hardware,
  live tracking and owner visual/usability approval remain separate.

## 2026-11-02

### Windows installation and theme

- Online **Windows x64 MSI** with patched private Python 3.12.16 and the application wheel.
  No manual Python/pip commands or system Python/PATH changes.
- Start-menu launcher opens a responsive first-launch component wizard. Downloads are
  binary-only and hash locked; verified HTTPS mirrors are supported without shipping private
  feed settings. No TLS bypass is accepted. Cancel/failure never marks components ready.
- Models, recordings and presets use per-user application data. All six helpers are included
  in the wheel; no source checkout is required. Uninstall preserves per-user data/cache.
- Dark slider filled tracks and handles now use warm cardboard brown; mint continues to
  indicate checked/live states. The light theme retains its existing contrast.
- Successful Studio VIDEO exports open their actual saved result in the system's default
  player after cleanup. Failed/cancelled jobs never launch. A refused launch leaves the video
  saved and shows an actionable error. The selected player must support the output codec.
- Canonical extended-length private prefixes avoid Qt wheel extraction failures without
  changing Windows long-path settings. Installer-owned bytecode caches are removed on uninstall.
- Setup is **unsigned** and requires internet on first launch. OBS's installed virtual-camera
  component is separate; AI models remain explicit downloads in Studio.

### Studio and output

- Front-level **LIVE** and **VIDEO** modes distinguish streaming from file processing.
- Forest/mint dark theme and kraft/cream light theme follow the approved top-banner palette.
  Checked boxes have explicit contrasting ticks; restart-only fields dim and show LOCKED.
- Raw face, mesh/pose and body diagnostics occupy dedicated local side panels instead of
  covering the program image. Clean output never includes those panels.
- Separate **KardboardCode - Clean Output** window for OBS Window Capture, independent of
  OBS Virtual Camera. It opens for Live/demo by default and can be reopened from View.
- Bottom **Logs** and **CLI equivalent** tabs, with one-click complete command copying.
- Standard SD/HD/FHD/QHD/4K/portrait and current-display virtual-resolution presets.
- Camera-route labels explain that index 0 is the first device for an API and that Media
  Foundation / DirectShow are backend alternatives, not RGB/IR modes.

### Eye calibration and identity

- Guided relaxed-OPEN / BOTH-CLOSED sampling derives both blink overrides and compatible
  shared open/wink rules. Overlapping samples fail visibly rather than applying guesses.
- Raw eye signals drive closure decisions while pose/geometry remain filtered, so brief
  blinks are not smoothed away. Readouts show the effective rendered decision and threshold.
- Tighter optical icon bounds remove near-invisible outer noise and unnecessary small-size
  margins. The supplied original master remains unchanged; Windows still controls icon-slot size.

### Process an existing video

- Every frame is tracked synchronously in MediaPipe VIDEO mode and rendered at original size.
  Source presentation timing is kept within output-container precision.
- Default **lossless FFV1/MKV** avoids additional compression loss in processed RGB frames.
  Optional **high-quality H.264/MP4 CRF 17** is explicitly lossy.
- Compatible audio streams are copied without re-encoding. No live camera opens.
- New output filenames only, owned temporary files, atomic no-overwrite publication, progress
  and cooperative cancellation. Input/existing files are never replaced.
- Qt-free `python -m kardboard_vtuber.video_cli` shares the processing engine with Studio.
- The old unmasked MP4/CSV recorder remains an advanced Live-mode **Private capture** utility,
  not the meaning of prerecorded-video processing.

### README and documentation

- Milestone raster cards removed. Decorative section/footer art is transparent SVG with real
  font outlines; no external font service is needed.
- The restyled runtime-avatar hero follows the top banner directly and shares its palette.
- Borderless full-width gallery images replace table layouts. The approved original/green-screen
  GIF comparison remains side by side, also without table borders.
- Updated actual synthetic GUI screenshots, tutorial, design rationale, runtime/video
  architecture, guides and engineering handbook.

## Install / launch

**Windows setup:** run `KardboardCode-Studio-windows-x64.msi`, then open KardboardCode Studio
from Start and choose **Install components**. The first launch requires internet. Use Models
for explicit model downloads. Setup does not open a camera.

**Source ZIP:** extract it and open PowerShell in its project folder, then:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -e ".[tracking,virtual-camera,gui]"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

Existing installations should refresh the optional GUI dependencies, including PyAV, and
close/reopen Studio to load the new code/icon assets. Opening Studio lists metadata only;
press Start camera deliberately. Models are verified/downloaded explicitly from Models.

## Known limitations

- Setup targets Windows 10/11 x64 with an OpenGL 3.3-capable graphics driver. ARM64/native
  non-Windows installers and offline installation are not included. Unsigned packages may be
  restricted by SmartScreen/application-control policy; never disable device protections.
- Live distant-face reliability and actual Discord/Teams/Meet qualification remain unconfirmed.
- Experimental shoulder/hood tracking remains available in LIVE, not the selected default;
  no face/side markers does not establish rear orientation.
- RGB hand foreground is approximate, not arbitrary-object depth occlusion.
- Video export supports one opaque, progressive, square-pixel 8-bit SDR video stream with valid
  timing/rate metadata. HDR/high-bit-depth/alpha/rotation/interlacing/changing-dimension inputs
  and extra subtitle/data/attachment streams fail explicitly. MP4 requires even dimensions
  and compatible audio codecs.
- MKV may quantize source timestamps to milliseconds. The source bitstream cannot remain
  byte-identical after adding an avatar; lossless describes the processed RGB video.
- Lossless files can be large. Final publication needs a destination filesystem supporting
  hard links, such as local NTFS; failure is explicit and existing files remain untouched.
- The advanced private recorder saves unmasked footage and retains its earlier fixed-FPS
  duration limitation at low capture throughput.
- Camera indices can change with hardware changes. Refresh/reselect before live capture.
- Source ZIP excludes models, recordings, environments, credentials and private context.
  MSI intentionally includes the pinned private Python runtime and its licenses, not third-party
  dependency wheels. Dependencies, codecs and fonts retain their own licenses. No custom driver.
