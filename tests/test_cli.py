from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.cli import (
    _apply_brightness,
    _draw_debug_face_preview,
    _resize_preview,
    build_parser,
    main,
)
from tests.test_ps1_cardboard_renderer import state


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


def test_raw_face_preview_is_disabled_by_default() -> None:
    args = build_parser().parse_args([])

    assert not args.debug_face_preview
    assert not args.hand_occlusion
    assert args.hand_tracking_width == 320


def test_preview_height_reduces_only_display_dimensions() -> None:
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)

    preview = _resize_preview(frame, 900)

    assert preview.shape == (900, 506, 3)
    assert frame.shape == (1920, 1080, 3)


def test_preview_height_rejects_tiny_windows() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--preview-height", "100"])


def test_debug_face_preview_draws_source_crop_at_top_center() -> None:
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)
    source = np.full_like(frame, (30, 90, 150))

    _draw_debug_face_preview(frame, source, state(1))

    assert frame[40, 500].any()
    assert np.array_equal(frame[16, 480], (0, 0, 255))


def test_hand_occlusion_requires_cardboard_rendering() -> None:
    assert main(["--hand-occlusion", "--headless", "--duration", "0"]) == 2
