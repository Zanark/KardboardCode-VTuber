# KardboardCode-VTuber

A lightweight Python VTuber tool that places a low-poly, PS1-style KardboardCode box over the user's head in a real camera feed.

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
- An opt-in low-resolution pose-driven body whose neck extends beneath the cardboard head.
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

The phone preview has been verified around 28-30 FPS. The isolated GPU renderer measures about
8.17 ms per 1080x1920 frame on the validated AMD Radeon 780M environment.

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

Add `--full-body` to render the pose-driven body beneath the cardboard head and open the
independent 33-point skeleton window. The complete body must be visible to the camera for reliable
limb tracking.

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
