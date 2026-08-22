from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from kardboard_vtuber.tracking.mediapipe_tracker import draw_tracking_debug
from kardboard_vtuber.tracking.models import HeadPose, normalize_face


@dataclass
class FakeLandmark:
    x: float
    y: float
    z: float


@dataclass
class FakeCategory:
    category_name: str
    score: float


def test_head_pose_identity_matrix() -> None:
    pose = HeadPose.from_matrix(np.eye(4))

    assert pose.translation_x == 0
    assert pose.translation_y == 0
    assert pose.translation_z == 0
    assert pose.pitch_degrees == pytest.approx(0)
    assert pose.yaw_degrees == pytest.approx(0)
    assert pose.roll_degrees == pytest.approx(0)


def test_head_pose_rejects_non_4x4_matrix() -> None:
    with pytest.raises(ValueError, match="must be 4x4"):
        HeadPose.from_matrix(np.eye(3))


def test_normalize_face_extracts_bounds_and_expressions() -> None:
    state = normalize_face(
        timestamp_ms=42,
        landmarks=[
            FakeLandmark(0.2, 0.3, -0.1),
            FakeLandmark(0.8, 0.9, 0.1),
        ],
        blendshapes=[
            FakeCategory("eyeBlinkLeft", 0.25),
            FakeCategory("eyeBlinkRight", 0.75),
            FakeCategory("jawOpen", 0.4),
        ],
        transformation_matrix=np.eye(4),
    )

    assert state.detected
    assert state.timestamp_ms == 42
    assert state.center_x == pytest.approx(0.5)
    assert state.center_y == pytest.approx(0.6)
    assert state.face_width == pytest.approx(0.6)
    assert state.face_height == pytest.approx(0.6)
    assert state.left_eye_open == pytest.approx(0.75)
    assert state.right_eye_open == pytest.approx(0.25)
    assert state.mouth_open == pytest.approx(0.4)


def test_normalize_face_returns_no_face_for_empty_landmarks() -> None:
    state = normalize_face(
        timestamp_ms=7,
        landmarks=[],
        blendshapes=[],
        transformation_matrix=None,
    )

    assert not state.detected
    assert state.timestamp_ms == 7
    assert state.landmarks == ()


def test_normalize_face_clamps_invalid_blendshape_scores() -> None:
    state = normalize_face(
        timestamp_ms=1,
        landmarks=[FakeLandmark(0.5, 0.5, 0.0)],
        blendshapes=[
            FakeCategory("eyeBlinkLeft", 2.0),
            FakeCategory("eyeBlinkRight", -1.0),
            FakeCategory("jawOpen", float("nan")),
        ],
        transformation_matrix=None,
    )

    assert state.left_eye_open == 0.0
    assert state.right_eye_open == 1.0
    assert state.mouth_open == 0.0


def test_draw_tracking_debug_modifies_frame() -> None:
    state = normalize_face(
        timestamp_ms=1,
        landmarks=[
            FakeLandmark(0.25, 0.25, 0.0),
            FakeLandmark(0.75, 0.75, 0.0),
        ],
        blendshapes=[FakeCategory("jawOpen", 0.5)],
        transformation_matrix=np.eye(4),
    )
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    draw_tracking_debug(frame, state)

    assert np.count_nonzero(frame) > 0


def test_draw_tracking_debug_adds_black_face_mesh_inset() -> None:
    landmarks = [
        FakeLandmark(0.2 + (index % 20) * 0.03, 0.2 + (index // 20) * 0.02, 0.0)
        for index in range(478)
    ]
    state = normalize_face(
        timestamp_ms=1,
        landmarks=landmarks,
        blendshapes=[],
        transformation_matrix=np.eye(4),
    )
    frame = np.full((720, 1280, 3), 255, dtype=np.uint8)

    draw_tracking_debug(frame, state)

    assert np.mean(frame[30:220, 900:1240]) < 80
