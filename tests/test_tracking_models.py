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


def test_normalize_face_swaps_eye_semantics_for_mirrored_input() -> None:
    state = normalize_face(
        timestamp_ms=42,
        landmarks=[FakeLandmark(0.5, 0.5, 0.0)],
        blendshapes=[
            FakeCategory("eyeBlinkLeft", 0.2),
            FakeCategory("eyeBlinkRight", 0.8),
        ],
        transformation_matrix=np.eye(4),
        swap_eyes=True,
    )

    assert state.left_eye_open == pytest.approx(0.2)
    assert state.right_eye_open == pytest.approx(0.8)


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


def test_draw_tracking_debug_displays_latest_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kardboard_vtuber.tracking import mediapipe_tracker

    labels: list[str] = []

    def record_text(
        _frame: np.ndarray,
        text: str,
        *_args: object,
        **_kwargs: object,
    ) -> None:
        labels.append(text)

    monkeypatch.setattr(mediapipe_tracker.cv2, "putText", record_text)
    mediapipe_tracker.draw_tracking_debug(
        np.zeros((240, 320, 3), dtype=np.uint8),
        normalize_face(
            timestamp_ms=1,
            landmarks=[FakeLandmark(0.5, 0.5, 0.0)],
            blendshapes=[],
            transformation_matrix=np.eye(4),
        ),
        action="left_wink",
    )

    assert "ACTION = LEFT WINK" in labels


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


def test_face_mesh_inset_labels_pose_xyz_axes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kardboard_vtuber.tracking import mediapipe_tracker

    labels: list[str] = []

    def record_text(
        _frame: np.ndarray,
        text: str,
        *_args: object,
        **_kwargs: object,
    ) -> None:
        labels.append(text)

    monkeypatch.setattr(mediapipe_tracker.cv2, "putText", record_text)
    draw_tracking_debug(
        np.zeros((720, 1280, 3), dtype=np.uint8),
        normalize_face(
            timestamp_ms=1,
            landmarks=[FakeLandmark(0.5, 0.5, 0.0) for _ in range(478)],
            blendshapes=[],
            transformation_matrix=np.eye(4),
        ),
    )

    assert {"POSE", "X", "Y", "Z"} <= set(labels)


def test_face_mesh_inset_preserves_portrait_frame_aspect_ratio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kardboard_vtuber.tracking import mediapipe_tracker

    landmarks = [FakeLandmark(0.5, 0.5, 0.0) for _ in range(478)]
    oval = mediapipe_tracker._FACE_OVAL
    for position, index in enumerate(oval):
        angle = 2 * np.pi * position / len(oval)
        landmarks[index] = FakeLandmark(
            0.5 + 0.1 * np.cos(angle),
            0.5 + 0.1 * np.sin(angle),
            0.0,
        )
    state = normalize_face(
        timestamp_ms=1,
        landmarks=landmarks,
        blendshapes=[],
        transformation_matrix=np.eye(4),
    )
    lines: list[tuple[tuple[int, int], tuple[int, int]]] = []

    def record_line(
        _frame: np.ndarray,
        start: tuple[int, int],
        end: tuple[int, int],
        *_args: object,
        **_kwargs: object,
    ) -> None:
        lines.append((start, end))

    monkeypatch.setattr(mediapipe_tracker.cv2, "line", record_line)
    mediapipe_tracker.draw_tracking_debug(
        np.zeros((1920, 1080, 3), dtype=np.uint8),
        state,
    )

    oval_points = [point for line in lines[: len(oval)] for point in line]
    width = max(point[0] for point in oval_points) - min(point[0] for point in oval_points)
    height = max(point[1] for point in oval_points) - min(point[1] for point in oval_points)
    assert height > width * 1.5
