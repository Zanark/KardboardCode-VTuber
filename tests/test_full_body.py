from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.renderer.full_body import (
    FullBodyAvatarRenderer,
    FullBodyRendererConfig,
)
from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    FullBodyTrackerConfig,
    PoseLandmark,
    render_pose_skeleton_debug,
)
from tests.test_ps1_cardboard_renderer import state


def pose_state() -> FullBodyPoseState:
    coordinates = [(0.5, 0.24)] * 33
    coordinates[11] = (0.38, 0.40)
    coordinates[12] = (0.62, 0.40)
    coordinates[13] = (0.30, 0.52)
    coordinates[14] = (0.70, 0.52)
    coordinates[15] = (0.25, 0.64)
    coordinates[16] = (0.75, 0.64)
    coordinates[17] = (0.23, 0.65)
    coordinates[18] = (0.77, 0.65)
    coordinates[19] = (0.24, 0.66)
    coordinates[20] = (0.76, 0.66)
    coordinates[21] = (0.26, 0.65)
    coordinates[22] = (0.74, 0.65)
    coordinates[23] = (0.43, 0.62)
    coordinates[24] = (0.57, 0.62)
    coordinates[25] = (0.42, 0.76)
    coordinates[26] = (0.58, 0.76)
    coordinates[27] = (0.41, 0.91)
    coordinates[28] = (0.59, 0.91)
    coordinates[29] = (0.39, 0.94)
    coordinates[30] = (0.61, 0.94)
    coordinates[31] = (0.44, 0.95)
    coordinates[32] = (0.56, 0.95)
    return FullBodyPoseState(
        timestamp_ms=1,
        landmarks=tuple(
            PoseLandmark(x=x, y=y, z=0.0, visibility=1.0, presence=1.0)
            for x, y in coordinates
        ),
    )


def test_full_body_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="positive"):
        FullBodyTrackerConfig(input_width=0)
    with pytest.raises(ValueError, match="minimum_visibility"):
        FullBodyRendererConfig(minimum_visibility=1.1)


def test_skeleton_debug_renders_all_pose_landmarks_on_black() -> None:
    image = render_pose_skeleton_debug(pose_state())

    assert image.shape == (480, 360, 3)
    assert np.count_nonzero(image) > 1_000
    assert np.count_nonzero(np.all(image == (80, 255, 80), axis=2)) >= 33


def test_full_body_renderer_draws_torso_limbs_and_neck_into_head() -> None:
    frame = np.full((720, 405, 3), 91, dtype=np.uint8)

    FullBodyAvatarRenderer().render(frame, pose_state(), state(1))

    assert np.all(frame[40, 40] == 91)
    assert not np.all(frame[430, 202] == 91)
    assert not np.all(frame[324, 202] == 91)
