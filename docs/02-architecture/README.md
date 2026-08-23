---
title: "Architecture"
description: "Implemented capture, tracking, rendering, segmentation, composition, and presentation boundaries."
---

# 02 · Architecture

> **TL;DR** — The application is a staged real-time pipeline. Capture is already isolated behind a
> narrow API. Tracking, segmentation, rendering, and composition consume immutable latest-state
> snapshots without changing capture semantics.

## Chapter map

- [System architecture](system-architecture.md) — current components, boundaries, and frame flow
- [Domain and runtime data model](data-model.md) — every current structure and invariant
- [Camera lifecycle](camera-lifecycle.md) — startup, running, failure, reconnect, and shutdown
- [Textured GPU 3D renderer](textured-3d-renderer.md) — default mesh, materials, lighting, pose, and compositing
- [Green-screen compositing](green-screen-compositing.md) — async person masks and fail-closed chroma output
- [Procedural PS1 renderer](ps1-cardboard-renderer.md) — privacy-safe 2D fallback and original prototype

```mermaid
flowchart TD
    Architecture --> System["System architecture"]
    Architecture --> Model["Data model"]
    Architecture --> Lifecycle["Camera lifecycle"]
    Architecture --> Renderer["Textured GPU 3D renderer"]
    Architecture --> Green["Green-screen compositor"]
    Architecture --> Fallback["Procedural 2D fallback"]
    System --> Future["Tracking + rendering boundaries"]
    Model --> Contracts["Typed contracts"]
    Lifecycle --> Runtime["Concurrent runtime behavior"]
    Renderer --> Composite["Low-resolution overlay composition"]
    Green --> Composite
    Fallback --> Composite
```

## Architectural style

The code currently combines:

- **Pipeline architecture** for frame flow.
- **Ports and adapters** at the video-capture boundary.
- **Producer/consumer concurrency** with a single latest-value register.
- **Finite-state lifecycle management** for recovery and diagnostics.
- **Functional data contracts** through frozen dataclasses.
- **Fail-closed privacy boundaries** for face loss and stale segmentation masks.

```mermaid
flowchart LR
    Capture["Capture thread"] --> Latest["Latest FramePacket"]
    Latest --> Face["Face state"]
    Latest --> Optional["Pose, hand, person masks"]
    Face --> Render["Avatar render"]
    Optional --> Compose["Ordered composition"]
    Render --> Compose
    Compose --> Preview["Preview and OBS"]
    style Capture fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Latest fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Face fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Optional fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Render fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Compose fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Preview fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
```

## Sources

- `src/kardboard_vtuber/camera/models.py:15-157`
- `src/kardboard_vtuber/camera/stream.py:20-288`
- `src/kardboard_vtuber/cli.py:215-414`
- `src/kardboard_vtuber/renderer/textured_3d.py:140-327`
- `src/kardboard_vtuber/tracking/green_screen.py:16-152`

---

⬅️ [Foundations](../01-foundations/README.md) · ➡️
[Algorithms and data structures](../03-algorithms-and-data-structures/README.md)
