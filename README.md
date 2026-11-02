# KardboardCode-VTuber

A lightweight Python VTuber tool that places a low-poly, PS1-style KardboardCode box over the user's head in a real camera feed.

## Native desktop studio

The optional **PySide6 desktop GUI** exposes every camera CLI option, live independent left/right
eye calibration, virtual-camera output, green screen, hands, experimental tracking, private
recording, model setup, redacted logs, and a nine-part built-in tutorial. The CLI remains available.

<p align="center">
  <img src="./docs/images/kardboardcode-studio-dark.png" alt="KardboardCode Studio native GUI with live left/right blink sliders and a synthetic cardboard avatar preview" width="1200">
</p>
<p align="center"><em>
Actual desktop widgets running the real textured renderer on a labelled synthetic stage.
No live camera, raw face image, or virtual output was used for this screenshot.
</em></p>

From `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber`:

```powershell
.\.venv312\Scripts\python.exe -m pip install -e ".[dev,tracking,virtual-camera,gui]"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

Click **Try demo** to explore without a camera, then **Tutorial** for the complete walkthrough.
Opening the GUI does not start capture. **LIVE** sliders update the current session; other
settings unlock after **Stop**. Presets never retain camera sources or raw-preview consent.
The installed launcher is `.\.venv312\Scripts\kardboard-studio.exe`.

### Use this laptop's camera

Open **Camera → Input type → This computer's camera**, click **Refresh**, select the laptop
or USB camera by name, then click **Start camera**. Refresh reads Windows device metadata only:
it does not open a camera or capture frames. Each named choice uses its matching capture
backend/index. The same physical camera may appear under both Media Foundation and DirectShow.

Choose **Phone stream / video file / manual source** to keep using a phone URL or recording.
Manual numeric indices such as `0` remain supported. Refresh/reselect after device changes;
index `0` is not guaranteed to be the laptop camera on every machine.

![Native camera selection](docs/images/kardboardcode-studio-native-camera.png)

*Actual native-source controls with illustrative laptop/USB device names. No camera was opened;
Refresh retrieves the real names on the machine running the tool.*

<details>
<summary>Light theme and built-in tutorial</summary>

![Native studio light theme](docs/images/kardboardcode-studio-light.png)

*The same actual controls in the light theme, including both sun and moon icons; theme changes
affect the interface, not video pixels.*

![Built-in anatomical eye calibration tutorial](docs/images/kardboardcode-studio-tutorial.png)

*The in-app tutorial explains per-eye thresholds, relative winks, validation, and navigation to
the corresponding settings. It works before connecting a camera.*

</details>

Read the [studio tutorial](docs/09-desktop-studio/tutorial.md),
[research and design rationale](docs/09-desktop-studio/research-and-design.md),
[complete control inventory](docs/09-desktop-studio/interface-specification.md), and
[GUI/runtime architecture](docs/09-desktop-studio/runtime-architecture.md).
The numbered implementation workstreams and evidence live in [`TODO`](TODO/00_INDEX.todo).

<p align="center">
  <img src="./docs/images/kardboardcode-hero.png" alt="Current KardboardCode textured 3D avatar" width="1000">
</p>
<p align="center"><em>
Current face-free synthetic render of the default textured GPU avatar.
</em></p>

## Live avatar demo

<p align="center">
  <img src="./docs/images/kardboardcode-live-demo.gif" alt="Animated KardboardCode avatar demonstrating tracked head movement, expressions, and flap physics" width="1000">
</p>
<p align="center"><em>
Real motion telemetry from the private regression recording drives this entirely synthetic render.
The GIF contains no camera frames or human face pixels.
</em></p>

### Real-life body composite

<p align="center">
  <img src="./docs/images/kardboardcode-real-life-demo.gif" alt="Real-life black-hoodie demonstration with the user's face and hairline fully covered by the KardboardCode avatar" width="420">
</p>
<p align="center"><em>
User-approved camera example with the black hoodie and body visible.
The cardboard shell and opaque head-region backing cover the face and hairline in every frame.
</em></p>

### Green-screen body composite

<p align="center">
  <img src="./docs/images/kardboardcode-green-screen-demo.gif" alt="Green-screen black-hoodie demonstration with the user's face and hairline fully covered by the KardboardCode avatar" width="420">
</p>
<p align="center"><em>
The same user-approved performance processed through the runtime person-segmentation compositor.
The body remains visible while every background pixel becomes chroma green.
</em></p>

## Current milestone

The current working vertical slice includes:

- Local Windows cameras.
- Phone-hosted MJPEG/RTSP streams.
- Android USB-tethered streams without a Windows vendor camera client.
- Latest-frame-only buffering.
- Automatic stream reconnection.
- Negotiated-format and latency diagnostics.
- Rotation and selfie-style mirroring.
- MediaPipe face tracking, calibrated pose, and anatomical blink/wink controls.
- Optional MediaPipe 33-point full-body tracking with a separate skeleton diagnostic window.
- An opt-in separate 33-point line-skeleton diagnostic window.
- A default ModernGL textured 3D cardboard character with corrugated edges, hollow underside,
  front/side flaps, low-poly headphones, side shipping stickers and barcodes, and a top `FRAGILE`
  label. The paper decals use dirty beige stock, torn corners, stains, and coarse pixel lettering.
  The two left-side labels use separate irregular tear silhouettes rather than mirrored cuts.
- Optional underdamped hinge physics for three underside flaps and both external side tabs.
- Optional person segmentation that preserves the camera-visible body over pure chroma green.
- Clean output by default; face mesh, pose, action, FPS, and latency overlays require
  `--tracking-debug`.
- Fail-closed privacy: black before safe face acquisition, frozen last-safe output after face loss,
  and fully green output before a fresh segmentation mask.
- A privacy-safe procedural 2D fallback.
- Direct Windows virtual-camera output through the installed OBS camera component, without
  running OBS or capturing a preview window.
- An optional native desktop studio with complete CLI controls, live per-eye calibration,
  source-free presets, a synthetic demo, and built-in tutorial.

The phone preview has been verified around 28-30 FPS. The isolated GPU renderer measures about
8.17 ms per 1080x1920 frame on the validated AMD Radeon 780M environment.

## Use as a camera in Discord, Teams, or Meet

On Windows, install OBS Studio once to register **OBS Virtual Camera**, then install the optional
Python dependency:

```powershell
.\.venv312\Scripts\python.exe -m pip install -e ".[tracking,virtual-camera]"
```

Run the tool with your camera source. Set `KARDBOARD_CAMERA_URL` in the same terminal;
an assignment in another terminal does not populate this one:

```powershell
$env:KARDBOARD_CAMERA_URL = Read-Host "Paste your full camera stream URL"
.\.venv312\Scripts\python.exe -m kardboard_vtuber `
  --source $env:KARDBOARD_CAMERA_URL `
  --mirror `
  --physics `
  --tracking-width 1280 `
  --brightness 30 `
  --virtual-camera
