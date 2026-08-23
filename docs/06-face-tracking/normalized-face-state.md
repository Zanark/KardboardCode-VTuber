---
title: "Normalized Face State"
description: "The library-neutral tracking contract consumed by debugging and current renderers."
---

# Normalized face state

> **TL;DR** — `FaceTrackingState` is the anti-corruption layer between MediaPipe and the current
> renderer. It preserves only stable concepts the application owns.

## Contract shape

```mermaid
classDiagram
    class NormalizedLandmark {
      float x
      float y
      float z
    }
    class HeadPose {
      float translation_x
      float translation_y
      float translation_z
      float pitch_degrees
      float yaw_degrees
      float roll_degrees
    }
    class FaceTrackingState {
      int timestamp_ms
      bool detected
      tuple landmarks
      float center_x
      float center_y
      float face_width
      float face_height
      float left_eye_open
      float right_eye_open
      float mouth_open
      HeadPose head_pose
    }
    class TrackingSnapshot {
      FaceTrackingState state
      FaceTrackingState raw_state
      int submitted_frames
      int result_frames
      int detected_frames
      int dropped_or_pending_frames
      float measured_fps
      string last_error
    }
    FaceTrackingState --> NormalizedLandmark
    FaceTrackingState --> HeadPose
    TrackingSnapshot --> FaceTrackingState
```

Definitions live in `src/kardboard_vtuber/tracking/models.py:15-90`.

## Data derivation

```mermaid
flowchart LR
    Landmarks["478 normalized landmarks"] --> Bounds["min/max bounds"]
    Bounds --> Center["center_x, center_y"]
    Bounds --> Size["face_width, face_height"]
    Blend["52 blendshape categories"] --> Eyes["1 - eyeBlinkLeft/Right"]
    Blend --> Mouth["jawOpen"]
    Matrix["4x4 transform"] --> Pose["translation + pitch/yaw/roll"]
    Center --> State["FaceTrackingState"]
    Size --> State
    Eyes --> State
    Mouth --> State
    Pose --> State
    style Landmarks fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Blend fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Matrix fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style State fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
```

`normalize_face()` performs this conversion
(`src/kardboard_vtuber/tracking/models.py:93-135`).

## Invariants

- Eye and mouth controls are clamped to `[0, 1]`
  (`src/kardboard_vtuber/tracking/models.py:148-151`).
- Non-finite blendshape scores become zero.
- No-face observations use centered neutral defaults
  (`src/kardboard_vtuber/tracking/models.py:74-88`).
- All contracts are frozen and slotted.
- The result timestamp uses MediaPipe's millisecond timeline.

## Why retain landmarks?

The opt-in debug overlay uses landmarks as spatial evidence. Current renderers use normalized
bounds, center, expressions, and pose rather than consuming MediaPipe objects directly.

## Raw and filtered states

`TrackingSnapshot` retains the raw normalized observation and the filtered renderer/debug state:

```text
FaceTrackingState (raw normalized observation)
    -> One Euro filter
    -> FaceTrackingState (stable control targets)
    -> AvatarControlState (renderer-specific values)
```

Action detection consumes `raw_state`; visual geometry and current renderer controls consume
filtered `state`. This prevents quick blinks from being hidden by smoothing.

## References

- `src/kardboard_vtuber/tracking/models.py:15-151`
- `src/kardboard_vtuber/tracking/mediapipe_tracker.py:143-166`
- `src/kardboard_vtuber/tracking/mediapipe_tracker.py:177-232`
- `src/kardboard_vtuber/cli.py:1`
- `tests/test_tracking_models.py:1`

---

⬅️ [Face tracking](README.md) · ➡️
[Live debugging](live-debugging-and-validation.md)
