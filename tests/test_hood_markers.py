from __future__ import annotations

import cv2
import numpy as np
import pytest

from kardboard_vtuber.tracking.full_body import FullBodyPoseState, PoseLandmark
from kardboard_vtuber.tracking.hood_markers import (
    HoodMarkerColor,
    HoodMarkerHeadTracker,
    HoodMarkerTrackerConfig,
    HoodTrackingSource,
)
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose


def pose_state(
    timestamp_ms: int = 1,
    center_x: float = 0.5,
) -> FullBodyPoseState:
    landmarks = [PoseLandmark(center_x, 0.5, 0.0, 1.0, 1.0) for _ in range(33)]
    landmarks[11] = PoseLandmark(center_x - 0.12, 0.58, 0.0, 1.0, 1.0)
    landmarks[12] = PoseLandmark(center_x + 0.12, 0.58, 0.0, 1.0, 1.0)
    landmarks[23] = PoseLandmark(center_x - 0.07, 0.78, 0.0, 1.0, 1.0)
    landmarks[24] = PoseLandmark(center_x + 0.07, 0.78, 0.0, 1.0, 1.0)
    return FullBodyPoseState(timestamp_ms=timestamp_ms, landmarks=tuple(landmarks))


def marker_frame(
    color: tuple[int, int, int],
    *,
    side_pixels: int = 100,
    center_x: float = 0.5,
) -> np.ndarray:
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    half_side = side_pixels // 2
    center_x_pixels = round(center_x * frame.shape[1])
    cv2.rectangle(
        frame,
        (center_x_pixels - half_side, 225 - half_side),
        (center_x_pixels + half_side, 225 + half_side),
        color,
        -1,
    )
    return frame


def test_marker_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="input_width"):
        HoodMarkerTrackerConfig(input_width=0)
    with pytest.raises(ValueError, match="stale_after_ms"):
        HoodMarkerTrackerConfig(stale_after_ms=-1)
    with pytest.raises(ValueError, match="maximum_face_age_ms"):
        HoodMarkerTrackerConfig(maximum_face_age_ms=-1)
    with pytest.raises(ValueError, match="maximum_pose_age_ms"):
        HoodMarkerTrackerConfig(maximum_pose_age_ms=-1)


@pytest.mark.parametrize(
    ("color_bgr", "expected"),
    [
        ((0, 255, 0), HoodMarkerColor.GREEN),
        ((255, 0, 0), HoodMarkerColor.BLUE),
    ],
)
def test_tracker_detects_coloured_square(
    color_bgr: tuple[int, int, int],
    expected: HoodMarkerColor,
) -> None:
    tracker = HoodMarkerHeadTracker()

    head = tracker.update(
        marker_frame(color_bgr),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    snapshot = tracker.snapshot()
    assert head.detected
    assert len(snapshot.observations) == 1
    assert snapshot.observations[0].color is expected
    assert snapshot.observations[0].center_x == pytest.approx(0.5, abs=0.01)
    assert snapshot.observations[0].center_y == pytest.approx(0.3125, abs=0.01)
    assert snapshot.observations[0].side_height > snapshot.observations[0].side_width


@pytest.mark.parametrize(
    ("color_bgr", "expected_yaw"),
    [
        ((0, 255, 0), 90.0),
        ((255, 0, 0), -90.0),
    ],
)
def test_side_markers_follow_anatomical_left_and_right(
    color_bgr: tuple[int, int, int],
    expected_yaw: float,
) -> None:
    tracker = HoodMarkerHeadTracker()

    head = tracker.update(
        marker_frame(color_bgr),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    assert head.head_pose.yaw_degrees == pytest.approx(expected_yaw)
    assert head.face_width > 0.0
    assert head.face_height > 0.0


@pytest.mark.parametrize("color_bgr", [(0, 0, 255), (180, 80, 255)])
def test_red_and_pink_squares_are_not_accepted(
    color_bgr: tuple[int, int, int],
) -> None:
    tracker = HoodMarkerHeadTracker()

    tracker.update(
        marker_frame(color_bgr),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    assert tracker.snapshot().observations == ()
    assert tracker.snapshot().source is HoodTrackingSource.REAR


def test_recent_marker_position_is_predicted_during_short_occlusion() -> None:
    tracker = HoodMarkerHeadTracker()
    detected = tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )
    predicted = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=200,
        face=FaceTrackingState.no_face(200),
        pose=FullBodyPoseState.empty(200),
    )

    assert detected.detected
    assert predicted.detected
    assert tracker.snapshot().predicted
    assert tracker.snapshot().source is HoodTrackingSource.PREDICTION


def test_marker_prediction_expires_closed() -> None:
    tracker = HoodMarkerHeadTracker()
    tracker.update(
        marker_frame((255, 0, 0)),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    expired = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=800,
        face=FaceTrackingState.no_face(800),
        pose=FullBodyPoseState.empty(800),
    )

    assert not expired.detected


def test_prediction_requires_recent_marker_history() -> None:
    tracker = HoodMarkerHeadTracker()
    tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=10,
        face=FaceTrackingState(
            timestamp_ms=10,
            detected=True,
            landmarks=(),
            center_x=0.5,
            center_y=0.3,
            face_width=0.1,
            face_height=0.1,
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose.identity(),
        ),
        pose=FullBodyPoseState.empty(10),
    )

    predicted = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=100,
        face=FaceTrackingState.no_face(100),
        pose=FullBodyPoseState.empty(100),
    )

    assert not predicted.detected
    assert tracker.snapshot().source is HoodTrackingSource.NONE


