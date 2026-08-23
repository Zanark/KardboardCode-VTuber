---
title: "KardboardCode VTuber Engineering Book"
description: "Architecture, algorithms, operations, privacy, and visual reference for the current VTuber."
---

# KardboardCode VTuber Engineering Book

> **TL;DR** — This is the engineering book for a lightweight Python VTuber that keeps the real
> camera image, tracks one face, and overlays a deliberately low-resolution PS1-style cardboard
> head. Camera ingestion, tracking, filtering, procedural fallback rendering, and textured GPU 3D
> rendering are implemented and verified.

This documentation is written to be read in sequence, used as an interview study guide, and reused
as the technical backbone for a future development video. It explains not only **what** the code
does, but also **why** each data structure, algorithm, boundary, and tradeoff exists.

<p align="center">
  <img src="./images/kardboardcode-hero.png" alt="Current KardboardCode textured 3D avatar" width="1000">
</p>
<p align="center"><em>
The current default GPU-rendered avatar, generated entirely from synthetic geometry.
</em></p>

```mermaid
flowchart LR
    NoFace["No safe face"] --> Black["Black"]
    Tracked["Tracked face"] --> Avatar["Textured avatar"]
    Lost["Tracking lost"] --> Freeze["Last safe frame"]
    NoMask["No fresh person mask"] --> Green["Fully green"]
    style NoFace fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Tracked fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Lost fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style NoMask fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Black fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Avatar fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Freeze fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Green fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
```

## Book status

| Part | Status | Evidence |
|---|---|---|
| Camera ingestion | Implemented and verified | `src/kardboard_vtuber/camera/`, covered by the full test suite |
| Android IP Webcam integration | Implemented and user-verified | 1080x1920 preview at about 28-30 FPS |
| Face tracking | Implemented and live-validated | MediaPipe near 30 result FPS plus debounced action logs |
| Textured 3D renderer | Implemented as default | ModernGL mesh, cubic shell, complete front, neck-safe underside, headphones, decals, K/C eyes |
| Flap physics | Implemented and opt-in | Five independent shader hinges driven by bounded damped springs |
| Full-body mode | Implemented and opt-in | 33-point pose tracker, synthetic body, and separate skeleton window |
| Green-screen mode | Implemented and opt-in | Person mask preserves the body and replaces the room with chroma green |
| Hand occlusion | Implemented and opt-in | Hand/forearm-only foreground restoration over the avatar |
| Procedural renderer | Implemented fallback | Fail-closed opaque shell retained for GPU troubleshooting |
| OBS integration | Operational through Window Capture | Clean preview output; chroma-key mode available with `--green-screen` |

## Current visual reference

<p align="center">
  <img src="./images/kardboardcode-six-sides.png" alt="Six-sided turnaround of the textured cardboard avatar" width="1000">
</p>

<p align="center">
  <img src="./images/kardboardcode-angle-gallery.png" alt="Nine-angle gallery of the current textured avatar" width="1000">
</p>

See [Textured GPU 3D renderer](02-architecture/textured-3d-renderer.md) for the detailed material,
geometry, shader, privacy, decal, and animation specification.

## Reading paths

| I want to… | Read this path |
|---|---|
| Understand the project in ten minutes | [Foundations](01-foundations/README.md) → [System architecture](02-architecture/system-architecture.md) |
| Run the working camera tool | [Camera ingestion](05-camera-ingestion/README.md) → [Android IP Webcam](05-camera-ingestion/android-ip-webcam.md) |
| Explain the design in an interview | [Principal engineer guide](00-onboarding/principal-engineer-guide.md) → [Algorithms](03-algorithms-and-data-structures/README.md) → [Design principles](04-design-principles/README.md) |
| Learn every data structure | [Domain and runtime data model](02-architecture/data-model.md) |
| Study every current algorithm | [Algorithms and data structures](03-algorithms-and-data-structures/README.md) |
| Understand tracking | [Face tracking](06-face-tracking/README.md) |
| Understand green-screen compositing | [Green-screen compositing](02-architecture/green-screen-compositing.md) |
| Inspect every current avatar surface | [Textured GPU 3D renderer](02-architecture/textured-3d-renderer.md) |
| Understand testing | [Quality and testing](07-quality-and-testing/README.md) |
| Understand what comes next | [Roadmap](08-roadmap/README.md) |
| Look up a term or file | [Glossary](99-appendix/glossary.md) → [Repository map](99-appendix/repository-map.md) |

## Chapters

| # | Chapter | Question answered |
|---:|---|---|
| 00 | [Onboarding](00-onboarding/README.md) | How should a newcomer or principal engineer approach this system? |
| 01 | [Foundations](01-foundations/README.md) | What are we building, what does the avatar look like, and under which constraints? |
| 02 | [Architecture](02-architecture/README.md) | How do capture, tracking, rendering, and OBS fit together? |
| 03 | [Algorithms and data structures](03-algorithms-and-data-structures/README.md) | Which algorithms preserve low latency and correctness? |
| 04 | [Design principles](04-design-principles/README.md) | Which engineering principles shaped the implementation? |
| 05 | [Camera ingestion](05-camera-ingestion/README.md) | How does the implemented subsystem work and how is it operated? |
| 06 | [Face tracking](06-face-tracking/README.md) | How are landmarks, expressions, and head pose produced? |
| 07 | [Quality and testing](07-quality-and-testing/README.md) | How do we verify behavior without depending only on hardware? |
| 08 | [Roadmap](08-roadmap/README.md) | Which production-hardening tasks remain after the working avatar milestone? |
| 99 | [Appendix](99-appendix/README.md) | Where are commands, terms, source files, and quick references? |

## The system in one picture

```mermaid
flowchart LR
    Phone["Android phone<br/>IP Webcam"] --> Network["Wi-Fi or<br/>USB tethering"]
    Laptop["Integrated camera"] --> Capture
    Network --> Capture["OpenCV capture<br/>implemented"]
    Capture --> Slot["Latest-frame slot<br/>implemented"]
    Slot --> Tracker["Face + optional pose/hand/person trackers<br/>implemented"]
    Slot --> Composer["Full-resolution composer<br/>implemented"]
    Tracker --> Filter["One Euro + springs<br/>implemented"]
    Filter --> Renderer["Textured GPU 3D box + flap physics<br/>implemented"]
    Renderer --> Composer
    Slot --> Segment["Person segmentation<br/>optional"]
    Segment --> Composer
    Composer --> Preview["Preview window"]
    Preview --> OBS["OBS Window Capture"]
```

## Documentation contract

Every chapter follows these rules:

1. Start with a TL;DR and state whether behavior is implemented or planned.
2. Explain the concept at beginner level before introducing implementation detail.
3. Ground implementation claims in real repository files and line numbers.
4. Use diagrams where structure, state, flow, or tradeoffs are easier to see than to describe.
5. Separate measured facts from targets and future design.
6. Never store camera credentials, stream passwords, or private authenticated URLs.

---

Start with [00 · Onboarding](00-onboarding/README.md) · Look up terms in the
[Glossary](99-appendix/glossary.md)
