from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.tracking.green_screen import (
    GreenScreenConfig,
    PersonSegmentationState,
    apply_green_screen,
)


def test_green_screen_preserves_person_and_replaces_background() -> None:
    frame = np.full((8, 8, 3), (20, 40, 80), dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.float32)
    mask[1:3, 1:3] = 1.0
    state = PersonSegmentationState(timestamp_ms=100, person_mask=mask)

    apply_green_screen(
        frame,
        state,
        current_timestamp_ms=110,
        config=GreenScreenConfig(person_threshold=0.5),
    )

    assert np.array_equal(frame[0, 0], (0, 255, 0))
    assert np.array_equal(frame[4, 4], (20, 40, 80))


def test_green_screen_fails_closed_without_a_fresh_mask() -> None:
    config = GreenScreenConfig(maximum_mask_age_ms=100)
    for state in (
        PersonSegmentationState.empty(),
        PersonSegmentationState(timestamp_ms=100, person_mask=np.ones((2, 2), np.float32)),
    ):
        frame = np.full((4, 4, 3), 90, dtype=np.uint8)

        apply_green_screen(frame, state, current_timestamp_ms=250, config=config)

        assert np.all(frame == (0, 255, 0))


def test_green_screen_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="input width"):
        GreenScreenConfig(input_width=0)
    with pytest.raises(ValueError, match="threshold"):
        GreenScreenConfig(person_threshold=1.1)
