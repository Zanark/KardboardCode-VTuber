---
title: "Camera Ingestion"
description: "Implemented device and network capture, transformations, recovery, and diagnostics."
---

# 05 · Camera ingestion

```mermaid
flowchart LR
    Source["Device or URL"] --> Open["Open source"]
    Open --> Worker["Capture worker"]
    Worker --> Transform["Rotate and mirror"]
    Transform --> Latest["Publish latest frame"]
    style Source fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Open fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Worker fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Transform fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Latest fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
```

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

When `--source` resolves to a local video file, capture is paced at the file's negotiated FPS and
stops at EOF rather than reconnecting. Use `--input-already-mirrored` for recordings captured from
an already mirrored preview so anatomical eye mapping remains correct without flipping the pixels
a second time.

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
[Face tracking](../06-face-tracking/README.md)
