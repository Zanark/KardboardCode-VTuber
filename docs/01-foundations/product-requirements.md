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
| FR-05 | Track one face | Planned |
| FR-06 | Animate `K` and `C` independently | Planned |
| FR-07 | Animate mouth flaps | Planned |
| FR-08 | Render PS1-style cardboard geometry | Planned |
| FR-09 | Produce an OBS-capturable preview | Camera preview implemented |

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

## Sources

- CLI arguments: `src/kardboard_vtuber/cli.py:15-52`
- Capture behavior: `src/kardboard_vtuber/camera/stream.py:167-220`
- Credential redaction: `src/kardboard_vtuber/camera/models.py:80-87`
- Avatar semantics: `assets/PNGTuberV1/model-manifest.json:1`

---

⬅️ [Foundations](README.md) · ➡️ [System architecture](../02-architecture/system-architecture.md)
