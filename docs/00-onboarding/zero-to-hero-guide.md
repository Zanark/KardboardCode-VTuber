# Zero-to-hero learning path

> **TL;DR** — This path starts with Python and video basics, then introduces this repository's
> architecture, and finally shows how to run, test, and extend the application.

## Part I · Foundations you need

### Python objects versus JavaScript objects

This repository uses frozen, slotted dataclasses for small contracts:

```python
@dataclass(frozen=True, slots=True)
class FramePacket:
    sequence: int
    captured_at_ns: int
    frame: ndarray
```

The closest JavaScript mental model is an immutable object passed between components. Python adds
declared types and generated constructors, while `slots=True` prevents arbitrary attributes.

Read: `src/kardboard_vtuber/camera/models.py:124-138`.

### What OpenCV contributes

OpenCV owns:

- Opening a local device or network video URL.
- Decoding frames into NumPy arrays.
- Applying rotation, mirroring, text overlays, and preview display.

The project owns:

- Thread lifecycle.
- Stale-frame prevention.
- Reconnection policy.
- Diagnostics and security-conscious source display.

### What a frame is

The current frame is a NumPy array shaped `(height, width, channels)` in BGR order. Rotation swaps
width and height. A 1920x1080 landscape source therefore becomes a 1080x1920 portrait frame after a
90-degree rotation.

## Part II · Learn this codebase

```mermaid
flowchart LR
    CLI["cli.py<br/>parse intent"] --> Config["CameraConfig<br/>validated request"]
    Config --> Camera["LatestFrameCamera<br/>runtime owner"]
    Camera --> Packet["FramePacket<br/>latest image"]
    Camera --> Stats["CaptureSnapshot<br/>diagnostics"]
    Packet --> Preview["OpenCV preview"]
```

Read in this order:

1. `src/kardboard_vtuber/camera/models.py:15-157`
2. `src/kardboard_vtuber/camera/stream.py:39-288`
3. `src/kardboard_vtuber/cli.py:15-150`
4. `tests/test_camera_stream.py:13-98`

## Part III · Set up and run

```powershell
cd C:\devdesk\KardboardCode\KardboardCode-VTuber
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest
```

Run a local camera:

```powershell
python -m kardboard_vtuber --source 0 --backend auto --mirror
```

Run a portrait phone stream:

```powershell
python -m kardboard_vtuber `
  --source "http://USERNAME:PASSWORD@PHONE_IP:8080/video" `
  --backend auto `
  --rotate left `
  --mirror
```

Never commit the authenticated URL.

## Part IV · Make a safe change

```mermaid
flowchart TD
    Requirement --> Model["Change model/config"]
    Model --> Worker["Wire runtime behavior"]
    Worker --> CLI["Expose user control"]
    CLI --> Test["Add fake-capture test"]
    Test --> Docs["Update the matching chapter"]
    Docs --> Validate["Ruff + pytest + runtime probe"]
```

Example: rotation required coordinated changes to:

- `CameraRotation` in `models.py:33-48`
- `CameraConfig.rotation` in `models.py:90-106`
- frame transformation in `stream.py:192-197`
- `--rotate` parsing in `cli.py:36-42`
- behavior test in `tests/test_camera_stream.py:83-98`

## Graduation checklist

- [ ] Explain why frames are not processed with a FIFO queue.
- [ ] Explain requested versus negotiated camera properties.
- [ ] Trace one frame from OpenCV to the preview.
- [ ] Explain what the reported frame age excludes.
- [ ] Run Ruff and all tests.
- [ ] Add a behavior through model, runtime, CLI, test, and documentation layers.

---

⬅️ [Onboarding](README.md) · ➡️ [Foundations](../01-foundations/README.md)
