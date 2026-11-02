from __future__ import annotations

import json
from pathlib import Path

import pytest

from kardboard_vtuber.cli import build_parser, live_tuning
from kardboard_vtuber.gui import settings
from scripts.record_guided_regression import build_parser as recording_parser


def test_every_cli_option_has_a_native_control_and_roundtrips() -> None:
    controls = [field.name for fields in settings.PAGES.values() for field in fields]
    assert len(controls) == len(set(controls))
    assert set(controls) == set(settings.parser_actions())
    values = settings.defaults()
    args = build_parser().parse_args(settings.arguments(values))
    assert args.render_cardboard and args.physics
    assert live_tuning(args).eyes.left_closed == 0.35


def test_preset_keeps_current_source_and_drops_raw_consent(tmp_path: Path) -> None:
    values = dict(
        settings.defaults(),
        source="rtsp://user:synthetic@invalid/video",
        debug_face_preview=True,
        left_blink_threshold=0.21,
    )
    path = tmp_path / "preset.json"
    settings.save_preset(path, values)
    payload = path.read_text()
    assert "synthetic" not in payload and '"source"' not in payload
    assert "debug_face_preview" not in payload
    current = dict(settings.defaults(), source="4", debug_face_preview=True)
    loaded = settings.load_preset(path, current)
    assert loaded["source"] == "4" and loaded["debug_face_preview"] is False
    assert loaded["left_blink_threshold"] == 0.21


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("brightness", "90"),
        ("mirror", "false"),
        ("tracking_width", True),
        ("virtual_camera_fps", float("nan")),
        ("left_blink_threshold", 0.8),
    ],
)
def test_presets_reject_wrong_types_and_invalid_values(
    tmp_path: Path,
    name: str,
    value: object,
) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schemaVersion": 1, "options": {name: value}}))
    with pytest.raises(ValueError):
        settings.load_preset(path, settings.defaults())


def test_command_copy_never_contains_actual_camera_source() -> None:
    values = dict(settings.defaults(), source="rtsp://private.example/camera?token=synthetic")
    command = settings.command_preview(values)
    assert "private.example" not in command and "synthetic" not in command
    assert "$env:KARDBOARD_CAMERA_URL" in command


def test_recording_options_reach_the_existing_recorder(tmp_path: Path) -> None:
    options = settings.RecordingOptions(
        full_body=True,
        free_recording=True,
        duration=12,
        pose_tracking_width=256,
        pose_tracking_fps=8,
        output_dir=str(tmp_path),
        name="safe-test",
    )
    args = recording_parser().parse_args(options.arguments(settings.defaults(), tmp_path / "stop"))
    assert args.free_recording and args.full_body
    assert args.duration == 12 and args.pose_tracking_fps == 8
    assert args.output_dir == tmp_path
    assert args.stop_file == tmp_path / "stop"


def test_recording_name_cannot_escape_output_folder(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="filename stem"):
        settings.RecordingOptions(name="..\\escape").arguments(
            settings.defaults(), tmp_path / "stop"
        )
