from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from kardboard_vtuber.tracking.body_head_fallback import (
    BodyHeadFallback,
    BodyHeadFallbackConfig,
)
from kardboard_vtuber.tracking.full_body import FullBodyPoseState, PoseLandmark
from kardboard_vtuber.tracking.models import FaceTrackingState
from tests.test_ps1_cardboard_renderer import state


def pose_state(
    *,
    timestamp_ms: int = 1,
    left: tuple[float, float, float] = (0.38, 0.40, 0.0),
    right: tuple[float, float, float] = (0.62, 0.40, 0.0),
    confidence: float = 1.0,
) -> FullBodyPoseState:
    landmarks = [
        PoseLandmark(0.5, 0.5, 0.0, confidence, confidence)
        for _ in range(33)
    ]
    landmarks[11] = PoseLandmark(*left, confidence, confidence)
    landmarks[12] = PoseLandmark(*right, confidence, confidence)
    shoulder_center_x = (left[0] + right[0]) / 2.0
    shoulder_center_y = (left[1] + right[1]) / 2.0
    landmarks[23] = PoseLandmark(
        shoulder_center_x - 0.07,
        shoulder_center_y + 0.22,
        0.0,
        confidence,
        confidence,
    )
    landmarks[24] = PoseLandmark(
        shoulder_center_x + 0.07,
        shoulder_center_y + 0.22,
        0.0,
        confidence,
        confidence,
    )
    return FullBodyPoseState(timestamp_ms=timestamp_ms, landmarks=tuple(landmarks))


def face_state(timestamp_ms: int, *, yaw: float = 0.0) -> FaceTrackingState:
    return replace(
        state(timestamp_ms, yaw=yaw),
        center_y=0.24,
        face_width=0.12,
        face_height=0.16,
    )


def calibrate(fallback: BodyHeadFallback, *, yaw: float = 0.0) -> None:
    for timestamp_ms in range(10, 60, 10):
        fallback.update(
            face_state(timestamp_ms, yaw=yaw),
            pose_state(timestamp_ms=timestamp_ms),
            current_timestamp_ms=timestamp_ms,
        )


def activate(
    fallback: BodyHeadFallback,
    pose: FullBodyPoseState,
) -> FaceTrackingState:
    result = FaceTrackingState.no_face()
    for timestamp_ms in (70, 80, 90):
        result = fallback.update(
            FaceTrackingState.no_face(timestamp_ms),
            replace(pose, timestamp_ms=timestamp_ms),
            current_timestamp_ms=timestamp_ms,
        )
    return result


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="minimum_landmark_confidence"):
        BodyHeadFallbackConfig(minimum_landmark_confidence=1.1)
    with pytest.raises(ValueError, match="coverage_scale"):
        BodyHeadFallbackConfig(coverage_scale=0.0)
    with pytest.raises(ValueError, match="maximum_state_age_ms"):
        BodyHeadFallbackConfig(maximum_state_age_ms=0)


def test_detected_face_is_returned_and_used_for_calibration() -> None:
    fallback = BodyHeadFallback()
    face = face_state(10)

    assert fallback.update(
        face,
        pose_state(timestamp_ms=10),
        current_timestamp_ms=10,
    ) is face
    for timestamp_ms in range(20, 60, 10):
        fallback.update(
            face_state(timestamp_ms),
            pose_state(timestamp_ms=timestamp_ms),
            current_timestamp_ms=timestamp_ms,
        )

    inferred = activate(fallback, pose_state())
    assert inferred.detected
    assert inferred.center_x == pytest.approx(face.center_x)
    assert inferred.center_y == pytest.approx(face.center_y)
    assert inferred.face_width > face.face_width
    assert inferred.face_height > face.face_height


def test_fallback_refuses_to_guess_without_prior_face_calibration() -> None:
    inferred = BodyHeadFallback().update(
        FaceTrackingState.no_face(20),
        pose_state(timestamp_ms=20),
        current_timestamp_ms=20,
    )

    assert not inferred.detected


def test_calibration_hold_masks_head_but_keeps_lower_body_visible() -> None:
    fallback = BodyHeadFallback()
    frame = np.full((720, 1280, 3), 100, dtype=np.uint8)

    fallback.render_calibration_hold(
        frame,
        pose_state(),
        current_timestamp_ms=1,
    )

    assert np.all(frame[200, 1000] == 0)
    assert np.all(frame[600, 1000] == 100)
    assert np.count_nonzero(frame[:140]) > 0


