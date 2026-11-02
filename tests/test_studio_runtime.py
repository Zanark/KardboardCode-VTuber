from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from kardboard_vtuber import cli
from kardboard_vtuber.renderer import PS1CardboardRenderer
from kardboard_vtuber.runtime import LiveTuning, RuntimeBridge, RuntimeTelemetry, redact
from kardboard_vtuber.tracking.eyes import EyeSensitivity
from tests.test_ps1_cardboard_renderer import state
from tests.test_virtual_camera_cli import FakeCapture, FakeTracker


def test_mailbox_owns_only_latest_pixels_and_reports_log_overflow() -> None:
    bridge = RuntimeBridge()
    frame = np.ones((10, 10, 3), dtype=np.uint8)
    bridge.publish(frame, RuntimeTelemetry())
    frame[:] = 90
    packet, _ = bridge.take()
    assert packet is not None and packet.frame is not None
    assert np.all(packet.frame == 1)
    for value in range(600):
        bridge.publish(np.full_like(frame, value % 255), RuntimeTelemetry())
        bridge.log(str(value))
    packet, logs = bridge.take()
    assert packet is not None and packet.frame is not None
    assert np.all(packet.frame == 599 % 255)
    assert len(logs) == 501 and "100 older log lines" in logs[0]
    assert bridge.take() == (None, ())


@pytest.mark.parametrize("value", [-0.1, float("nan"), 1.1])
def test_invalid_per_eye_thresholds_are_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        EyeSensitivity(left_closed=value)


def test_gui_runtime_reuses_pipeline_and_keeps_raw_debug_out_of_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = FakeCapture([1000, 1033, 1700])
    tracker = FakeTracker([state(1000, detected=False), state(1033), state(1033)])
    original_snapshot = tracker.snapshot
    monkeypatch.setattr(
        tracker,
        "snapshot",
        lambda: type(
            "Snapshot",
            (),
            {
                "state": original_snapshot().state,
                "raw_state": tracker.current,
                "measured_fps": 30,
            },
        )(),
    )
    bridge = RuntimeBridge(LiveTuning(brightness=30))
    monkeypatch.setattr(cli, "LatestFrameCamera", lambda config: capture)
    monkeypatch.setattr(cli, "_create_tracker", lambda args: tracker)
    monkeypatch.setattr(cli, "_create_renderer", lambda args, **kw: PS1CardboardRenderer())
    monkeypatch.setattr(cli, "_create_action_detector", lambda args: None)
    monkeypatch.setattr(cli, "_print_snapshot", lambda camera, **kw: None)
    monkeypatch.setattr(cli, "_print_tracking_snapshot", lambda tracker, **kw: None)
    exported: list[np.ndarray] = []
    output = type(
        "Output",
        (),
        {
            "device": "Fake virtual camera",
            "send": lambda self, frame: exported.append(frame.copy()),
            "repeat": lambda self: None,
            "close": lambda self: None,
        },
    )()
    monkeypatch.setattr(cli, "VirtualCameraOutput", lambda config: output)
    monkeypatch.setattr(
        cli.signal, "signal", lambda *args: pytest.fail("No signals in a Qt worker")
    )
    monkeypatch.setattr(cli.cv2, "imshow", lambda *args: pytest.fail("No HighGUI in a Qt worker"))
    monkeypatch.setattr(
        cli.cv2, "destroyAllWindows", lambda: pytest.fail("No global window cleanup")
    )

    assert (
        cli.main(
            [
                "--virtual-camera",
                "--tracking-debug",
                "--debug-face-preview",
                "--brightness",
                "30",
            ],
            runtime=bridge,
        )
        == 0
    )
    assert capture.stopped and tracker.closed
    assert not exported[0].any()
    np.testing.assert_array_equal(exported[1], exported[2])
    packet, _ = bridge.take()
    assert packet is not None and packet.frame is not None
    assert not packet.telemetry.effective_detected
    np.testing.assert_array_equal(packet.frame, exported[-1])
    assert packet.clean_frame is not None and packet.face_mesh is not None
    np.testing.assert_array_equal(packet.clean_frame, exported[-1])


def test_clean_program_and_diagnostics_have_separate_owned_buffers() -> None:
    bridge = RuntimeBridge()
    clean = np.full((10, 10, 3), 20, np.uint8)
    raw = np.full_like(clean, 140)
    debug = np.full_like(clean, 240)
    bridge.publish(
        clean, RuntimeTelemetry(), clean_frame=clean, raw_face=raw, face_mesh=debug,
    )
    clean[:] = raw[:] = debug[:] = 0
    packet, _ = bridge.take()
    assert packet is not None
    assert np.all(packet.clean_frame == 20)
    assert np.all(packet.frame == 20)
    assert np.all(packet.raw_face == 140)
    assert np.all(packet.face_mesh == 240)


