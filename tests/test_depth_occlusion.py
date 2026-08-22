from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.tracking.depth_occlusion import (
    DepthOcclusionConfig,
    DepthOcclusionState,
    _prepare_depth_input,
    build_depth_occlusion_mask,
)
from kardboard_vtuber.tracking.hand_occlusion import HandOcclusionState, build_hand_mask
from tests.test_hand_occlusion import _hand
from tests.test_ps1_cardboard_renderer import state


def test_depth_config_requires_model_multiple() -> None:
    with pytest.raises(ValueError, match="multiple of 14"):
        DepthOcclusionConfig(input_long_side=200)


def test_depth_input_preserves_portrait_aspect_with_model_multiples() -> None:
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)

    prepared = _prepare_depth_input(frame, 196)

    assert prepared.shape == (1, 3, 196, 112)
    assert prepared.dtype == np.float32


def test_near_object_connected_to_hand_is_restored_but_face_is_not() -> None:
    frame_shape = (200, 200)
    depth = np.ones(frame_shape, dtype=np.float32)
    depth[70:140, 70:135] = 1.5
    depth[35:85, 25:75] = 3.4
    face = state(1)
    face = type(face)(
        timestamp_ms=100,
        detected=True,
        landmarks=face.landmarks,
        center_x=0.5,
        center_y=0.5,
        face_width=0.5,
        face_height=0.5,
        left_eye_open=face.left_eye_open,
        right_eye_open=face.right_eye_open,
        mouth_open=face.mouth_open,
        head_pose=face.head_pose,
    )
    hands = HandOcclusionState(timestamp_ms=100, hands=(_hand(),))
    depth[build_hand_mask(frame_shape, hands) > 0] = 3.0

    mask = build_depth_occlusion_mask(
        frame_shape,
        DepthOcclusionState(timestamp_ms=100, depth=depth),
        hands,
        face,
    )

    assert mask[55, 45] == 255
    assert mask[100, 100] == 255
    assert mask[75, 125] == 0


def test_ambiguous_depth_falls_back_to_privacy_safe_hand_mask() -> None:
    depth = np.ones((200, 200), dtype=np.float32)
    hands = HandOcclusionState(timestamp_ms=100, hands=(_hand(),))

    mask = build_depth_occlusion_mask(
        (200, 200),
        DepthOcclusionState(timestamp_ms=100, depth=depth),
        hands,
        state(100),
    )

    assert mask[100, 100] == 255
    assert mask[35, 110] == 0
