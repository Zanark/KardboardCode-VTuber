"""Generate a face-free README GIF from private tracking telemetry."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import median

import cv2
import numpy as np

from kardboard_vtuber.renderer.textured_3d import (
    Textured3DCardboardRenderer,
    Textured3DRendererConfig,
)
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose

BACKGROUND = (23, 17, 13)
PRIMARY_TEXT = (235, 237, 230)
SECONDARY_TEXT = (160, 148, 139)
STAGE_ORDER = (
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
    "combined",
)
STAGE_LABELS = {
    "neutral": "NEUTRAL",
    "yaw_right": "TURN RIGHT",
    "yaw_left": "TURN LEFT",
    "look_up": "LOOK UP",
    "look_down": "LOOK DOWN",
    "roll_left": "LEAN LEFT",
    "roll_right": "LEAN RIGHT",
    "blink": "BLINK",
    "left_wink": "LEFT WINK",
    "right_wink": "RIGHT WINK",
    "combined": "COMBINED MOTION",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--telemetry",
        type=Path,
        required=True,
        help="Private guided-regression CSV. Only numeric tracking values are read.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/images/kardboardcode-live-demo.gif"),
    )
    parser.add_argument("--frames-per-stage", type=int, default=7)
    parser.add_argument("--frame-duration-ms", type=int, default=150)
    return parser


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as telemetry_file:
        rows = [
            row
            for row in csv.DictReader(telemetry_file)
            if row["detected"].strip().lower() == "true"
        ]
    if not rows:
        raise ValueError(f"telemetry contains no detected face states: {path}")
    return rows


def _sample_stage(rows: list[dict[str, str]], stage: str, count: int) -> list[dict[str, str]]:
    stage_rows = [row for row in rows if row["stage"] == stage]
    if not stage_rows:
        return []
    start = len(stage_rows) // 8
    end = max(start + 1, len(stage_rows) - len(stage_rows) // 8)
    candidates = stage_rows[start:end]
    indices = np.linspace(0, len(candidates) - 1, count, dtype=np.int32)
    return [candidates[index] for index in indices]


def _tracking_state(
    row: dict[str, str],
    *,
    timestamp_ms: int,
    median_center_x: float,
    median_center_y: float,
    median_width: float,
    median_height: float,
) -> FaceTrackingState:
    source_width = float(row["face_width"])
    source_height = float(row["face_height"])
    return FaceTrackingState(
        timestamp_ms=timestamp_ms,
        detected=True,
        landmarks=(),
        center_x=0.31
        + _clamp((float(row["center_x"]) - median_center_x) * 0.24, -0.045, 0.045),
        center_y=0.61
        + _clamp((float(row["center_y"]) - median_center_y) * 0.18, -0.035, 0.035),
        face_width=_clamp(0.125 * source_width / median_width, 0.105, 0.145),
        face_height=_clamp(0.105 * source_height / median_height, 0.09, 0.125),
        left_eye_open=_clamp(float(row["filtered_left_eye"]), 0.0, 1.0),
        right_eye_open=_clamp(float(row["filtered_right_eye"]), 0.0, 1.0),
        mouth_open=_clamp(float(row["filtered_mouth"]), 0.0, 1.0),
        head_pose=HeadPose(
            translation_x=0.0,
            translation_y=0.0,
            translation_z=0.0,
            pitch_degrees=_clamp(float(row["filtered_pitch"]), -42.0, 42.0),
            yaw_degrees=_clamp(float(row["filtered_yaw"]), -55.0, 55.0),
            roll_degrees=_clamp(float(row["filtered_roll"]), -32.0, 32.0),
        ),
    )


def _draw_copy(frame: np.ndarray, row: dict[str, str], frame_index: int, total: int) -> None:
    cv2.putText(
        frame,
        "KARDBOARDCODE LIVE",
        (455, 72),
        cv2.FONT_HERSHEY_DUPLEX,
        1.02,
        PRIMARY_TEXT,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        STAGE_LABELS.get(row["stage"], row["stage"].upper()),
        (458, 112),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.66,
        (80, 255, 80),
        2,
        cv2.LINE_AA,
    )
    pose = (
        f"pitch {float(row['filtered_pitch']):+.0f}  "
        f"yaw {float(row['filtered_yaw']):+.0f}  "
        f"roll {float(row['filtered_roll']):+.0f}"
    )
    cv2.putText(
        frame,
        pose,
        (458, 144),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        SECONDARY_TEXT,
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "REAL TRACKED MOTION",
        (458, 190),
        cv2.FONT_HERSHEY_DUPLEX,
        0.58,
        PRIMARY_TEXT,
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "SYNTHETIC RENDER ONLY",
        (458, 218),
        cv2.FONT_HERSHEY_DUPLEX,
        0.58,
        PRIMARY_TEXT,
        1,
        cv2.LINE_AA,
    )
    progress_width = 280
    progress = round(progress_width * (frame_index + 1) / total)
    cv2.rectangle(frame, (458, 246), (458 + progress_width, 252), (55, 55, 55), -1)
    cv2.rectangle(frame, (458, 246), (458 + progress, 252), (80, 255, 80), -1)
    cv2.putText(
        frame,
        "No camera pixels are stored in this GIF",
        (18, 428),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        SECONDARY_TEXT,
        1,
        cv2.LINE_AA,
    )


def generate_animation(
    telemetry_path: Path,
    output_path: Path,
    *,
    frames_per_stage: int,
    frame_duration_ms: int,
) -> None:
    if frames_per_stage < 2:
        raise ValueError("frames_per_stage must be at least 2")
    if frame_duration_ms <= 0:
        raise ValueError("frame_duration_ms must be positive")
    rows = _read_rows(telemetry_path)
    selected = [
        row
        for stage in STAGE_ORDER
        for row in _sample_stage(rows, stage, frames_per_stage)
    ]
    selected.extend(_sample_stage(rows, "neutral", frames_per_stage))
    if not selected:
        raise ValueError("telemetry does not contain any configured animation stages")

    median_center_x = median(float(row["center_x"]) for row in rows)
    median_center_y = median(float(row["center_y"]) for row in rows)
    median_width = median(float(row["face_width"]) for row in rows)
    median_height = median(float(row["face_height"]) for row in rows)
    renderer = Textured3DCardboardRenderer(
        Textured3DRendererConfig(physics_enabled=True)
    )
    frames: list[np.ndarray] = []
    try:
        for frame_index, row in enumerate(selected):
            frame = np.full((450, 800, 3), BACKGROUND, dtype=np.uint8)
            tracking_state = _tracking_state(
                row,
                timestamp_ms=frame_index * frame_duration_ms + 1,
                median_center_x=median_center_x,
                median_center_y=median_center_y,
                median_width=median_width,
                median_height=median_height,
            )
            renderer.render(frame, tracking_state)
            _draw_copy(frame, row, frame_index, len(selected))
            frames.append(frame)
    finally:
        renderer.close()

    animation = cv2.Animation()
    animation.frames = frames
    animation.durations = [frame_duration_ms] * len(frames)
    animation.loop_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parameters = (
        cv2.IMWRITE_GIF_DITHER,
        cv2.IMWRITE_GIF_FAST_FLOYD_DITHER,
        cv2.IMWRITE_GIF_QUALITY,
        cv2.IMWRITE_GIF_COLORTABLE_SIZE_128,
    )
    if not cv2.imwriteanimation(str(output_path), animation, parameters):
        raise RuntimeError(f"could not write README animation: {output_path}")
    print(
        f"{output_path}: {len(frames)} frames, "
        f"{frame_duration_ms} ms/frame, {output_path.stat().st_size} bytes"
    )


def main() -> None:
    args = build_parser().parse_args()
    generate_animation(
        args.telemetry,
        args.output,
        frames_per_stage=args.frames_per_stage,
        frame_duration_ms=args.frame_duration_ms,
    )


if __name__ == "__main__":
    main()
