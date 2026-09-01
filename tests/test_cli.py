from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.cli import (
    _apply_brightness,
    _create_full_body_tracker,
    _draw_debug_face_preview,
    _resize_preview,
    _ShutdownSignal,
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
    assert not args.full_body
    assert not args.body_head_fallback
    assert not args.hood_marker_tracking
    assert not args.physics
    assert not args.tracking_debug
    assert not args.green_screen
    assert args.hand_tracking_width == 320
    assert args.pose_tracking_width == 480
    assert args.segmentation_width == 384
    assert args.box_depth_offset == 0.16
    assert args.blink_threshold == 0.35
    assert args.wink_threshold == 0.70
    assert args.eye_open_threshold == 0.65
    assert args.wink_min_difference == 0.15


def test_tracking_debug_is_opt_in() -> None:
    args = build_parser().parse_args(["--tracking-debug"])

    assert args.tracking_debug


def test_body_head_fallback_is_opt_in() -> None:
    args = build_parser().parse_args(["--body-head-fallback"])

    assert args.body_head_fallback


def test_hood_marker_tracking_is_opt_in() -> None:
    args = build_parser().parse_args(["--hood-marker-tracking"])

    assert args.hood_marker_tracking


def test_body_fallback_and_hood_markers_are_mutually_exclusive(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["--body-head-fallback", "--hood-marker-tracking"])

    assert exit_code == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_body_head_fallback_uses_throttled_low_resolution_pose_tracking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kardboard_vtuber.tracking import full_body

    monkeypatch.setattr(
        full_body,
        "MediaPipeFullBodyTracker",
        lambda config: config,
    )
    args = build_parser().parse_args(["--body-head-fallback"])

    config = _create_full_body_tracker(args)

    assert config.input_width == 256
    assert config.minimum_submit_interval_ms == 125


def test_full_body_mode_preserves_requested_pose_tracking_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kardboard_vtuber.tracking import full_body

    monkeypatch.setattr(
        full_body,
        "MediaPipeFullBodyTracker",
        lambda config: config,
    )
    args = build_parser().parse_args(
        ["--full-body", "--pose-tracking-width", "400"]
    )

    config = _create_full_body_tracker(args)

    assert config.input_width == 400
    assert config.minimum_submit_interval_ms == 0


def test_eye_sensitivity_thresholds_are_configurable() -> None:
    args = build_parser().parse_args(
        [
            "--blink-threshold",
            "0.25",
            "--wink-threshold",
            "0.55",
            "--eye-open-threshold",
            "0.72",
            "--wink-min-difference",
            "0.25",
        ]
    )

    assert args.blink_threshold == 0.25
    assert args.wink_threshold == 0.55
    assert args.eye_open_threshold == 0.72
    assert args.wink_min_difference == 0.25


def test_eye_sensitivity_thresholds_reject_out_of_range_values() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--blink-threshold", "-0.1"])


def test_box_depth_offset_can_restore_previous_position() -> None:
    args = build_parser().parse_args(["--box-depth-offset", "0"])

    assert args.box_depth_offset == 0.0


def test_box_depth_offset_has_no_positive_upper_cap() -> None:
    args = build_parser().parse_args(["--box-depth-offset", "25"])

    assert args.box_depth_offset == 25.0


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


def test_physics_flag_is_opt_in_and_requires_textured_renderer() -> None:
    assert build_parser().parse_args(["--physics"]).physics
    assert (
        main(
            [
                "--physics",
                "--cardboard-renderer",
                "procedural-2d",
                "--headless",
                "--duration",
                "0",
            ]
        )
        == 2
    )


def test_ctrl_c_requests_clean_shutdown_once(capsys: pytest.CaptureFixture[str]) -> None:
    shutdown = _ShutdownSignal()

    shutdown(2, None)
    shutdown(2, None)

    assert shutdown.requested
    assert capsys.readouterr().out.count("closing cleanly") == 1
