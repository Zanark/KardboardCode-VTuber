from __future__ import annotations

import numpy as np

from kardboard_vtuber.tracking.full_body import FullBodyPoseState, PoseLandmark
from scripts.record_guided_regression import (
    FULL_BODY_STAGES,
    STAGES,
    _draw_instruction,
    _recording_stages,
    _resize_preview,
    _stage_at,
    _telemetry_row,
)
from tests.test_ps1_cardboard_renderer import state


def test_guided_recording_covers_all_required_pose_and_expression_stages() -> None:
    names = {stage.name for stage in STAGES}

    assert {
        "neutral",
        "yaw_right",
        "yaw_left",
        "look_up",
        "look_down",
        "roll_left",
        "roll_right",
        "blink",
        "left_wink",
        "right_wink",
        "mouth",
        "combined",
    } == names
    assert sum(stage.duration_seconds for stage in STAGES) == 50.0


def test_guided_recording_stage_lookup_tracks_boundaries() -> None:
    assert _stage_at(0.0)[0].name == "neutral"
    assert _stage_at(4.0)[0].name == "yaw_right"
    assert _stage_at(44.0)[0].name == "combined"


def test_full_body_routine_covers_both_rotation_directions_and_occlusion() -> None:
    names = {stage.name for stage in FULL_BODY_STAGES}

    assert {
        "clockwise_right_profile",
        "clockwise_back",
        "counter_left_profile",
        "counter_back",
        "lean",
        "crouch",
        "arms_up",
        "head_occlusion",
        "free_motion",
    } <= names
    assert sum(stage.duration_seconds for stage in FULL_BODY_STAGES) == 93.0
    assert _stage_at(0.0, FULL_BODY_STAGES)[0].name == "front_neutral"
    assert _stage_at(92.0, FULL_BODY_STAGES)[0].name == "free_motion"


def test_free_recording_has_one_unguided_stage_for_requested_duration() -> None:
    stages = _recording_stages(
        full_body=True,
        free_recording=True,
        duration=75.0,
    )

    assert stages == (type(STAGES[0])("free_session", "", 75.0),)
    assert _stage_at(30.0, stages)[0].name == "free_session"


def test_telemetry_row_serializes_all_pose_landmarks() -> None:
    face = state(20)
    body = FullBodyPoseState(
        timestamp_ms=21,
        landmarks=tuple(
            PoseLandmark(0.1, 0.2, -0.3, 0.9, 0.8)
            for _ in range(33)
        ),
    )

    row = _telemetry_row(
        0.5,
        "front_neutral",
        1,
        2,
        face,
        face,
        (),
        body,
    )

    assert row["pose_timestamp_ms"] == 21
    assert row["pose_detected"] is True
    assert str(row["pose_landmarks"]).count("[") == 34


def test_guided_recording_preview_is_reduced_without_changing_aspect_ratio() -> None:
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)

    preview = _resize_preview(frame, 720)

    assert preview.shape == (720, 405, 3)


def test_guided_recording_instruction_panel_is_at_top_left() -> None:
    frame = np.full((720, 405, 3), 255, dtype=np.uint8)

    _draw_instruction(frame, "LOOK UP", "4.0s")

    assert not frame[20, 20].any()
    assert frame[-20, 20].all()