```

Select **OBS Virtual Camera** in the calling application's camera settings. OBS does **not**
need to run: Python sends the composed frames directly to its installed camera component.
Do not start OBS's virtual-camera output or another sender at the same time; the OBS backend
has only one camera instance. This is an existing Windows camera device, not a new custom-named
KardboardCode device. App permissions or organizational policies can restrict virtual cameras.

`--virtual-camera` automatically enables face tracking and cardboard rendering. With face-only
tracking, output is black before the first face acquisition and freezes on the last safe frame
when face tracking is lost or its result becomes stale. Debug text, face-mesh panels, and even `--debug-face-preview` stay
local; they are never sent to the virtual camera. Processing-only brightness remains internal.
Video output defaults to **1280x720 at an advertised 30 FPS**; delivered motion depends on capture
and tracking speed. Input is fitted with black bars if necessary, not stretched or cropped.
Use `--virtual-camera-width`, `--virtual-camera-height` (positive even values), and
`--virtual-camera-fps` (1-60) to change the output format. These are separate from capture settings
and `--preview-height`.

Add `--headless` to send video without opening any preview windows. Use Ctrl+C to stop and
release the device. Select your microphone separately in the calling application; this output
carries video only. Window Capture in OBS remains available when you do not use this mode.

Backend details: [pyvirtualcam supported cameras](https://github.com/letmaik/pyvirtualcam#supported-virtual-cameras).

## Current avatar

<p align="center">
  <img src="./docs/images/kardboardcode-six-sides.png" alt="Six-sided turnaround of the current cardboard avatar" width="1000">
</p>
<p align="center"><em>
Front, rear, left, right, top, and underside views generated without camera imagery.
</em></p>

<p align="center">
  <img src="./docs/images/kardboardcode-expression-states.png" alt="K and C eye expression states" width="1000">
</p>

### More angles and scenarios

<p align="center">
  <img src="./docs/images/kardboardcode-angle-gallery.png" alt="Nine-angle gallery of the textured cardboard avatar" width="1000">
</p>
<p align="center"><em>
High, low, profile, rear-quarter, and rolled camera angles rendered from the runtime mesh.
</em></p>

<p align="center">
  <img src="./docs/images/kardboardcode-cinematic-poses.png" alt="Six cinematic pose scenarios for the cardboard avatar" width="1000">
</p>

<p align="center">
  <img src="./docs/images/kardboardcode-performance-states.png" alt="Pose and K C expression combinations" width="1000">
</p>

### Face-free debug views

<p align="center">
  <img src="./docs/images/kardboardcode-tracking-debug-window.png" alt="Synthetic tracking-debug preview with face mesh inset" width="1000">
</p>

<p align="center">
  <img src="./docs/images/kardboardcode-render-mesh-debug.png" alt="Wireframe mesh hinge and privacy-volume diagnostics" width="900">
</p>

<p align="center">
  <img src="./docs/images/kardboardcode-body-skeleton-debug-window.png" alt="Synthetic 33-point body skeleton debug window" width="420">
</p>

The first and third images use the real runtime debug drawing functions with synthetic landmarks.
The wireframe sheet is generated directly from the renderer's vertex buffer and color-codes the
five hinge groups and internal privacy volume. None contains camera imagery.

The complete visual breakdown—including decals, hinges, underside privacy geometry, materials,
lighting, and depth settings—is documented in the
[textured renderer chapter](docs/02-architecture/textured-3d-renderer.md).

## Quick start

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Face tracking currently uses a separate Python 3.12 environment:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
python -m pip install -e ".[dev,tracking]"
python scripts\download_face_landmarker_model.py
python scripts\download_pose_landmarker_model.py
python scripts\download_hand_landmarker_model.py
python scripts\download_selfie_segmenter_model.py
```

