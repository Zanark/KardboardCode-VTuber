---
title: "Product Requirements and Constraints"
description: "Implemented functional requirements, quality priorities, and deliberate exclusions."
---

# Product requirements and constraints

> **TL;DR** — The product is optimized for one creator, one recognizable cardboard character, low
> latency, and explainable source code. Generality is intentionally deferred.

## Functional requirements

| ID | Requirement | Current state |
|---|---|---|
| FR-01 | Accept local camera indices | Implemented |
| FR-02 | Accept authenticated MJPEG/RTSP URLs | Implemented |
| FR-03 | Rotate and mirror frames | Implemented |
| FR-04 | Reconnect after repeated failures | Implemented |
| FR-05 | Track one face | Implemented |
| FR-06 | Animate `K` and `C` independently | Implemented |
| FR-07 | Track mouth state without exposing the real mouth | Implemented; flap redesign deferred |
| FR-08 | Render PS1-style cardboard geometry | Implemented in ModernGL plus procedural fallback |
| FR-09 | Produce an OBS-capturable preview | Implemented through Window Capture |
| FR-10 | Add secondary flap motion | Implemented behind `--physics` |
| FR-11 | Preserve the body while replacing the room with chroma green | Implemented behind `--green-screen` |
| FR-12 | Hide tracking diagnostics by default | Implemented behind `--tracking-debug` |

## Non-functional requirements

```mermaid
quadrantChart
    title Product priorities
    x-axis Lower importance --> Higher importance
    y-axis Lower impact --> Higher impact
    quadrant-1 Protect strongly
    quadrant-2 Reconsider
    quadrant-3 Defer
    quadrant-4 Optimize
    Low latency: [0.92, 0.95]
    Source readability: [0.82, 0.82]
    Visual identity: [0.88, 0.88]
    Multi-model support: [0.18, 0.25]
    Photorealism: [0.12, 0.15]
    Complete frame retention: [0.10, 0.20]
```

- **Latency:** prefer dropping old frames over showing delayed motion.
- **Performance:** target stable 1080p30 first; 60 FPS is optional.
- **Explainability:** algorithms and tradeoffs must be teachable in an interview.
- **Security:** no credentials in source, docs, diagnostics, or commits.
- **Portability:** isolate OpenCV backend differences behind configuration.
- **Art direction:** intentional low fidelity, not accidental poor rendering.

## Verified camera acceptance result

The user confirmed the real preview with:

- 1080x1920 portrait output after left rotation.
- Approximately 27.9 FPS at the observed moment.
- Mirrored selfie orientation.
- No observed read failures or reconnects during the validation run.

The overlay's 0.4 ms frame age measured only post-decode in-process delay. It was not an
end-to-end phone latency measurement.

## Implemented privacy constraints

```mermaid
flowchart LR
    NoFace["No safe face yet"] --> Black["Black output"]
    Safe["Safe rendered frame"] --> Visible["Composed avatar"]
    Lost["Tracking lost"] --> Freeze["Freeze last safe frame"]
    NoMask["No fresh person mask"] --> Green["Fully green output"]
    style NoFace fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Safe fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Lost fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style NoMask fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Black fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Visible fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Freeze fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Green fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
```

The textured renderer blacks output before first acquisition and freezes the last safely composed
frame after face loss. Green-screen composition independently fails closed to a fully green frame
before a fresh person mask exists (`src/kardboard_vtuber/renderer/textured_3d.py:180-279`,
`src/kardboard_vtuber/tracking/green_screen.py:124-152`).

## Sources

- CLI arguments: `src/kardboard_vtuber/cli.py:32-213`
- Capture behavior: `src/kardboard_vtuber/camera/stream.py:167-220`
- Credential redaction: `src/kardboard_vtuber/camera/models.py:80-87`
- Avatar semantics: `assets/PNGTuberV1/model-manifest.json:1`
- Textured renderer: `src/kardboard_vtuber/renderer/textured_3d.py:111-1414`
- Runtime tests: `tests/test_cli.py:1`, `tests/test_textured_3d_renderer.py:1`

---

⬅️ [Foundations](README.md) · ➡️ [System architecture](../02-architecture/system-architecture.md)
