from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from kardboard_vtuber import cli
from kardboard_vtuber.camera.models import CaptureState, FramePacket
from kardboard_vtuber.renderer import PS1CardboardRenderer
from kardboard_vtuber.tracking import hand_occlusion
from kardboard_vtuber.tracking.models import FaceTrackingState
from tests.test_ps1_cardboard_renderer import state
from tests.test_virtual_camera import FakeBackend


class FakeCapture:
    def __init__(self, timestamps_ms: list[int]) -> None:
        self.packets = [
            FramePacket(index, timestamp * 1_000_000,
                        np.full((360, 640, 3), 70 + index * 30, dtype=np.uint8))
            for index, timestamp in enumerate(timestamps_ms)
        ]
        self.remaining = iter(self.packets)
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def read(self, **options: object) -> FramePacket | None:
        return next(self.remaining, None)

    def snapshot(self) -> SimpleNamespace:
        return SimpleNamespace(state=CaptureState.STOPPED, last_error=None, measured_fps=30.0)

    def stop(self) -> None:
        self.stopped = True


class FakeTracker:
    def __init__(self, states: list[FaceTrackingState]) -> None:
        self.states = iter(states)
        self.current = FaceTrackingState.no_face()
        self.inputs: list[np.ndarray] = []
        self.closed = False

    def submit(self, frame: np.ndarray, captured_at_ns: int) -> None:
        self.inputs.append(frame.copy())
        self.current = next(self.states)

    def snapshot(self) -> SimpleNamespace:
        return SimpleNamespace(state=self.current, raw_state=self.current)

    def close(self) -> None:
        self.closed = True


def setup_runtime(
    monkeypatch: pytest.MonkeyPatch, states: list[FaceTrackingState], timestamps: list[int],
) -> tuple[FakeCapture, FakeTracker, FakeBackend, list[np.ndarray]]:
    capture = FakeCapture(timestamps)
    tracker = FakeTracker(states)
    backend = FakeBackend()
    previews: list[np.ndarray] = []
    monkeypatch.setattr(cli, "LatestFrameCamera", lambda config: capture)
    monkeypatch.setattr(cli, "_create_tracker", lambda args: tracker)
    monkeypatch.setattr(cli, "_create_renderer", lambda args: PS1CardboardRenderer())
    monkeypatch.setattr(cli, "_create_action_detector", lambda args: None)
    monkeypatch.setattr(cli, "_print_snapshot", lambda camera: None)
    monkeypatch.setattr(cli, "_print_tracking_snapshot", lambda face_tracker: None)
    monkeypatch.setattr(cli, "VirtualCameraOutput", lambda config: backend)
    monkeypatch.setattr(backend, "repeat", lambda: None, raising=False)
    monkeypatch.setattr(cli.cv2, "imshow", lambda name, frame: previews.append(frame.copy()))
    monkeypatch.setattr(cli.cv2, "waitKey", lambda delay: -1)
    monkeypatch.setattr(cli.cv2, "destroyAllWindows", lambda: None)
    return capture, tracker, backend, previews


def test_virtual_camera_is_opt_in() -> None:
    args = cli.build_parser().parse_args([])
    assert not args.virtual_camera
    assert (args.virtual_camera_width, args.virtual_camera_height) == (1280, 720)
    assert args.virtual_camera_fps == 30.0


@pytest.mark.parametrize("headless", [False, True])
@pytest.mark.parametrize("stale_result", [False, True])
def test_output_is_composed_and_freezes_without_exporting_preview_debug(
    monkeypatch: pytest.MonkeyPatch, headless: bool, stale_result: bool,
) -> None:
    face_states = [state(1000, detected=False), state(1033),
                   state(1033) if stale_result else state(1700, detected=False)]
    capture, tracker, backend, previews = setup_runtime(
        monkeypatch, face_states, [1000, 1033, 1700],
    )
    args = [
        "--virtual-camera", "--tracking-debug", "--debug-face-preview",
        "--brightness", "30", "--preview-height", "240",
    ]
    if headless:
        args.append("--headless")

    assert cli.main(args) == 0

    assert capture.started and capture.stopped and tracker.closed
    assert backend.close_count == 1
    assert len(backend.frames) == 3
    assert not backend.frames[0].any()
    assert np.all(backend.frames[1][0, 0] == 100)
    assert not np.array_equal(backend.frames[1], capture.packets[1].frame)
    np.testing.assert_array_equal(backend.frames[1], backend.frames[2])
    assert np.all(tracker.inputs[1] == 130)
    assert np.all(capture.packets[1].frame == 100)
    if headless:
        assert previews == []
    else:
        assert len(previews) == 3
        assert previews[0].any()
        assert previews[0].shape == (240, 427, 3)
    assert backend.frames[1].shape == (360, 640, 3)


def test_virtual_camera_start_failure_closes_tracking_without_starting_capture(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    capture, tracker, _, _ = setup_runtime(monkeypatch, [], [])

    def fail(config: object) -> None:
        raise RuntimeError("Virtual camera unavailable")

    monkeypatch.setattr(cli, "VirtualCameraOutput", fail)
    assert cli.main(["--virtual-camera", "--headless"]) == 1
    assert "Virtual camera unavailable" in capsys.readouterr().err
    assert tracker.closed and capture.stopped and not capture.started


def test_tracking_loss_does_not_restore_live_hand_pixels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, backend, _ = setup_runtime(
        monkeypatch, [state(1000, detected=False), state(1033), state(1066, detected=False)],
        [1000, 1033, 1066],
    )
    hand_tracker = SimpleNamespace(
        submit=lambda frame, timestamp: None, snapshot=lambda: None, close=lambda: None,
    )
    monkeypatch.setattr(cli, "_create_hand_occluder", lambda args: hand_tracker)
    composited: list[np.ndarray] = []

    def composite(frame: np.ndarray, source: np.ndarray, hands: object) -> None:
        composited.append(source.copy())
        frame[0, 0] = (0, 255, 0)

    monkeypatch.setattr(hand_occlusion, "composite_hand_foreground", composite)
    assert cli.main(["--virtual-camera", "--hand-occlusion", "--headless"]) == 0

    assert len(composited) == 1
    assert not backend.frames[0].any()
    assert np.all(backend.frames[1][0, 0] == (0, 255, 0))
    assert np.all(backend.frames[2][0, 0] == 100)


def test_existing_headless_capture_does_not_render_or_send_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture, tracker, backend, previews = setup_runtime(
        monkeypatch, [state(1000)], [1000],
    )
    assert cli.main(["--track-face", "--headless"]) == 0
    assert capture.stopped and tracker.closed
    assert backend.frames == [] and backend.close_count == 0
    assert previews == []


def test_virtual_camera_send_failure_closes_capture(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    capture, tracker, backend, _ = setup_runtime(monkeypatch, [state(1000)], [1000])
    backend.fail_send = True

    assert cli.main(["--virtual-camera", "--headless"]) == 1
    assert "sender disconnected" in capsys.readouterr().err
    assert tracker.closed and capture.stopped and backend.close_count == 1


@pytest.mark.parametrize(
    ("flag", "value"),
    [("--virtual-camera-width", "0"), ("--virtual-camera-height", "719"),
     ("--virtual-camera-fps", "nan")],
)
def test_invalid_output_options_fail_before_camera_start(
    flag: str, value: str, capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["--virtual-camera", flag, value]) == 2
    assert "virtual-camera" in capsys.readouterr().err
