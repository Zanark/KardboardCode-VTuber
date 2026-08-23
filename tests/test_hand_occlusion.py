from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.tracking.hand_occlusion import (
    HandOcclusionConfig,
    HandOcclusionState,
    build_hand_mask,
    composite_hand_foreground,
)


def _hand() -> tuple[tuple[float, float], ...]:
    return (
        (0.50, 0.72),
        (0.43, 0.62),
        (0.40, 0.53),
        (0.38, 0.44),
        (0.36, 0.35),
        (0.46, 0.56),
        (0.45, 0.42),
        (0.45, 0.29),
        (0.45, 0.18),
        (0.51, 0.54),
        (0.51, 0.38),
        (0.51, 0.24),
        (0.51, 0.12),
        (0.56, 0.56),
        (0.57, 0.42),
        (0.58, 0.30),
        (0.59, 0.20),
        (0.61, 0.60),
        (0.64, 0.49),
        (0.66, 0.40),
        (0.68, 0.32),
    )


def test_hand_occlusion_config_rejects_invalid_width() -> None:
    with pytest.raises(ValueError, match="width"):
        HandOcclusionConfig(input_width=0)


def test_hand_mask_covers_palm_fingers_and_forearm() -> None:
    state = HandOcclusionState(timestamp_ms=1, hands=(_hand(),))

    mask = build_hand_mask((200, 200), state)

    assert mask[100, 100] == 255
    assert mask[35, 90] == 255
    assert mask[170, 100] == 255
    assert mask[35, 110] == 0


def test_hand_foreground_is_restored_over_rendered_avatar() -> None:
    rendered = np.zeros((200, 200, 3), dtype=np.uint8)
    source = np.full_like(rendered, (20, 80, 160))
    state = HandOcclusionState(timestamp_ms=1, hands=(_hand(),))

    composite_hand_foreground(rendered, source, state)

    assert np.array_equal(rendered[100, 100], source[100, 100])
    assert not rendered[10, 10].any()
