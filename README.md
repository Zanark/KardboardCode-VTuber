# KardboardCode-VTuber

A lightweight Python VTuber tool that places a low-poly, PS1-style KardboardCode box over the user's head in a real camera feed.

<p align="center">
  <img src="./assets/PNGTuberV1/reference/state-sheet.png" alt="KardboardCode PNGTuber V1 state sheet" width="760">
</p>
<p align="center"><em>
The preserved first-generation KardboardCode avatar: independent idle/talking and
open-eye/blinking states.
</em></p>

## Current milestone

The first implemented subsystem is low-latency camera ingestion:

- Local Windows cameras.
- Phone-hosted MJPEG/RTSP streams.
- Android USB-tethered streams without a Windows vendor camera client.
- Latest-frame-only buffering.
- Automatic stream reconnection.
- Negotiated-format and latency diagnostics.
- Rotation and selfie-style mirroring.

The phone preview has been verified at 1080x1920 portrait output and approximately 28-30 FPS.

Face tracking and the PS1 cardboard renderer are the next milestones.

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
--track-face
```

## Documentation

- [Engineering book](docs/README.md) - chaptered, diagram-first documentation covering onboarding, architecture, every current algorithm/data structure, design principles, camera operations, testing, roadmap, glossary, and source map.
- [PNGTuber V1 model](assets/PNGTuberV1/README.md) - preserved original avatar layers and behavior.

## Assets

- [`assets/PNGTuberV1`](assets/PNGTuberV1/README.md) - original PNGTuber Plus model, source layers, behavior specification, and reference renders.