def test_body_without_face_or_side_markers_resolves_to_rear_view() -> None:
    tracker = HoodMarkerHeadTracker()

    head = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    assert head.detected
    assert tracker.snapshot().source is HoodTrackingSource.REAR
    assert head.head_pose.yaw_degrees == pytest.approx(179.0)
    assert 0.04 <= head.face_width <= 0.14


def test_side_marker_keeps_pose_derived_head_size() -> None:
    tracker = HoodMarkerHeadTracker()
    rear = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    side = tracker.update(
        marker_frame((0, 255, 0), side_pixels=110),
        timestamp_ms=20,
        face=FaceTrackingState.no_face(20),
        pose=pose_state(20),
    )

    assert side.face_width == pytest.approx(rear.face_width)
    assert side.face_height == pytest.approx(rear.face_height)


def test_expired_reference_size_is_relearned_from_current_perspective() -> None:
    tracker = HoodMarkerHeadTracker(HoodMarkerTrackerConfig(stale_after_ms=100))
    first = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )
    wider_pose = pose_state(200)
    landmarks = list(wider_pose.landmarks)
    landmarks[11] = PoseLandmark(0.25, 0.58, 0.0, 1.0, 1.0)
    landmarks[12] = PoseLandmark(0.75, 0.58, 0.0, 1.0, 1.0)
    wider_pose = FullBodyPoseState(200, tuple(landmarks))

    reacquired = tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=200,
        face=FaceTrackingState.no_face(200),
        pose=wider_pose,
    )

    assert reacquired.face_width > first.face_width * 1.5


def test_stale_pose_cannot_refresh_head_tracking() -> None:
    tracker = HoodMarkerHeadTracker(
        HoodMarkerTrackerConfig(stale_after_ms=100, maximum_pose_age_ms=50)
    )

    head = tracker.update(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=1_000,
        face=FaceTrackingState.no_face(1_000),
        pose=pose_state(10),
    )

    assert not head.detected
    assert tracker.snapshot().source is HoodTrackingSource.NONE


def test_stale_pose_cannot_suppress_current_marker_detection() -> None:
    tracker = HoodMarkerHeadTracker(
        HoodMarkerTrackerConfig(maximum_pose_age_ms=50)
    )
    tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    head = tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=100,
        face=FaceTrackingState.no_face(100),
        pose=pose_state(10, center_x=0.8),
    )

    assert head.detected
    assert tracker.snapshot().source is HoodTrackingSource.MARKER


def test_expired_marker_size_history_does_not_block_reacquisition() -> None:
    tracker = HoodMarkerHeadTracker(HoodMarkerTrackerConfig(stale_after_ms=100))
    tracker.update(
        marker_frame((255, 0, 0), side_pixels=30),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    reacquired = tracker.update(
        marker_frame((255, 0, 0), side_pixels=80),
        timestamp_ms=200,
        face=FaceTrackingState.no_face(200),
        pose=pose_state(200),
    )

    assert reacquired.detected
    assert tracker.snapshot().source is HoodTrackingSource.MARKER


def test_expired_head_anchor_does_not_block_moved_marker_reacquisition() -> None:
    tracker = HoodMarkerHeadTracker(HoodMarkerTrackerConfig(stale_after_ms=100))
    tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )
    moved_pose = pose_state(200, center_x=0.8)
    landmarks = list(moved_pose.landmarks)
    for index in (0, 2, 5, 7, 8):
        point = landmarks[index]
        landmarks[index] = PoseLandmark(
            point.x,
            point.y,
            point.z,
            0.0,
            0.0,
        )
    moved_pose = FullBodyPoseState(200, tuple(landmarks))

    reacquired = tracker.update(
        marker_frame((0, 255, 0), center_x=0.8),
        timestamp_ms=200,
        face=FaceTrackingState.no_face(200),
        pose=moved_pose,
    )

    assert reacquired.detected
    assert tracker.snapshot().source is HoodTrackingSource.MARKER


def test_stale_face_cannot_suppress_marker_tracking() -> None:
    tracker = HoodMarkerHeadTracker(
        HoodMarkerTrackerConfig(maximum_face_age_ms=50)
    )

    head = tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=1_000,
        face=FaceTrackingState(
            timestamp_ms=10,
            detected=True,
            landmarks=(),
            center_x=0.2,
            center_y=0.2,
            face_width=0.1,
            face_height=0.1,
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose.identity(),
        ),
        pose=pose_state(1_000),
    )

    assert head.detected
    assert tracker.snapshot().source is HoodTrackingSource.MARKER
    assert head.head_pose.yaw_degrees == pytest.approx(90.0)


def test_body_only_state_becomes_rear_after_side_marker_hold() -> None:
    tracker = HoodMarkerHeadTracker()
    tracker.update(
        marker_frame((0, 255, 0)),
        timestamp_ms=10,
        face=FaceTrackingState.no_face(10),
        pose=pose_state(10),
    )

    head = FaceTrackingState.no_face()
    for timestamp_ms in (500, 550, 600, 650, 700):
        head = tracker.update(
            np.zeros((720, 1280, 3), dtype=np.uint8),
            timestamp_ms=timestamp_ms,
            face=FaceTrackingState.no_face(timestamp_ms),
            pose=pose_state(timestamp_ms),
        )

    assert head.head_pose.yaw_degrees > 170.0
    assert tracker.snapshot().source is HoodTrackingSource.REAR
