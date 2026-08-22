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
    pitch: float = -10.0,
    yaw: float = 0.0,
    roll: float = 0.0,
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
        mouth_open=0.0,
        head_pose=HeadPose(0.0, 0.0, 0.0, pitch, yaw, roll),
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


def test_default_shell_has_enlarged_xyz_dimensions() -> None:
    config = CardboardRendererConfig()

    assert config.box_width_multiplier == 2.25
    assert config.box_height_multiplier == 2.05
    assert config.box_depth_multiplier == 1.55


def test_screen_left_k_follows_anatomical_left_eye_in_mirrored_preview() -> None:
    renderer = PS1CardboardRenderer(CardboardRendererConfig(mirrored=True))
    open_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    wink_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    renderer.render(open_frame, state(1))
    renderer.render(wink_frame, state(34, left_eye=0.56, right_eye=0.96))

    difference = cv_difference = np.abs(
        open_frame.astype(np.int16) - wink_frame.astype(np.int16)
    )
    left_half = cv_difference[:, :640].sum()
    right_half = difference[:, 640:].sum()
    assert left_half > right_half


def test_screen_right_c_follows_anatomical_right_eye_in_mirrored_preview() -> None:
    renderer = PS1CardboardRenderer(CardboardRendererConfig(mirrored=True))
    open_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    wink_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    renderer.render(open_frame, state(1))
    renderer.render(wink_frame, state(34, left_eye=0.98, right_eye=0.61))

    difference = np.abs(open_frame.astype(np.int16) - wink_frame.astype(np.int16))
    assert difference[:, 640:].sum() > difference[:, :640].sum()


def test_renderer_leaves_center_neck_opening_visible() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.full((720, 1280, 3), 91, dtype=np.uint8)

    renderer.render(frame, state(1))

    assert np.all(frame[500, 640] == 91)
    assert not np.all(frame[470, 640] == 91)
    assert not np.all(frame[450, 500] == 91)


def test_neck_opening_stays_below_chin_margin_during_pitch() -> None:
    for pitch in (-45.0, 20.0):
        renderer = PS1CardboardRenderer()
        frame = np.full((720, 1280, 3), 91, dtype=np.uint8)

        renderer.render(frame, state(1, pitch=pitch))

        assert not np.all(frame[470, 640] == 91)
        assert np.all(frame[500, 640] == 91)


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


def test_combined_extreme_pose_keeps_head_inside_shell_silhouette() -> None:
    renderer = PS1CardboardRenderer()
    frame = np.full((720, 1280, 3), 91, dtype=np.uint8)

    renderer.render(frame, state(1, pitch=32.2, yaw=26.5, roll=-7.5))

    assert not np.all(frame[110, 640] == 91)
    assert not np.all(frame[470, 640] == 91)


def test_roll_rotates_complete_shell_around_face_center() -> None:
    tilted_left = np.zeros((720, 1280, 3), dtype=np.uint8)
    tilted_right = np.zeros((720, 1280, 3), dtype=np.uint8)

    PS1CardboardRenderer().render(tilted_left, state(1, roll=35.0))
    PS1CardboardRenderer().render(tilted_right, state(1, roll=-35.0))

    assert np.count_nonzero(tilted_left[40:180, 640:960]) > np.count_nonzero(
        tilted_left[40:180, 320:640]
    )
    assert np.count_nonzero(tilted_right[40:180, 320:640]) > np.count_nonzero(
        tilted_right[40:180, 640:960]
    )
