# v0.2.0 - Native Desktop Studio

A native Python desktop interface for KardboardCode's camera-tracked PS1-style cardboard avatar,
while retaining the existing CLI.

## 2026-11-02

### New features

- Native PySide6 Studio with camera setup, preview, diagnostics, selectable logs, source-free
  presets, light/dark themes, and an original KC cardboard-box icon.
- Live independent anatomical left/right blink thresholds, relative wink tuning, brightness
  and debounce controls shared with the renderer/action detector.
- Explicit laptop/USB camera selection by Windows device name, with metadata-only discovery
  and matching Media Foundation/DirectShow index/backend routing.
- Access to all 45 runtime CLI controls, private guided/free recording, model verification,
  experimental tracking modes, and a nine-part built-in tutorial.
- Direct clean output through the installed OBS Virtual Camera component; OBS itself can remain
  closed. This is the existing OBS device, not a new KardboardCode-named camera driver.

### Fixes and safety

- Cooperative startup/shutdown and cleanup of partially initialized resources.
- Cancelled model initialization does not subsequently open capture/output.
- Invalid tuning stays visible without replacing the last valid configuration.
- Literal source argument handling, explicit parser-exit failures, and stronger endpoint
  redaction in GUI log copies.
- Existing zero-duration CLI probes remain supported.
- Face-only output retains black startup and a last-safe-frame freeze on tracking loss.
- Local debugging/raw-face preview is excluded from virtual-camera pixels.

### Documentation

- Illustrated README, source-grounded GUI research/design rationale, control-placement
  decisions, architecture, algorithm/design chapters, and native-camera tutorial.
- Updated 245-page engineering handbook with 97 diagrams.
- Versioned release export tooling, checksums, source manifest and manual-publishing context.

## Install / launch

This is a **source release**, not a standalone `.exe` or installer. Extract the source ZIP,
open PowerShell in its project folder, then:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -e ".[tracking,virtual-camera,gui]"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

Verify/download models explicitly from **Models**. Opening Studio or listing devices does not
start camera capture. Choose the source and press **Start camera** when ready.

## Known limitations

- Live distant-face reliability and real Discord/Teams/Meet qualification remain unconfirmed.
- Body/hood tracking is experimental; face-only remains the selected default. Missing face/side
  markers is not proof of rear orientation.
- RGB hand foreground is approximate; arbitrary-object depth occlusion is unsupported.
- Private recordings contain unmasked footage. The existing fixed-FPS writer may compress
  playback duration when delivered capture FPS is lower.
- Camera names/indices can change with hardware changes; refresh/reselect before capture.
- Models, recordings, environments, credentials and private agent context are not bundled.
- The package uses optional dependencies with their own licensing terms; this release does not
  introduce a packaged Windows installer or custom camera driver.