def test_calibration_hold_is_fully_opaque_without_body_pose() -> None:
    fallback = BodyHeadFallback()
    frame = np.full((720, 1280, 3), 100, dtype=np.uint8)

    fallback.render_calibration_hold(
        frame,
        FullBodyPoseState.empty(),
        current_timestamp_ms=0,
    )

    assert np.all(frame[300:, :] == 0)
    assert np.count_nonzero(frame[:140]) > 0


def test_calibration_hold_is_fully_opaque_with_stale_body_pose() -> None:
    fallback = BodyHeadFallback(BodyHeadFallbackConfig(maximum_state_age_ms=50))
    frame = np.full((720, 1280, 3), 100, dtype=np.uint8)

    fallback.render_calibration_hold(
        frame,
        pose_state(timestamp_ms=10),
        current_timestamp_ms=1_000,
    )

    assert np.all(frame[300:, :] == 0)
    assert np.count_nonzero(frame[:140]) > 0


def test_calibration_progress_becomes_ready_after_required_samples() -> None:
    fallback = BodyHeadFallback()

    assert not fallback.calibration_ready
    calibrate(fallback)

    assert fallback.calibration_ready
    assert fallback.calibration_samples == fallback.required_calibration_samples


def test_fallback_waits_for_multiple_face_loss_results() -> None:
    fallback = BodyHeadFallback()
    calibrate(fallback)

    first_miss = fallback.update(
        FaceTrackingState.no_face(70),
        pose_state(timestamp_ms=70),
        current_timestamp_ms=70,
    )
    repeated_snapshot = fallback.update(
        FaceTrackingState.no_face(70),
        pose_state(timestamp_ms=70),
        current_timestamp_ms=70,
    )
    second_miss = fallback.update(
        FaceTrackingState.no_face(80),
        pose_state(timestamp_ms=80),
        current_timestamp_ms=80,
    )

    assert not first_miss.detected
    assert not repeated_snapshot.detected
    assert not second_miss.detected
    assert fallback.update(
        FaceTrackingState.no_face(90),
        pose_state(timestamp_ms=90),
        current_timestamp_ms=90,
    ).detected


def test_fallback_follows_shoulder_motion_and_smooths_it() -> None:
    fallback = BodyHeadFallback()
    calibrate(fallback)
    first = activate(fallback, pose_state())
    moved = fallback.update(
        FaceTrackingState.no_face(100),
        pose_state(
            timestamp_ms=100,
            left=(0.48, 0.50, 0.0),
            right=(0.72, 0.50, 0.0),
        ),
        current_timestamp_ms=100,
    )

    assert first.center_x == pytest.approx(0.5)
    assert first.center_y == pytest.approx(0.24)
    assert moved.center_x == pytest.approx(0.535)
    assert moved.center_y == pytest.approx(0.275)


def test_fallback_tracks_calibrated_shoulder_yaw_after_face_loss() -> None:
    fallback = BodyHeadFallback()
    calibrate(fallback, yaw=15.0)
    inferred = activate(
        fallback,
        pose_state(
            left=(0.38, 0.40, -0.12),
            right=(0.62, 0.40, 0.12),
        ),
    )

    assert inferred.head_pose.yaw_degrees == pytest.approx(60.0)


def test_fallback_fails_closed_when_shoulders_are_not_confident() -> None:
    missing = FaceTrackingState.no_face(20)

    inferred = BodyHeadFallback().update(
        missing,
        pose_state(timestamp_ms=20, confidence=0.2),
        current_timestamp_ms=20,
    )

    assert inferred is missing
    assert not inferred.detected


def test_fallback_fails_closed_for_stale_face_and_pose_states() -> None:
    fallback = BodyHeadFallback(BodyHeadFallbackConfig(maximum_state_age_ms=50))

    stale_face = fallback.update(
        face_state(10),
        pose_state(timestamp_ms=1_000),
        current_timestamp_ms=1_000,
    )
    stale_pose = fallback.update(
        FaceTrackingState.no_face(1_000),
        pose_state(timestamp_ms=10),
        current_timestamp_ms=1_000,
    )

    assert not stale_face.detected
    assert not stale_pose.detected