@pytest.mark.parametrize("renderer_kind", ("procedural", "textured"))
def test_reported_closed_eye_scores_work_after_guided_calibration(renderer_kind: str) -> None:
    from kardboard_vtuber.tracking.eyes import calibrate_eyes, render_eye_state

    calibrated = calibrate_eyes([(.93, .94)] * 15, [(.51, .66)] * 15)
    assert calibrated.closed(.51, .66, left_eye=True)
    assert calibrated.closed(.66, .51, left_eye=False)
    assert not calibrated.closed(.93, .94, left_eye=True)
    assert not calibrated.closed(.94, .93, left_eye=False)
    raw = replace(state(34), left_eye_open=.1, right_eye_open=.1)
    smooth = replace(raw, left_eye_open=.8, right_eye_open=.8)
    visual = render_eye_state(smooth, raw)
    if renderer_kind == "textured":
        from kardboard_vtuber.renderer import Textured3DCardboardRenderer

        try:
            renderer = Textured3DCardboardRenderer()
        except RuntimeError as error:
            pytest.skip(f"GPU context unavailable: {error}")
    else:
        renderer = PS1CardboardRenderer()
    try:
        renderer.set_eye_sensitivity(calibrated)
        before = np.full((480, 640, 3), 90, np.uint8)
        after = before.copy()
        renderer.render(before, smooth)
        renderer.render(after, visual)
        assert visual.head_pose == smooth.head_pose
        assert not np.array_equal(before, after)
    finally:
        renderer.close()


def test_overlapping_eye_samples_are_not_silently_applied() -> None:
    from kardboard_vtuber.tracking.eyes import calibrate_eyes

    with pytest.raises(ValueError, match="overlap"):
        calibrate_eyes([(.8, .8)] * 15, [(.78, .77)] * 15)


def test_experimental_calibration_hold_can_be_published_without_debug_text() -> None:
    from kardboard_vtuber.tracking.body_head_fallback import BodyHeadFallback
    from kardboard_vtuber.tracking.full_body import FullBodyPoseState

    fallback = BodyHeadFallback()
    frame = np.full((480, 640, 3), 100, np.uint8)
    fallback.render_calibration_hold(
        frame, FullBodyPoseState.empty(0), current_timestamp_ms=0, show_status=False,
    )
    assert not frame.any()


def test_partial_runtime_initialization_closes_already_created_tracker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = FakeCapture([])
    tracker = FakeTracker([])
    monkeypatch.setattr(cli, "LatestFrameCamera", lambda config: capture)
    monkeypatch.setattr(cli, "_create_tracker", lambda args: tracker)

    def fail(args: object) -> None:
        raise RuntimeError("Hand model unavailable")

    monkeypatch.setattr(cli, "_create_hand_occluder", fail)
    bridge = RuntimeBridge()
    assert cli.main(["--render-cardboard", "--hand-occlusion"], runtime=bridge) == 1
    assert capture.stopped and tracker.closed
    assert "Hand model unavailable" in "\n".join(bridge.take()[1])


def test_cancel_during_model_initialization_does_not_open_source_or_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = FakeCapture([])
    tracker = FakeTracker([])
    bridge = RuntimeBridge()
    monkeypatch.setattr(cli, "LatestFrameCamera", lambda config: capture)

    def initialize(args: object) -> FakeTracker:
        bridge.stop_event.set()
        return tracker

    monkeypatch.setattr(cli, "_create_tracker", initialize)
    monkeypatch.setattr(cli, "_create_renderer", lambda args, **kw: PS1CardboardRenderer())
    monkeypatch.setattr(cli, "_create_action_detector", lambda args: None)
    monkeypatch.setattr(
        cli,
        "VirtualCameraOutput",
        lambda config: pytest.fail("A cancelled start must not open a virtual output"),
    )
    assert cli.main(["--virtual-camera"], runtime=bridge) == 0
    assert not capture.started and capture.stopped and tracker.closed


def test_live_eye_tuning_changes_procedural_expression_without_resetting_safe_frame() -> None:
    renderer = PS1CardboardRenderer()
    face = replace(state(1), left_eye_open=0.4, right_eye_open=0.4)
    original = np.full((480, 640, 3), 90, dtype=np.uint8)
    before = original.copy()
    renderer.render(before, face)
    renderer.set_eye_sensitivity(EyeSensitivity(left_closed=0.5, right_closed=0.2))
    after = original.copy()
    renderer.render(after, replace(face, timestamp_ms=34))
    assert not np.array_equal(before, after)
    held = original.copy()
    renderer.render(held, state(67, detected=False))
    np.testing.assert_array_equal(held, after)


def test_log_redaction_hides_full_urls_not_just_passwords() -> None:
    text = "failure https://example.invalid/path?secret=synthetic rtsp://user:example@host/video"
    safe = redact(text)
    assert "example.invalid" not in safe and "secret=" not in safe and "user:" not in safe
    assert "private" not in redact("HTTP://user:private@host/stream")
    assert "thetic" not in redact("http://user:syn'thetic@invalid/video")
    source = "http://user:example@invalid/video?token=synthetic value"
    bridge = RuntimeBridge(source=source)
    bridge.log("source=http://***@invalid/video?token=synthetic value | fps=20")
    assert bridge.take()[1] == ("source=[camera source hidden] | fps=20",)
