---
title: "Face Tracking"
description: "Implemented MediaPipe Face Landmarker pipeline, runtime behavior, contracts, and verified performance."
---

# 06 · Face tracking

> **Status: implemented and live-validated.**
>
> **TL;DR** — The tracker submits a downscaled copy of each latest camera frame to MediaPipe's
> asynchronous live-stream API. It retains one newest normalized result containing 478 landmarks,
> face bounds, independent eye openness, mouth openness, and a renderer-friendly head pose.

## Why tracking is a separate subsystem

MediaPipe is an inference engine, not the application's domain model. The adapter converts
MediaPipe results into frozen project contracts so future rendering can change independently
(`src/kardboard_vtuber/tracking/models.py:1`,
`src/kardboard_vtuber/tracking/mediapipe_tracker.py:1`).

```mermaid
flowchart LR
    Frame["Latest rotated/mirrored BGR frame"] --> Resize["Downscale to max 640 px"]
    Resize --> RGB["BGR to RGB"]
    RGB --> Async["MediaPipe detect_async"]
    Async --> Result["Landmarks + blendshapes + 4x4 matrix"]
    Result --> Normalize["FaceTrackingState"]
    Normalize --> Debug["Debug overlay"]
    Normalize --> Renderer["Future PS1 renderer"]
    style Frame fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Resize fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style RGB fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Async fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Result fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Normalize fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Debug fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Renderer fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
```

## Implemented components

| Component | Responsibility | Source |
|---|---|---|
| `FaceTrackingState` | Library-neutral face observation | `src/kardboard_vtuber/tracking/models.py:58` |
| `HeadPose` | Translation and Euler-angle view of 4x4 transform | `src/kardboard_vtuber/tracking/models.py:25` |
| `normalize_face()` | Landmark, bounds, blendshape, and pose conversion | `src/kardboard_vtuber/tracking/models.py:93` |
| `MediaPipeTrackerConfig` | Model path, input width, confidence thresholds | `src/kardboard_vtuber/tracking/mediapipe_tracker.py:23` |
| `MediaPipeFaceTracker` | Async task ownership and latest-result diagnostics | `src/kardboard_vtuber/tracking/mediapipe_tracker.py:44` |
| `FaceActionDetector` | Debounced blink, wink, eye, mouth, and face transitions | `src/kardboard_vtuber/tracking/events.py:73` |
| `draw_tracking_debug()` | Sparse landmarks, connected mesh inset, expressions, pose, and latest action | `src/kardboard_vtuber/tracking/mediapipe_tracker.py:191` |
| Model downloader | Official URL plus SHA-256 verification | `scripts/download_face_landmarker_model.py:1` |
| CLI integration | Flags, submission, diagnostics, and cleanup | `src/kardboard_vtuber/cli.py:1` |

## Runtime sequence

```mermaid
sequenceDiagram
    autonumber
    participant CLI
    participant Tracker
    participant MediaPipe
    participant Callback
    participant Preview
    CLI->>Tracker: submit(frame, captured_at_ns)
    Tracker->>Tracker: downscale and convert to RGB
    Tracker->>MediaPipe: detect_async(image, timestamp_ms)
    MediaPipe-->>Callback: result
    Callback->>Callback: normalize landmarks/blendshapes/matrix
    Callback->>Tracker: replace latest FaceTrackingState
    CLI->>Tracker: snapshot()
    Tracker-->>Preview: newest normalized state
    Preview->>Preview: draw landmarks, mesh, bounds, eye/mouth/pose values
    CLI->>CLI: emit debounced facial action transitions
```

## Verified performance

The live Nothing Phone stream remained near 30 FPS while tracking at 640-pixel input width:

| Signal | Observed |
|---|---|
| Camera receive rate | Approximately 29.5-31 FPS |
| Tracking result rate | Approximately 29-32 FPS |
| Pending or dropped count during probe | One current in-flight frame |
| Face detection | Continuous after startup |
| Tracking errors | None |
| Independent eye values | Present and changing |
| Mouth value | Present; near zero while mouth was closed |
| Spectacles | Face detected and a complete blink transition observed |
| Action transitions | Face detected, eyes closed/open, and blink emitted |

This was a twelve-second probe, not a long-duration soak test.

## Canonical regression recording

`scripts/record_guided_regression.py` records a clean 50-second camera video plus synchronized CSV
telemetry. Its preview guides neutral pose, yaw, pitch, roll, blink, both winks, mouth movement,
and combined motion. Preview instructions and debug graphics are never written into the saved MP4.

The CSV stores raw and filtered expressions/pose, filtered bounds, stage names, frame numbers, and
action events. Generated recordings belong in the private session artifact directory and must not
be committed.

## Run it

```powershell
.\.venv312\Scripts\Activate.ps1
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror `
  --track-face
```

## Deep dives

- [Normalized face state](normalized-face-state.md)
- [Live debugging and validation](live-debugging-and-validation.md)
- [Asynchronous live inference](../03-algorithms-and-data-structures/asynchronous-live-inference.md)
- [Blendshape normalization](../03-algorithms-and-data-structures/blendshape-normalization.md)
- [Transformation-matrix decomposition](../03-algorithms-and-data-structures/transformation-matrix-decomposition.md)
- [Facial action state machine](../03-algorithms-and-data-structures/facial-action-state-machine.md)

## References

- `pyproject.toml:16-23` — tracking dependency
- `scripts/download_face_landmarker_model.py:1` — verified model acquisition
- `src/kardboard_vtuber/tracking/models.py:1` — normalized contracts
- `src/kardboard_vtuber/tracking/mediapipe_tracker.py:1` — MediaPipe adapter
- `src/kardboard_vtuber/cli.py:1` — runtime integration
- `tests/test_tracking_models.py:1` — normalization tests

---

⬅️ [Camera ingestion](../05-camera-ingestion/README.md) · ➡️
[Quality and testing](../07-quality-and-testing/README.md)
