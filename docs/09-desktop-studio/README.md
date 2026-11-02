---
title: "Desktop Studio"
description: "Native operation, live eye calibration, privacy, and the rationale behind the desktop interface."
---

# Desktop Studio

> **TL;DR:** The desktop studio is an optional native PySide6 interface to the same camera
> pipeline used by the CLI. This chapter records the research before implementation, then
> explains the controls, thread/ownership boundaries, tutorial, and evidence.

![Native studio with independent eye calibration](../images/kardboardcode-studio-dark.png)

*Actual Qt widgets displaying the real textured renderer on a synthetic, camera-free stage.
The independent thresholds shown are illustrative demo settings, not recommended personal calibration.*

```mermaid
flowchart TD
    Controls["Native controls / tutorial"] --> Settings["Validated settings"]
    Settings --> Worker["Worker: existing CLI pipeline"]
    Worker --> Output["Clean virtual camera"]
    Worker --> Slot["One latest preview + telemetry"]
    Slot --> UI["Qt timer: display latest, never queue video"]
    UI --> Controls
    style Controls fill:#183a39,stroke:#72dcc0,color:#ecf6f5
    style Settings fill:#222b3a,stroke:#8da9dd,color:#ecf6f5
    style Worker fill:#222b3a,stroke:#8da9dd,color:#ecf6f5
    style Slot fill:#222b3a,stroke:#8da9dd,color:#ecf6f5
    style UI fill:#183a39,stroke:#72dcc0,color:#ecf6f5
    style Output fill:#183a39,stroke:#72dcc0,color:#ecf6f5
```

## Reading order

- [Research and design](research-and-design.md): five investigation lenses and toolkit decision.
- [Interface specification](interface-specification.md): every control and its placement rationale.
- [Runtime architecture](runtime-architecture.md): threading, ownership, errors, shutdown and calibration.
- [Tutorial](tutorial.md): first run through recording and troubleshooting.

Research findings describe the pre-GUI source; implementation/evidence sections are updated as
work completes. Neither a synthetic screenshot nor a passing test establishes live camera privacy
or calling-app compatibility.
