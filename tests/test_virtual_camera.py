from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from kardboard_vtuber.virtual_camera import VirtualCameraConfig, VirtualCameraOutput


class FakeBackend:
    device = "OBS Virtual Camera"

    def __init__(self) -> None:
        self.frames: list[np.ndarray] = []
        self.options: dict[str, object] = {}
        self.close_count = 0
        self.fail_send = False

    def open(self, **options: object) -> FakeBackend:
        self.options = options
        return self

    def send(self, frame: np.ndarray) -> None:
        if self.fail_send:
            raise RuntimeError("sender disconnected")
        self.frames.append(frame.copy())

    def close(self) -> None:
        self.close_count += 1


@pytest.fixture
def backend(monkeypatch: pytest.MonkeyPatch) -> FakeBackend:
    backend = FakeBackend()
    monkeypatch.setitem(
        sys.modules,
        "pyvirtualcam",
        SimpleNamespace(Camera=backend.open, PixelFormat=SimpleNamespace(BGR="BGR")),
    )
    return backend


@pytest.mark.parametrize(
    "options",
    [
        {"width": 0},
        {"width": 1279},
        {"height": -2},
        {"height": 719},
        {"fps": 0},
        {"fps": 61},
        {"fps": float("nan")},
        {"fps": float("inf")},
    ],
)
def test_invalid_virtual_camera_format_is_rejected(options: dict[str, int | float]) -> None:
    with pytest.raises(ValueError, match="virtual-camera"):
        VirtualCameraConfig(**options)


def test_output_starts_black_and_uses_the_explicit_obs_bgr_backend(backend: FakeBackend) -> None:
    output = VirtualCameraOutput(VirtualCameraConfig(width=8, height=6))

    assert output.device == "OBS Virtual Camera"
    assert backend.options == {
        "width": 8, "height": 6, "fps": 30.0, "fmt": "BGR", "backend": "obs",
    }
    assert backend.frames[0].shape == (6, 8, 3)
    assert not backend.frames[0].any()
    output.close()
    output.close()
    assert backend.close_count == 1
    with pytest.raises(RuntimeError, match="closed"):
        output.repeat()


def test_repeat_owns_a_copy_unaffected_by_preview_overlays(backend: FakeBackend) -> None:
    output = VirtualCameraOutput(VirtualCameraConfig(width=8, height=6))
    frame = np.full((6, 8, 3), (20, 70, 200), dtype=np.uint8)
    output.send(frame)
    frame[:] = 255
    output.repeat()

    assert np.all(backend.frames[-1] == (20, 70, 200))
    np.testing.assert_array_equal(backend.frames[-1], backend.frames[-2])
    output.close()


def test_portrait_input_is_pillarboxed_without_cropping(backend: FakeBackend) -> None:
    output = VirtualCameraOutput(VirtualCameraConfig(width=8, height=6))
    frame = np.full((6, 2, 3), (255, 0, 0), dtype=np.uint8)
    output.send(frame)

    image = backend.frames[-1]
    assert not image[:, :3].any()
    assert not image[:, 5:].any()
    assert np.all(image[:, 3:5] == (255, 0, 0))
    assert np.all(frame == (255, 0, 0))
    output.close()


def test_source_resolution_changes_keep_the_output_format(backend: FakeBackend) -> None:
    output = VirtualCameraOutput(VirtualCameraConfig(width=8, height=6))
    output.send(np.full((12, 16, 3), 90, dtype=np.uint8))
    output.send(np.full((4, 8, 3), 110, dtype=np.uint8))

    assert all(frame.shape == (6, 8, 3) for frame in backend.frames)
    assert not backend.frames[-1][0].any()
    assert not backend.frames[-1][-1].any()
    assert np.all(backend.frames[-1][1:-1] == 110)
    output.close()


def test_missing_dependency_has_an_install_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pyvirtualcam", None)
    with pytest.raises(RuntimeError, match=r'pip install -e "\.\[tracking,virtual-camera\]"'):
        VirtualCameraOutput(VirtualCameraConfig())


def test_unavailable_driver_has_actionable_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(**options: object) -> None:
        raise RuntimeError("already running")

    monkeypatch.setitem(
        sys.modules,
        "pyvirtualcam",
        SimpleNamespace(Camera=unavailable, PixelFormat=SimpleNamespace(BGR="BGR")),
    )
    with pytest.raises(RuntimeError, match="Stop OBS's virtual-camera output"):
        VirtualCameraOutput(VirtualCameraConfig())


def test_send_failure_is_not_reported_as_success(backend: FakeBackend) -> None:
    output = VirtualCameraOutput(VirtualCameraConfig(width=8, height=6))
    backend.fail_send = True
    with pytest.raises(RuntimeError, match="frame delivery failed"):
        output.send(np.zeros((6, 8, 3), dtype=np.uint8))
    output.close()
    assert backend.close_count == 1


def test_startup_send_failure_releases_device(backend: FakeBackend) -> None:
    backend.fail_send = True
    with pytest.raises(RuntimeError, match="frame delivery failed"):
        VirtualCameraOutput(VirtualCameraConfig())
    assert backend.close_count == 1


@pytest.mark.parametrize(
    "frame",
    [np.zeros((6, 8)), np.zeros((6, 8, 4), dtype=np.uint8),
     np.zeros((0, 8, 3), dtype=np.uint8)],
)
def test_invalid_frame_is_rejected(backend: FakeBackend, frame: np.ndarray) -> None:
    output = VirtualCameraOutput(VirtualCameraConfig(width=8, height=6))
    with pytest.raises(ValueError, match="uint8 BGR"):
        output.send(frame)
    assert len(backend.frames) == 1
    output.close()
