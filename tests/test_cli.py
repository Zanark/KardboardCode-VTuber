from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.cli import _apply_brightness, build_parser


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
