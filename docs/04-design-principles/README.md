---
title: "Design Principles"
description: "Architectural values governing latency, boundaries, state, and privacy."
---

# 04 · Design principles

```mermaid
flowchart LR
    Principles["Design principles"] --> Fresh["Freshness"]
    Principles --> Boundaries["Dependency boundaries"]
    Principles --> State["Immutable observations"]
    Principles --> Privacy["Fail-closed privacy"]
    style Principles fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Fresh fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Boundaries fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style State fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Privacy fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
```

> **TL;DR** — The implementation is governed by four deliberate principles: freshness over
> completeness, dependency inversion at hardware boundaries, immutable observation of mutable
> runtime state, and explicit security boundaries around camera sources.

## Principle catalogue

| Principle | Chapter | Concrete manifestation |
|---|---|---|
| Latency over completeness | [Latency over completeness](latency-over-completeness.md) | Single latest-frame slot |
| Dependency inversion | [Dependency inversion](dependency-inversion.md) | `VideoCaptureLike` + injected factory |
| Immutable observations | [Immutable snapshots](immutable-snapshots.md) | Frozen `CaptureSnapshot` |
| Security by boundary | [Security and secret boundaries](security-and-secret-boundaries.md) | URL redaction and ignored local config |

```mermaid
flowchart TD
    Requirement["Interactive avatar"] --> Fresh["Freshness over completeness"]
    Testability["Hardware-independent tests"] --> DI["Dependency inversion"]
    Concurrency["Concurrent mutable worker"] --> Snapshot["Immutable snapshots"]
    Auth["Authenticated camera URL"] --> Security["Secret boundary"]
```

These are not slogans added after implementation. Each principle maps to code and tests.

---

⬅️ [Algorithms](../03-algorithms-and-data-structures/README.md) · ➡️
[Camera ingestion](../05-camera-ingestion/README.md)
