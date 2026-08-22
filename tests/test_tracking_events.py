from __future__ import annotations

from kardboard_vtuber.tracking.events import (
    ActionThresholds,
    FaceAction,
    FaceActionDetector,
)
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose


def state(
    timestamp_ms: int,
    *,
    detected: bool = True,
    left_eye: float = 1.0,
    right_eye: float = 1.0,
    mouth: float = 0.0,
) -> FaceTrackingState:
    return FaceTrackingState(
        timestamp_ms=timestamp_ms,
        detected=detected,
        landmarks=(),
        center_x=0.5,
        center_y=0.5,
        face_width=0.3,
        face_height=0.4,
        left_eye_open=left_eye,
        right_eye_open=right_eye,
        mouth_open=mouth,
        head_pose=HeadPose.identity(),
    )


def actions(detector: FaceActionDetector, observation: FaceTrackingState) -> list[FaceAction]:
    return [event.action for event in detector.update(observation)]


def test_detector_logs_initial_face_eyes_and_mouth_states() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=0, eye_hold_ms=0))

    assert actions(detector, state(1)) == [
        FaceAction.FACE_DETECTED,
        FaceAction.EYES_OPEN,
        FaceAction.MOUTH_CLOSED,
    ]


def test_detector_distinguishes_left_and_right_winks() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=0, eye_hold_ms=0))
    detector.update(state(1))

    assert actions(detector, state(2, left_eye=0.1, right_eye=0.9)) == [FaceAction.LEFT_WINK]
    assert actions(detector, state(3, left_eye=0.9, right_eye=0.9)) == [FaceAction.EYES_OPEN]
    assert actions(detector, state(4, left_eye=0.9, right_eye=0.1)) == [FaceAction.RIGHT_WINK]


def test_detector_recognizes_asymmetric_wink_with_spectacle_glare() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=0, eye_hold_ms=0))
    detector.update(state(1))

    assert actions(detector, state(2, left_eye=0.79, right_eye=0.60)) == [
        FaceAction.RIGHT_WINK
    ]


def test_detector_emits_blink_when_both_eyes_reopen_quickly() -> None:
    detector = FaceActionDetector(
        ActionThresholds(hold_ms=0, eye_hold_ms=0, maximum_blink_ms=500)
    )
    detector.update(state(100))

    assert actions(detector, state(200, left_eye=0.1, right_eye=0.1)) == [
        FaceAction.EYES_CLOSED
    ]
    assert actions(detector, state(350)) == [FaceAction.BLINK, FaceAction.EYES_OPEN]


def test_detector_logs_mouth_open_and_closed() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=0, eye_hold_ms=0))
    detector.update(state(1))

    assert actions(detector, state(2, mouth=0.8)) == [FaceAction.MOUTH_OPEN]
    assert actions(detector, state(3, mouth=0.05)) == [FaceAction.MOUTH_CLOSED]


def test_detector_debounces_short_changes() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=100, eye_hold_ms=100))

    assert actions(detector, state(0)) == []
    assert actions(detector, state(50)) == []
    assert actions(detector, state(100)) == [
        FaceAction.FACE_DETECTED,
        FaceAction.EYES_OPEN,
        FaceAction.MOUTH_CLOSED,
    ]


def test_detector_logs_face_loss_and_ignores_duplicate_timestamp() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=0, eye_hold_ms=0))
    detector.update(state(1))

    assert actions(detector, state(2, detected=False)) == [FaceAction.FACE_LOST]
    assert actions(detector, state(2, detected=False)) == []


def test_transient_tracking_loss_does_not_repeat_stable_actions() -> None:
    detector = FaceActionDetector(ActionThresholds(hold_ms=100, eye_hold_ms=100))
    detector.update(state(0))
    detector.update(state(100))

    assert actions(detector, state(200, detected=False)) == []
    assert actions(detector, state(250)) == []
