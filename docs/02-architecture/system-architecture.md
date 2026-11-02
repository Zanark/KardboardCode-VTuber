---
title: "System Architecture"
description: "The implemented end-to-end runtime and its independent timing, privacy, and rendering domains."
---

# System architecture

> **TL;DR** — Capture, tracking, rendering, composition, and presentation are separate stages with
> different performance characteristics. The system passes small contracts between stages rather
> than allowing one library to own the entire application.

## End-to-end runtime

```mermaid
flowchart TD
    subgraph Sources
      Local["Windows camera index"]
      Phone["Android IP Webcam"]
      Recorded["Private recorded file"]
    end
    subgraph Capture["Camera domain"]
      Open["OpenCV VideoCapture"]
      Worker["Capture worker"]
      Latest["Latest FramePacket"]
      Diag["CaptureSnapshot"]
    end
    subgraph Avatar["Tracking and avatar domain"]
      Resize["Tracking resize"]
      MP["MediaPipe Face Landmarker"]
      Normalize["FaceTrackingState"]
      Smooth["One Euro + springs"]
      PS1["Textured GPU or procedural renderer"]
      Compose["Full-resolution composer"]
    end
    subgraph Optional["Optional parallel inference"]
      Pose["Pose Landmarker"]
      Hands["Hand Landmarker"]
      Person["Selfie Segmenter"]
    end
    Clean["Clean composite"]
    Virtual["OBS virtual-camera component"]
    Debug["Local diagnostics / opt-in raw debug"]
    Output["CLI preview / OBS Window Capture"]
    Mailbox["Latest display packet"]
    Qt["Native Qt studio"]
    Local --> Open
    Phone --> Open
    Recorded --> Open
    Open --> Worker --> Latest
    Worker --> Diag
    Latest --> Resize --> MP --> Normalize --> Smooth --> PS1 --> Compose
    Latest --> Compose
    Latest --> Pose
    Latest --> Hands
    Latest --> Person
    Pose --> Compose
    Hands --> Compose
    Person --> Compose
    Compose --> Clean
    Clean --> Virtual
    Clean --> Debug
    Debug --> Output
    Debug --> Mailbox
    Mailbox --> Qt
```

## Component boundaries

### Configuration boundary

`CameraConfig` contains requested behavior. It validates impossible values early but never claims
that hardware accepted a request (`src/kardboard_vtuber/camera/models.py:90-121`).

### Capture boundary

`VideoCaptureLike` describes the OpenCV methods the worker needs
(`src/kardboard_vtuber/camera/stream.py:20-29`). This protocol is the seam used by tests.

### Concurrency boundary

`LatestFrameCamera` owns the thread, capture handle, condition variable, latest packet, counters, and
lifecycle (`src/kardboard_vtuber/camera/stream.py:39-73`).

### Presentation boundary

`cli.main` reads packets, submits optional asynchronous inference, resolves the head mode,
orders green-screen/head/hand composition and publishes clean output. The CLI then adds local
overlays; Studio instead transfers diagnostics in independent side-panel channels. It does not
implement capture or reconnection. Full-body diagnostics stay
separate rather than adding a filled body to the output.

The optional native studio calls this same pipeline from `SessionWorker.run`. `RuntimeBridge`
replaces HighGUI presentation with a one-slot owned preview and typed telemetry. Qt widgets and
painting stay on the main thread; native capture/tracking/rendering and the ModernGL lifecycle stay
off it. [Desktop runtime architecture](../09-desktop-studio/runtime-architecture.md) traces the
complete ownership, stop, error, and live-calibration contracts.

The separate VIDEO host uses PyAV and synchronous MediaPipe VIDEO tasks to process every source
frame without a live camera/latest-frame dropping. Studio and the Qt-free video CLI share this
offline engine, reusing the existing renderer and effects. Source size/timing and compatible
audio are preserved within format precision. See [video processing](../09-desktop-studio/video-processing.md).

### Live calibration boundary

`tracking.eyes.EyeSensitivity` owns effective anatomical left/right thresholds. `LiveTuning`
atomically carries them and processing brightness to the worker. `FaceActionDetector.set_thresholds`
and both renderers' `set_eye_sensitivity` use the same validated snapshot, without rebuilding the
renderer or discarding its safe-frame hold. Raw eye signals now drive both action and visual
closure decisions so smoothing cannot erase a blink. Geometry/pose remain filtered; telemetry
also records the actual rendered state so fallback expressions are not confused with raw scores.

## Why not one giant loop?

```mermaid
flowchart TB
    subgraph Bad["Single synchronous loop"]
      Read1["Read camera"] --> Track1["Track face"] --> Render1["Render"] --> Show1["Show"]
      Show1 --> Read1
    end
    subgraph Better["Separated timing domains"]
      Read2["Capture continuously"] --> Latest2["Overwrite latest"]
      Latest2 --> Track2["Track when ready"]
      Latest2 --> Show2["Compose current frame"]
    end
```

A synchronous loop makes camera ingestion wait for every expensive downstream stage. Separation
lets capture stay current even when inference or rendering slows down.

## Dependency direction

```mermaid
flowchart TD
    GUI["Qt widgets"] --> Bridge["Toolkit-neutral RuntimeBridge"]
    GUI --> Session["Session worker"]
    Session --> CLI["Shared CLI pipeline"]
    GUI --> Export["VideoExportWorker"]
    Export --> Offline["Qt-free video pipeline"]
    Offline --> PyAV["PyAV decode / encode / audio remux"]
    CLI --> Bridge
    CLI --> CameraAPI["camera package API"]
    CameraAPI --> Models["models.py"]
    CameraAPI --> Stream["stream.py"]
    Stream --> Models
    Stream --> OpenCV["OpenCV adapter"]
    Tests["tests"] --> CameraAPI
    Tests --> Fake["FakeCapture adapter"]
```

Higher-level code depends on project abstractions. OpenCV-specific constants are translated by
`CameraBackend.opencv_id` and `CameraRotation.opencv_code`
(`src/kardboard_vtuber/camera/models.py:15-48`).

## Stable extension seams

- Trackers consume transformed frame data, not `VideoCapture`.
- Renderers consume normalized project-owned tracking state, not raw MediaPipe objects.
- Compositors consume the current full frame plus project-owned masks or rendered overlays.
- OBS transport should consume composed output and remain independent of tracking.
- Native widgets consume owned display packets and send validated control snapshots, not mutable
  OpenCV/MediaPipe/ModernGL objects.

These seams are implemented in the camera, tracking, renderer, and CLI packages
(`src/kardboard_vtuber/tracking/models.py:15-100`,
`src/kardboard_vtuber/renderer/__init__.py:1`,
`src/kardboard_vtuber/tracking/green_screen.py:124-152`).

---

⬅️ [Architecture](README.md) · ➡️ [Data model](data-model.md)
