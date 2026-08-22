from __future__ import annotations

import pytest

from kardboard_vtuber.tracking.filters import (
    FaceMotionFilter,
    OneEuroFilter,
    OneEuroParameters,
)
from kardboard_vtuber.tracking.models import (
    FaceTrackingState,
    HeadPose,
    NormalizedLandmark,
)


def face_state(
    timestamp_ms: int,
    *,
    center_x: float = 0.5,
    left_eye: float = 1.0,
) -> FaceTrackingState:
    return FaceTrackingState(
        timestamp_ms=timestamp_ms,
        detected=True,
        landmarks=(NormalizedLandmark(center_x, 0.5, 0.0),),
        center_x=center_x,
        center_y=0.5,
        face_width=0.3,
        face_height=0.4,
        left_eye_open=left_eye,
        right_eye_open=1.0,
        mouth_open=0.0,
        head_pose=HeadPose.identity(),
    )


def test_one_euro_preserves_first_value_and_rejects_stale_time() -> None:
    filter_ = OneEuroFilter()

    assert filter_.filter(0.5, 1.0) == 0.5
    with pytest.raises(ValueError, match="strictly increasing"):
        filter_.filter(0.6, 1.0)


def test_one_euro_reduces_stationary_jitter() -> None:
    filter_ = OneEuroFilter(OneEuroParameters(min_cutoff=0.5, beta=0.0))
    raw = [0.5, 0.54, 0.46, 0.53, 0.47, 0.5]
    filtered = [
        filter_.filter(value, index / 30.0)
        for index, value in enumerate(raw)
    ]

    assert max(filtered[1:]) - min(filtered[1:]) < max(raw) - min(raw)


def test_beta_makes_fast_motion_more_responsive() -> None:
    fixed = OneEuroFilter(OneEuroParameters(min_cutoff=0.5, beta=0.0))
    adaptive = OneEuroFilter(OneEuroParameters(min_cutoff=0.5, beta=2.0))
    fixed.filter(0.0, 0.0)
    adaptive.filter(0.0, 0.0)

    fixed_value = fixed.filter(1.0, 1 / 30)
    adaptive_value = adaptive.filter(1.0, 1 / 30)

    assert adaptive_value > fixed_value


def test_face_motion_filter_smooths_state_and_resets_after_face_loss() -> None:
    filter_ = FaceMotionFilter()
    assert filter_.filter(face_state(0, center_x=0.5)).center_x == 0.5

    smoothed = filter_.filter(face_state(33, center_x=0.8, left_eye=0.0))
    assert 0.5 < smoothed.center_x < 0.8
    assert 0.0 < smoothed.left_eye_open < 1.0
    assert smoothed.landmarks[0].x < 0.8

    filter_.filter(FaceTrackingState.no_face(66))
    reacquired = filter_.filter(face_state(99, center_x=0.8, left_eye=0.0))
    assert reacquired.center_x == 0.8
    assert reacquired.left_eye_open == 0.0


def test_expression_filter_remains_responsive_to_fast_changes() -> None:
    filter_ = FaceMotionFilter()
    filter_.filter(face_state(0, left_eye=0.85))

    first = filter_.filter(face_state(33, left_eye=0.1))
    second = filter_.filter(face_state(66, left_eye=0.1))

    assert second.left_eye_open < 0.35
    assert second.left_eye_open < first.left_eye_open
