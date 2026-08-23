---
title: "Command Reference"
description: "Environment setup, model downloads, runtime modes, privacy flags, and quality checks."
---

# Command reference

```mermaid
flowchart LR
    Source["Camera or recording"] --> Base["Base preview"]
    Base --> Debug["--tracking-debug"]
    Base --> Avatar["--render-cardboard or --physics"]
    Avatar --> Body["--full-body"]
    Avatar --> Hands["--hand-occlusion"]
    Base --> Green["--green-screen"]
    style Source fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Base fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Debug fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Avatar fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Body fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Hands fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Green fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
```

## Environment

```powershell
cd C:\devdesk\KardboardCode\KardboardCode-VTuber
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Local camera

```powershell
python -m kardboard_vtuber --source 0 --backend auto --mirror
```

Camera frames receive a mild brightness lift of `12` before tracking and preview. Override it with
`--brightness 0..100`, for example `--brightness 20` in a darker room.

## Android IP Webcam

```powershell
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror
```

## Headless benchmark

```powershell
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror `
  --headless `
  --duration 30
```

## Recorded calibration video

Local video files are automatically paced at their recorded FPS and stop cleanly at EOF.
The guided recording is already upright and mirrored:

```powershell
python -m kardboard_vtuber `
  --source "C:\path\to\KardboardCode-tracking-calibration-guided-45s.mp4" `
  --input-already-mirrored `
  --render-cardboard `
  --cardboard-renderer textured-3d
```

Do not add `--rotate left` or `--mirror` for this recording. Use
`--cardboard-renderer procedural-2d` to compare the preserved original prototype.

## Record a new canonical regression video

```powershell
python scripts\record_guided_regression.py `
  --source "http://YOUR_USERNAME:YOUR_PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror `
  --brightness 12 `
  --preview-height 720 `
  --output-dir "C:\path\to\private-regression-output" `
  --name "KardboardCode-canonical-regression"
```

Follow the 12 on-screen stages. The clean MP4 and synchronized CSV receive the same timestamp.

## Optional raw-face debug panel

The standard preview is clean by default. Add `--tracking-debug` to show the synthetic face-mesh
inset, pose axes, action state, tracked pose values, FPS, resolution, and frame-age text. This does
not expose raw face pixels.

The raw face panel is disabled by default because it reveals the user's face. Enable it only for
local debugging:

```powershell
python -m kardboard_vtuber `
  --source "http://YOUR_USERNAME:YOUR_PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror `
  --render-cardboard `
  --debug-face-preview `
  --preview-height 900
```

`--preview-height` changes only the displayed window size. Capture, tracking, and rendering remain
at the source resolution and retain the full camera frame.

## Full-body avatar and skeleton

Download and verify the official MediaPipe Pose Landmarker Lite model:

```powershell
python scripts\download_pose_landmarker_model.py
```

Then enable the feature:

```powershell
python -m kardboard_vtuber `
  --source "******PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror `
  --full-body `
  --preview-height 900
```

`--full-body` automatically enables face tracking and cardboard rendering. It draws a
low-resolution pose-driven body before the cardboard head, allowing the synthetic neck to overlap
inside the box. A separate `KardboardCode Full Body Skeleton` window shows the 33 numbered pose
landmarks and their connections on black. The tracker supports one person and can only track body
parts visible in the camera frame.

## Enable flap hinge physics

```powershell
python -m kardboard_vtuber `
  --source "YOUR_CAMERA_URL" `
  --backend auto `
  --rotate left `
  --mirror `
  --physics `
  --preview-height 900
```

`--physics` automatically enables face tracking and the textured 3D cardboard renderer. Both
inward underside flaps and the broad front underside flap receive separate bounded damped-spring
hinges driven by sustained tracked head turns, tilt, and movement. The two external side tabs use
wider, highly yaw-sensitive hinges for obvious left-right secondary motion. The internal opaque
privacy volume remains static.

The textured model is moved slightly backward in perspective by default. Add
`--box-depth-offset 0` to restore the previous Z position. Positive offsets have no upper cap;
large values can make the projected box too small to preserve head coverage.

## Green-screen the camera background

Download and verify the official MediaPipe Selfie Segmenter model:

```powershell
python scripts\download_selfie_segmenter_model.py
```

Then add `--green-screen` to the normal camera command. Person pixels remain visible and all
background pixels become pure chroma green for OBS. The compositor fails closed to a fully green
frame before the first mask or whenever the latest mask becomes stale.

## Privacy-safe hand occlusion

Download the verified official MediaPipe model once:

```powershell
python scripts\download_hand_landmarker_model.py
```

Then add `--hand-occlusion` to the textured renderer command:

```powershell
python -m kardboard_vtuber `
  --source "http://YOUR_USERNAME:YOUR_PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror `
  --render-cardboard `
  --hand-occlusion
```

The hand tracker runs asynchronously at a 320-pixel input width and restores detected hand and
forearm pixels over the rendered avatar. This provides convincing foreground interaction when a
hand is in front, but a monocular RGB camera cannot prove depth; a hand physically behind the
avatar may also be treated as foreground.

This mode intentionally supports only the anatomical hand and forearm mask. Arbitrary held-object
occlusion is not supported by the RGB-only camera pipeline. Inferred monocular depth was tested and
removed because it could classify face pixels as foreground and violate fail-closed privacy.
Reliable general-object occlusion requires an aligned hardware/AR depth stream.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#2d333b", "primaryBorderColor": "#6d5dfc", "primaryTextColor": "#e6edf3", "lineColor": "#8b949e", "secondaryColor": "#161b22", "tertiaryColor": "#2d333b"}}}%%
stateDiagram-v2
    [*] --> CameraPreview
    CameraPreview --> Black: face renderer has no safe acquisition
    CameraPreview --> AvatarVisible: face renderer has valid state
    AvatarVisible --> FrozenSafeFrame: face tracking becomes stale
    CameraPreview --> FullyGreen: green screen lacks a fresh mask
    FullyGreen --> PersonOnGreen: fresh person mask arrives
```

## Quality checks

```powershell
python -m ruff check .
python -m pytest
git --no-pager diff --check
```

## CLI help

```powershell
python -m kardboard_vtuber --help
```

## Backend fallback order

1. `auto`
2. `ffmpeg` for network streams
3. `dshow` for local Windows cameras
4. `msmf` for local Windows cameras

Never commit a command containing real credentials.

`Ctrl+C` requests an orderly shutdown. The capture loop exits and closes the renderer, MediaPipe
trackers, camera stream, and OpenCV windows before the process returns.

---

⬅️ [Repository map](repository-map.md) · 🏠 [Book home](../README.md)
