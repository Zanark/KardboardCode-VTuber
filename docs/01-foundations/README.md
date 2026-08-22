# 01 · Foundations

> **TL;DR** — KardboardCode-VTuber is not a generic avatar engine. It is a focused application that
> keeps a high-quality real camera feed and replaces only the user's head with one expressive,
> low-poly cardboard box.

## Product statement

The application will:

1. Read a local or Android-phone camera.
2. Track one face and head pose.
3. Map left/right eye state to the `K` and `C` markings.
4. Map mouth movement to cardboard front flaps.
5. Add restrained spring-driven secondary motion.
6. Render the box at low internal resolution for a PS1 aesthetic.
7. Composite it over the original high-resolution camera.
8. Present an OBS-capturable output.

<p align="center">
  <img src="../../assets/PNGTuberV1/reference/state-sheet.png" alt="KardboardCode PNGTuber V1 state sheet" width="760">
</p>
<p align="center"><em>
Figure 1 — The preserved source avatar and its independent talking/blinking state combinations.
See the <a href="./visual-identity-and-source-avatar.md">visual identity chapter</a> for the full
image-guided explanation.
</em></p>

```mermaid
mindmap
  root((KardboardCode VTuber))
    Real camera remains visible
    One fixed cardboard model
      K left eye
      C right eye
      Mouth flaps
      Side-flap physics
    PS1 visual style
      Low-poly
      Low-resolution texture
      Nearest-neighbor upscale
      Optional dithering and jitter
    Streaming
      Preview window
      OBS Window Capture
      Future Spout2
```

## Scope boundaries

| In scope | Out of scope for the prototype |
|---|---|
| One face | Multi-person tracking |
| One cardboard-head model | General model import |
| Real background and body | Full-body synthetic avatar |
| Python source-run workflow | Unity-first distribution |
| Window Capture for OBS | Custom OBS plugin |
| Relative head pose | Metric depth reconstruction |

## Why preserve two resolutions?

The camera image and the avatar have different jobs:

```mermaid
flowchart LR
    Frame["High-resolution phone frame"]
    Frame --> Downscale["Downscale copy<br/>about 640x360"]
    Downscale --> Tracking["Face tracking"]
    Frame --> Composite["Final composition"]
    Tracking --> Box["Render box<br/>320x180 or 426x240"]
    Box --> Nearest["Nearest-neighbor upscale"]
    Nearest --> Composite
```

Tracking needs stable landmarks, not 2 million pixels. The final stream benefits from the full
camera resolution. The box is intentionally coarse because visual imperfection is part of the art
direction.

## Current truth versus future design

**Implemented:** package, CLI, OpenCV capture, source parsing, authentication redaction, backend
selection, latest-frame buffering, lifecycle, reconnects, rotation, mirroring, diagnostics, tests,
and documentation.

**Planned:** MediaPipe adapter, normalized face state, filters, springs, box geometry, compositing,
calibration, OBS-specific output enhancements.

## Source anchors

- Project metadata and dependencies: `pyproject.toml:5-26`
- Preserved avatar behavior: `assets/PNGTuberV1/model-manifest.json:1`
- Working camera package: `src/kardboard_vtuber/camera/`
- CLI behavior: `src/kardboard_vtuber/cli.py:15-150`

## Related foundation chapters

- [Product requirements and constraints](product-requirements.md)
- [Visual identity and source avatar](visual-identity-and-source-avatar.md)

---

⬅️ [Book home](../README.md) · ➡️ [Architecture](../02-architecture/README.md)
