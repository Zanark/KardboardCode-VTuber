from __future__ import annotations

import numpy as np

from kardboard_vtuber.renderer import CardboardRendererConfig, PS1CardboardRenderer
from kardboard_vtuber.tracking.models import (
    FaceTrackingState,
    HeadPose,
    NormalizedLandmark,
)


def state(
    timestamp_ms: int,
    *,
    detected: bool = True,
    left_eye: float = 1.0,
    right_eye: float = 1.0,
    mouth: float = 0.0,
) -> FaceTrackingState:
    if not detected:
        return FaceTrackingState.no_face(timestamp_ms)
    return FaceTrackingState(
        timestamp_ms=timestamp_ms,
        detected=True,
        landmarks=(NormalizedLandmark(0.5, 0.5, 0.0),),
        center_x=0.5,
        center_y=0.45,
        face_width=0.28,
        face_height=0.34,
        left_eye_open=left_eye,
        right_eye_open=right_eye,
        mouth_open=mouth,
        head_pose=HeadPose.identity(),
    )


def test_renderer_leaves_frame_unchanged_without_face() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.full((720, 1280, 3), 100, dtype=np.uint8)
    before = frame.copy()

    renderer.render(frame, state(1, detected=False))

    assert np.array_equal(frame, before)


def test_renderer_overlays_only_tracked_head_region() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    renderer.render(frame, state(1))

    assert np.count_nonzero(frame[180:520, 400:880]) > 0
    assert np.count_nonzero(frame[:80, :80]) == 0


def test_mouth_openness_changes_front_flap_pixels() -> None:
    closed_renderer = PS1CardboardRenderer()
    open_renderer = PS1CardboardRenderer()
    closed = np.zeros((720, 1280, 3), dtype=np.uint8)
    opened = np.zeros((720, 1280, 3), dtype=np.uint8)

    for timestamp_ms in range(0, 300, 33):
        closed_renderer.render(closed, state(timestamp_ms, mouth=0.0))
        open_renderer.render(opened, state(timestamp_ms, mouth=1.0))

    assert not np.array_equal(closed, opened)


def test_mirrored_eye_mapping_changes_opposite_screen_side() -> None:
    renderer = PS1CardboardRenderer(CardboardRendererConfig(mirrored=True))
    open_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    wink_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    renderer.render(open_frame, state(1))
    renderer.render(wink_frame, state(34, left_eye=0.0))

    difference = cv_difference = np.abs(
        open_frame.astype(np.int16) - wink_frame.astype(np.int16)
    )
    left_half = cv_difference[:, :640].sum()
    right_half = difference[:, 640:].sum()
    assert right_half > left_half


def test_renderer_leaves_center_neck_opening_visible() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.full((720, 1280, 3), 91, dtype=np.uint8)

    renderer.render(frame, state(1))

    assert np.all(frame[480, 640] == 91)
    assert not np.all(frame[450, 500] == 91)


def test_renderer_front_panel_is_fully_opaque() -> None:
    renderer = PS1CardboardRenderer()
    dark = np.zeros((720, 1280, 3), dtype=np.uint8)
    bright = np.full((720, 1280, 3), 255, dtype=np.uint8)

    renderer.render(dark, state(1))
    renderer.render(bright, state(34))

    assert np.array_equal(dark[300, 640], bright[300, 640])