Preview the integrated laptop camera:

```powershell
python -m kardboard_vtuber --source 0 --backend auto --mirror
```

Preview the portrait-oriented Android IP Webcam stream over Wi-Fi or USB tethering:

```powershell
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left
```

Do not commit an authenticated stream URL. Camera diagnostics redact embedded credentials.

Press `Q` or `Escape` to exit.

Enable the live tracking overlay by adding:

```powershell
--tracking-debug
```

This opt-in flag shows the face mesh and pose inset plus action, pose, FPS, and latency text.
Without it, cardboard rendering remains visually clean. The tracker still logs debounced face,
eye, blink, wink, and mouth transitions. Use
`--action-hold-ms 100` to tune how long a candidate action must remain stable before it is logged.
One Euro smoothing is enabled by default; add `--no-motion-filter` to compare raw visual tracking.

If eye tracking blinks or winks too easily, lower the closed-eye thresholds and require a larger
difference between the two eyes:

```powershell
--blink-threshold 0.20 `
--wink-threshold 0.50 `
--eye-open-threshold 0.72 `
--wink-min-difference 0.25
```

Lower blink/wink values are less sensitive. A higher open-eye threshold and wink difference also
make accidental winks less likely. These settings affect both action detection and the rendered
K/C expressions.

Render the current PS1-style cardboard prototype by adding:

```powershell
--render-cardboard
```

This automatically enables face tracking and uses the textured 3D renderer. Add
`--cardboard-renderer procedural-2d` to use the original fallback.

Add `--physics` to automatically enable the textured cardboard renderer and give all three
underside flaps spring hinge motion. The two external side tabs are especially sensitive to
left-right head turns and swing independently around the box-side hinges.

The textured box defaults to a small `0.16` perspective Z offset away from the camera. Use
`--box-depth-offset 0` to restore its previous depth instantly, or provide any finite positive
value to move it farther away. Large values can make the box too small to preserve head coverage.

Add `--full-body` to open the independent 33-point line-skeleton window. The skeleton is
diagnostic-only and is not composited into the camera preview beneath the cardboard head. The
complete body must be visible to the camera for reliable limb tracking.

Add `--body-head-fallback` to enable cardboard rendering and keep the head attached to a
shoulder-derived anchor when the face turns away or face tracking is briefly lost. The option
automatically starts face and pose tracking without rendering the synthetic full body or opening
its skeleton window. It first learns several normal face-to-shoulder observations while the face is
visible, then uses neutral expressions during fallback. It will not guess a generic head size
before calibration and returns to the existing frozen fail-safe if both shoulders cannot be
tracked confidently. Fallback-only pose inference is capped at 256-pixel input and 8 FPS to avoid
starving camera capture and face tracking.

Start each session facing the camera normally for about one second so the fallback can collect its
initial calibration before you turn away. Until calibration completes, the preview keeps the lower
body visible, masks everything above the detected shoulders, and displays calibration progress
instead of showing an unexplained black frame.

For a hoodie carrying a green square on the wearer's anatomical left and a blue square on the
anatomical right, use `--hood-marker-tracking`. It automatically enables cardboard, face, and
low-rate pose tracking. Face landmarks plus body pose mean front-facing; a side square selects the
corresponding profile; body pose without face landmarks or either side square selects the rear.
Side markers change orientation and position while retaining the most recent face/body-derived
head size. Red and pink are not marker colours. Recent side-marker motion is held briefly through
occlusion, then the existing privacy-safe freeze resumes if body tracking is also lost.

For a camera-visible body over a chroma background, download the verified segmentation model once:

```powershell
python scripts\download_selfie_segmenter_model.py
```

Then add `--green-screen`. The detected person remains visible while all non-person pixels become
pure green `(0, 255, 0)` for OBS chroma keying. Before the first fresh segmentation mask, output is
entirely green rather than exposing the room.

A representative full command is:

```powershell
python -m kardboard_vtuber `
  --source "YOUR_CAMERA_URL" `
  --backend auto `
  --rotate left `
  --mirror `
  --physics `
  --green-screen `
  --preview-height 900
```

## Documentation

- [Engineering book](docs/README.md) - chaptered, diagram-first documentation covering onboarding, architecture, every current algorithm/data structure, design principles, camera operations, testing, roadmap, glossary, and source map.
- [PNGTuber V1 model](assets/PNGTuberV1/README.md) - preserved original avatar layers and behavior.

## Assets

- [`assets/PNGTuberV1`](assets/PNGTuberV1/README.md) - original PNGTuber Plus model, source layers, behavior specification, and reference renders.
