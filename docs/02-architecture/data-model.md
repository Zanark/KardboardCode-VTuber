---
title: "Domain and Runtime Data Model"
description: "Immutable configuration, frame, tracking, and diagnostics contracts."
---

# Domain and runtime data model

> **TL;DR** — The current model separates user intent, one captured frame, lifecycle state, and
> diagnostics. This prevents mutable runtime details from leaking into configuration or UI code.

## Relationship diagram

```mermaid
classDiagram
    class CameraBackend {
      AUTO
      DSHOW
      MSMF
      FFMPEG
      opencv_id
    }
    class CameraRotation {
      NONE
      LEFT
      RIGHT
      HALF
      opencv_code
    }
    class CaptureState {
      STOPPED
      STARTING
      RUNNING
      RECONNECTING
      FAILED
    }
    class CameraSource {
      int|string value
      parse()
      is_network_stream
      redacted()
    }
    class CameraConfig {
      CameraSource source
      CameraBackend backend
      CameraRotation rotation
      bool mirror
      int buffer_size
      int max_consecutive_failures
    }
    class FramePacket {
      int sequence
      int captured_at_ns
      ndarray frame
      width
      height
    }
    class CaptureSnapshot {
      CaptureState state
      string source
      CameraBackend backend
      int negotiated_width
      int negotiated_height
      float measured_fps
      counters
    }
    CameraConfig --> CameraSource
    CameraConfig --> CameraBackend
    CameraConfig --> CameraRotation
    CaptureSnapshot --> CaptureState
    CaptureSnapshot --> CameraBackend
```

## `CameraSource`

Defined at `src/kardboard_vtuber/camera/models.py:62-87`.

| Rule | Reason |
|---|---|
| Decimal strings become device indices | CLI input arrives as text |
| Other strings remain URLs/paths | OpenCV accepts string sources |
| Empty values fail immediately | Avoid meaningless reconnect loops |
| Credentials are redacted for display | Diagnostics must not leak secrets |

## `CameraConfig`

Defined at `src/kardboard_vtuber/camera/models.py:90-121`.

This is an immutable request, not observed truth. Width, height, FPS, and buffer size are offered to
the backend. The backend may ignore them. Observed values belong in `CaptureSnapshot`.

## `FramePacket`

Defined at `src/kardboard_vtuber/camera/models.py:124-138`.

| Field | Invariant |
|---|---|
| `sequence` | Strictly increases for every published frame |
| `captured_at_ns` | Uses a monotonic clock |
| `frame` | OpenCV BGR NumPy array |

Sequence numbers answer “is this newer than what I processed?” Timestamps answer “how old is this
inside the process?” They are deliberately separate.

## `CaptureSnapshot`

Defined at `src/kardboard_vtuber/camera/models.py:141-157`.

A snapshot is immutable and point-in-time. It contains:

- lifecycle state;
- redacted source and selected backend;
- negotiated width, height, and FPS;
- received, overwritten, failed-read, and reconnect counters;
- measured receive rate;
- last error.

```mermaid
flowchart LR
    Runtime["Mutable worker internals"] -->|"copy under lock"| Snapshot["Frozen CaptureSnapshot"]
    Snapshot --> CLI["CLI formats output"]
    Snapshot --> UI["Native studio telemetry"]
```

## Why frozen and slotted?

- `frozen=True` makes accidental mutation fail.
- `slots=True` prevents undeclared fields and reduces per-instance overhead.
- Explicit fields make the contracts easy to test, serialize later, and explain.

## Tracking models

The tracker introduces a library-neutral `FaceTrackingState` containing landmarks, face bounds,
independent eye openness, mouth openness, and `HeadPose`
(`src/kardboard_vtuber/tracking/models.py:58-90`).

```python
class FaceTrackingState:
    head_pose: HeadPose
    left_eye_open: float
    right_eye_open: float
    mouth_open: float
    timestamp_ms: int
```

This prevents MediaPipe-specific result objects from contaminating the renderer.

## Desktop control and display contracts

| Contract | Ownership / invariant |
|---|---|
| `EyeSensitivity` | Immutable effective anatomical left/right blink, open, wink and asymmetry thresholds shared by actions/renderers |
| `LiveTuning` | One validated tuple of eye sensitivity, internal brightness and debounce intervals; atomically replaced |
| `RuntimeTelemetry` | Raw/filtered face state, actual rendered eye state, effective detection, observed rates, dimensions and synthetic/raw flags |
| `PreviewPacket` | Separate owned program preview, full-resolution clean window frame, local mesh/raw-face/skeleton buffers and matching telemetry |
| `RuntimeBridge` | Thread event, short lock, one latest display slot and a bounded 500-entry log ring |
| Studio preset | Versioned allowlisted scalar settings; excludes camera source and raw-preview consent |
| `VideoExportOptions` | Local input, new output and explicit lossless/MP4 choice; never an existing destination |
| `VideoProgress` / `VideoExportResult` | Source-time progress, frame/dimension counts and completed output/audio metadata |

These are defined in `tracking\eyes.py`, `runtime.py`, and `gui\settings.py`. They separate a
small control plane from the full-size compositor/output. The widget thread receives no
mutable MediaPipe result or ModernGL object. [The desktop architecture
chapter](../09-desktop-studio/runtime-architecture.md) traces the actual readers and writers.
Offline file contracts live in `video.py` and the [video-processing chapter](../09-desktop-studio/video-processing.md).

---

⬅️ [System architecture](system-architecture.md) · ➡️ [Camera lifecycle](camera-lifecycle.md)
