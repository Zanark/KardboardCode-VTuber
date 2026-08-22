# 05 · Camera ingestion

> **Status: implemented and verified.**
>
> **TL;DR** — The camera subsystem accepts local device indices and OpenCV-supported stream URLs,
> captures on a background thread, keeps only the latest frame, applies orientation transforms,
> reconnects after sustained failures, and reports negotiated and measured behavior.

## Chapter map

- [Runtime flow](runtime-flow.md) — one frame from source to preview
- [Android IP Webcam](android-ip-webcam.md) — the verified phone setup
- [Diagnostics and performance](diagnostics-and-performance.md) — metrics and their interpretation

## Quick start

```powershell
cd C:\devdesk\KardboardCode\KardboardCode-VTuber
.\.venv\Scripts\Activate.ps1
```

Local camera:

```powershell
python -m kardboard_vtuber --source 0 --backend auto --mirror
```

Phone camera:

```powershell
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror
```

Press `Q` or Escape to stop.

## Verified result

```mermaid
flowchart LR
    Phone["Nothing Phone (3a)<br/>IP Webcam"] --> WiFi["Local Wi-Fi"]
    WiFi --> URL["Authenticated /video MJPEG"]
    URL --> Auto["OpenCV auto backend"]
    Auto --> Rotate["90° left"]
    Rotate --> Mirror["Horizontal mirror"]
    Mirror --> Preview["1080x1920 preview<br/>about 27.9 FPS observed"]
```

The displayed 0.4 ms frame age covered only post-decode time inside the Python application.

## Supported backends

| Value | OpenCV backend | Intended use |
|---|---|---|
| `auto` | `CAP_ANY` | Default; best verified local and phone result |
| `dshow` | `CAP_DSHOW` | Windows DirectShow fallback |
| `msmf` | `CAP_MSMF` | Windows Media Foundation fallback |
| `ffmpeg` | `CAP_FFMPEG` | Explicit network-stream fallback |

Mappings: `src/kardboard_vtuber/camera/models.py:15-30`.

---

⬅️ [Design principles](../04-design-principles/README.md) · ➡️
[Quality and testing](../06-quality-and-testing/README.md)
