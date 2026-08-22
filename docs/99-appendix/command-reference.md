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
