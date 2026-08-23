---
title: "Camera Runtime Flow"
description: "The capture worker loop from open through publication, recovery, and shutdown."
---

# Camera runtime flow

> **TL;DR** — The CLI constructs immutable configuration, starts the worker, waits for newer
> packets, renders diagnostics, and shuts down cleanly. Reconnection remains inside the camera
> class rather than leaking into the UI loop.

## Startup sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Camera
    participant Worker
    participant OpenCV
    User->>CLI: command-line arguments
    CLI->>CLI: parse CameraSource and enums
    CLI->>Camera: LatestFrameCamera(config)
    CLI->>Camera: start()
    Camera->>Worker: create daemon thread
    Worker->>OpenCV: VideoCapture(source, backend)
    Worker->>OpenCV: request buffer/width/height/FPS
    Worker->>Camera: publish RUNNING + negotiated values
    Camera-->>CLI: start returns
```

CLI construction: `src/kardboard_vtuber/cli.py:54-70`.

## Per-frame sequence

```mermaid
sequenceDiagram
    participant OpenCV
    participant Worker
    participant Slot
    participant CLI
    OpenCV-->>Worker: decoded BGR frame
    Worker->>Worker: rotate if configured
    Worker->>Worker: mirror if configured
    Worker->>Slot: publish sequence + monotonic timestamp
    CLI->>Slot: read(after_sequence)
    Slot-->>CLI: newest FramePacket
    CLI->>CLI: draw diagnostics
    CLI->>CLI: imshow()
```

Transformation order is rotation followed by mirroring
(`src/kardboard_vtuber/camera/stream.py:192-197`). Mirroring after rotation means “horizontal” is
relative to the final displayed orientation.

## Requested versus negotiated properties

`_apply_requests()` asks the backend for buffer size, width, height, and FPS
(`stream.py:261-268`). `_open()` then reads actual values back (`stream.py:246-248`).

```mermaid
flowchart LR
    Config["Requested 1920x1080 @ 30"] --> Driver["Backend/driver"]
    Driver --> Actual["Negotiated values"]
    Actual --> Snapshot["CaptureSnapshot"]
    Config -. not proof .-> Actual
```

## Shutdown sequence

The CLI exits on duration, `Q`, Escape, Ctrl+C, or terminal error. Its `finally` block always calls
`camera.stop()` and `cv2.destroyAllWindows()` (`src/kardboard_vtuber/cli.py:115-126`).

---

⬅️ [Camera chapter](README.md) · ➡️ [Android IP Webcam](android-ip-webcam.md)
