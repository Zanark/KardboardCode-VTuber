# v1.1.0 - Studio Workspaces

The fifteen-point live-use feedback pass: clearer controls, unobstructed program video,
separate clean output, meaningful eye calibration and genuine prerecorded-video processing.
v1.0.0 remains the first official version; v0.2.0 was unpublished local staging.

## 2026-11-02

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

This is a **source release**, not a standalone executable/installer. Extract the source ZIP,
open PowerShell in its project folder, then:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -e ".[tracking,virtual-camera,gui]"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

Existing installations should refresh the optional GUI dependencies, including PyAV, and
close/reopen Studio to load the new code/icon assets. Opening Studio lists metadata only;
press Start camera deliberately. Models are verified/downloaded explicitly from Models.

## Known limitations

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
- Models, recordings, environments, credentials and private context are excluded. Dependencies,
  codecs and bundled fonts retain their own licenses. No custom camera driver is installed.
