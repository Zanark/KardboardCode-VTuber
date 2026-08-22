# Command reference

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
  --source "C:\Users\mishrad\.copilot\session-state\5f0403d8-ec0e-4548-b7cd-c9120aeb3ec7\files\KardboardCode-tracking-calibration-guided-45s.mp4" `
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
  --output-dir "C:\Users\mishrad\.copilot\session-state\5f0403d8-ec0e-4548-b7cd-c9120aeb3ec7\files" `
  --name "KardboardCode-canonical-regression"
```

Follow the 12 on-screen stages. The clean MP4 and synchronized CSV receive the same timestamp.

## Optional raw-face debug panel

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

---

⬅️ [Repository map](repository-map.md) · 🏠 [Book home](../README.md)
