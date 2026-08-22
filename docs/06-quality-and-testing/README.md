# 06 · Quality and testing

> **Status: camera tests implemented and passing.**
>
> **TL;DR** — The project separates deterministic unit tests from hardware integration checks.
> `FakeCapture` proves buffering and transformation behavior without a camera; real probes verify
> backend and device behavior that mocks cannot establish.

## Test pyramid

```mermaid
flowchart TB
    Manual["Manual visual validation<br/>orientation, mirror, perceived latency"]
    Integration["Hardware/network probes<br/>camera opens, negotiated format, measured FPS"]
    Unit["Fast unit tests<br/>parsing, validation, redaction, buffering, rotation"]
    Unit --> Integration --> Manual
```

## Unit-test inventory

| Test | Purpose | Source |
|---|---|---|
| Device-index parsing | `"2"` becomes integer `2` | `tests/test_camera_models.py:6-10` |
| URL preservation | Stream URL remains a string | `tests/test_camera_models.py:13-17` |
| Credential redaction | User info is hidden | `tests/test_camera_models.py:20-24` |
| Empty-source rejection | Invalid input fails early | `tests/test_camera_models.py:27-30` |
| Dimension validation | Non-positive request rejected | `tests/test_camera_models.py:32-34` |
| Newer sequences | Consumer receives increasing sequence | `tests/test_camera_stream.py:47-64` |
| Frame overwrite | Producer can supersede unread frame | `tests/test_camera_stream.py:67-80` |
| Left rotation | Width/height swap correctly | `tests/test_camera_stream.py:83-98` |

Pytest reports nine tests because the empty-source test is parameterized with two inputs.

## `FakeCapture`

`FakeCapture` at `tests/test_camera_stream.py:13-44` implements the same structural protocol used by
production:

```mermaid
flowchart LR
    Factory["Injected factory"] --> Fake["FakeCapture"]
    Fake --> Frames["Synthetic 4x6 arrays"]
    Fake --> Props["Synthetic camera properties"]
    Fake --> Release["Observable release flag"]
    Camera["LatestFrameCamera"] --> Factory
```

The fake sleeps briefly per read so the real worker thread can publish multiple frames.

## What unit tests cannot prove

- Whether a Windows driver honors requested resolution.
- Whether FFmpeg can decode a particular phone stream.
- True network latency.
- Visual orientation and mirror preference.
- OBS capture behavior.

Those require integration or manual validation.

## Verified commands

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m kardboard_vtuber --help
```

Current verified result: Ruff passes and all nine tests pass.

## Definition of done for a new behavior

1. Model/config contract updated.
2. Runtime behavior wired.
3. CLI or API surface updated where applicable.
4. Deterministic test added.
5. Matching book chapter updated.
6. Ruff and pytest pass.
7. Hardware behavior checked if the change touches a real backend.

---

⬅️ [Camera ingestion](../05-camera-ingestion/README.md) · ➡️
[Roadmap](../07-roadmap/README.md)
