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
    pitch: float = -10.0,
    yaw: float = 0.0,
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
        head_pose=HeadPose(0.0, 0.0, 0.0, pitch, yaw, 0.0),
    )


def test_renderer_blacks_frame_before_first_face_detection() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.full((720, 1280, 3), 100, dtype=np.uint8)

    renderer.render(frame, state(1, detected=False))

    assert np.count_nonzero(frame) == 0


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

    assert np.array_equal(closed[:470], opened[:470])
    assert not np.array_equal(closed[470:], opened[470:])


def test_screen_left_k_follows_screen_left_eye_in_mirrored_preview() -> None:
    renderer = PS1CardboardRenderer(CardboardRendererConfig(mirrored=True))
    open_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    wink_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    renderer.render(open_frame, state(1))
    renderer.render(wink_frame, state(34, right_eye=0.0))

    difference = cv_difference = np.abs(
        open_frame.astype(np.int16) - wink_frame.astype(np.int16)
    )
    left_half = cv_difference[:, :640].sum()
    right_half = difference[:, 640:].sum()
    assert left_half > right_half


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
    assert np.array_equal(dark[450, 640], bright[450, 640])


def test_renderer_freezes_last_safe_frame_during_tracking_loss() -> None:
    renderer = PS1CardboardRenderer()
    tracked = np.full((720, 1280, 3), 50, dtype=np.uint8)
    exposed_camera = np.full((720, 1280, 3), 200, dtype=np.uint8)

    renderer.render(tracked, state(1000))
    renderer.render(exposed_camera, state(5000, detected=False))

    assert np.array_equal(exposed_camera, tracked)


def test_renderer_returns_to_black_fail_closed_state_after_reset() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.full((720, 1280, 3), 80, dtype=np.uint8)

    renderer.render(frame, state(1000))
    renderer.reset()
    frame.fill(200)
    renderer.render(frame, state(2000, detected=False))

    assert np.count_nonzero(frame) == 0


def test_positive_yaw_reveals_depth_on_screen_left() -> None:
    right_turn = np.zeros((720, 1280, 3), dtype=np.uint8)
    left_turn = np.zeros((720, 1280, 3), dtype=np.uint8)
    right_renderer = PS1CardboardRenderer()
    left_renderer = PS1CardboardRenderer()

    for timestamp_ms in range(0, 400, 33):
        right_renderer.render(right_turn, state(timestamp_ms, yaw=45.0))
        left_renderer.render(left_turn, state(timestamp_ms, yaw=-45.0))

    assert np.count_nonzero(right_turn[:, 300:430]) > np.count_nonzero(right_turn[:, 850:980])
    assert np.count_nonzero(left_turn[:, 850:980]) > np.count_nonzero(left_turn[:, 300:430])


def test_pitch_controls_top_and_underside_visibility() -> None:
    looking_down = np.zeros((720, 1280, 3), dtype=np.uint8)
    looking_up = np.zeros((720, 1280, 3), dtype=np.uint8)

    PS1CardboardRenderer().render(looking_down, state(1, pitch=20.0))
    PS1CardboardRenderer().render(looking_up, state(1, pitch=-45.0))

    assert np.count_nonzero(looking_down[80:180]) > np.count_nonzero(looking_up[80:180])
    assert np.count_nonzero(looking_up[480:580]) > np.count_nonzero(looking_down[480:580])


def test_downward_pitch_keeps_crown_inside_shell_silhouette() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    renderer.render(frame, state(1, pitch=20.0))

    assert np.count_nonzero(frame[60:150, 500:780]) > 0
