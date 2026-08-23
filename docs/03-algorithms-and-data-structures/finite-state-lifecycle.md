---
title: "Finite-State Lifecycle"
description: "Explicit runtime states and legal transitions for camera recovery."
---

# Finite-state lifecycle and reconnect algorithm

```mermaid
flowchart LR
    Start["Start"] --> Opening["Opening"]
    Opening --> Running["Running"]
    Running --> Reconnect["Reconnecting"]
    Reconnect --> Running
    Running --> Stop["Stopped"]
    style Start fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Opening fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Running fill:#1c2333,stroke:#6d5dfc,color:#e6edf3
    style Reconnect fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
    style Stop fill:#2d333b,stroke:#6d5dfc,color:#e6edf3
``` and reconnect algorithm

> **TL;DR** — The worker combines an explicit state machine with a consecutive-failure threshold.
> Short read glitches are retried cheaply; sustained failures release and reopen the source.

## States are data

`CaptureState` has five values (`src/kardboard_vtuber/camera/models.py:51-58`). This is more
expressive than `is_open: bool`, which cannot distinguish startup, retry, terminal failure, and
clean shutdown.

```mermaid
stateDiagram-v2
    STOPPED --> STARTING
    STARTING --> RUNNING
    STARTING --> RECONNECTING
    RUNNING --> RECONNECTING
    RECONNECTING --> RUNNING
    STARTING --> FAILED
    RUNNING --> FAILED
    RECONNECTING --> FAILED
    RUNNING --> STOPPED
    RECONNECTING --> STOPPED
```

## Consecutive-failure threshold

```text
on successful read:
    consecutive_failures = 0

on failed read:
    consecutive_failures += 1
    total_read_failures += 1
    if consecutive_failures >= threshold:
        release source
        state = RECONNECTING
        reconnects += 1
```

Implementation: `src/kardboard_vtuber/camera/stream.py:179-191`.

The distinction between consecutive and total failures matters:

- Consecutive failures drive recovery.
- Total failures explain long-run source quality.

## Reopen loop

When no open capture exists, `_open()` creates a new adapter, reapplies requested properties, and
reads negotiated properties (`stream.py:223-259`). Failure increments reconnects and waits the
configured delay before another attempt.

## Failure policy

| Failure | Policy |
|---|---|
| One bad frame | Retry after 5 ms |
| Repeated bad frames | Release and reconnect |
| Source cannot open | Remain reconnecting |
| Unexpected Python/OpenCV exception | Enter `FAILED` and expose typed message |
| User shutdown | Stop retrying immediately |

## Why no exponential backoff yet?

The current sources are local cameras or a nearby phone, not a remote internet service. A fixed
one-second retry is simple and responsive. Exponential backoff becomes useful if repeated network
failures create noise or battery load.

---

⬅️ [Condition synchronization](condition-variable-synchronization.md) · ➡️
[Monotonic timing](monotonic-timing-and-fps.md)
