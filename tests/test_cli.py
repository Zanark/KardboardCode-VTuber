from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.cli import _apply_brightness, _apply_film_grain, build_parser


def test_camera_brightness_defaults_to_mild_lift() -> None:
    args = build_parser().parse_args([])

    assert args.brightness == 12


def test_camera_brightness_is_applied_before_consumers() -> None:
    frame = np.array([[[0, 100, 250]]], dtype=np.uint8)

    adjusted = _apply_brightness(frame, 12)

    assert adjusted.tolist() == [[[12, 112, 255]]]
    assert frame.tolist() == [[[0, 100, 250]]]


def test_camera_brightness_rejects_out_of_range_values() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--brightness", "101"])


def test_film_grain_is_disabled_by_default() -> None:
    args = build_parser().parse_args([])

    assert args.film_grain == 0.0


def test_film_grain_changes_only_returned_display_frame() -> None:
    frame = np.full((32, 32, 3), 120, dtype=np.uint8)

    grained = _apply_film_grain(frame, 15.0, np.random.default_rng(7))

    assert not np.array_equal(grained, frame)
    assert np.all(frame == 120)
    assert np.array_equal(grained[:, :, 0], grained[:, :, 1])
    assert np.array_equal(grained[:, :, 1], grained[:, :, 2])


def test_film_grain_rejects_out_of_range_values() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--film-grain", "-1"])
