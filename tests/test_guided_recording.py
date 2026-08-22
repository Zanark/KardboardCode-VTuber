from __future__ import annotations

from scripts.record_guided_regression import STAGES, _stage_at


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
