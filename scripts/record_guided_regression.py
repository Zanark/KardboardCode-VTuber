"""Record a guided private regression video with synchronized tracking telemetry."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
from numpy import ndarray

from kardboard_vtuber.camera import CameraBackend, CameraConfig, CameraRotation, CameraSource
from kardboard_vtuber.camera.stream import LatestFrameCamera
from kardboard_vtuber.tracking.events import FaceActionDetector, FaceActionEvent
from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    FullBodyTrackerConfig,
    MediaPipeFullBodyTracker,
    render_pose_skeleton_debug,
)
from kardboard_vtuber.tracking.mediapipe_tracker import (
    MediaPipeFaceTracker,
    MediaPipeTrackerConfig,
    draw_tracking_debug,
)
from kardboard_vtuber.tracking.models import FaceTrackingState


@dataclass(frozen=True, slots=True)
class Stage:
    name: str
    instruction: str
    duration_seconds: float


STAGES = (
    Stage("neutral", "LOOK STRAIGHT / RELAX", 4.0),
    Stage("yaw_right", "SLOWLY TURN TO YOUR RIGHT", 4.0),
    Stage("yaw_left", "SLOWLY TURN TO YOUR LEFT", 4.0),
    Stage("look_up", "SLOWLY LOOK UP", 4.0),
    Stage("look_down", "SLOWLY LOOK DOWN", 4.0),
    Stage("roll_left", "TILT HEAD LEFT", 4.0),
    Stage("roll_right", "TILT HEAD RIGHT", 4.0),
    Stage("blink", "BLINK TWICE", 4.0),
    Stage("left_wink", "WINK LEFT EYE", 4.0),
    Stage("right_wink", "WINK RIGHT EYE", 4.0),
    Stage("mouth", "OPEN AND CLOSE MOUTH TWICE", 4.0),
    Stage("combined", "COMBINE TURNS / TILTS / EXPRESSIONS", 6.0),
)

FULL_BODY_STAGES = (
    Stage("front_neutral", "FACE FRONT / ARMS RELAXED", 5.0),
    Stage("clockwise_right_quarter", "TURN RIGHT TO 45 DEGREES", 4.0),
    Stage("clockwise_right_profile", "CONTINUE TO RIGHT PROFILE", 4.0),
    Stage("clockwise_back", "CONTINUE UNTIL BACK FACES CAMERA", 5.0),
    Stage("back_hold_clockwise", "HOLD BACK VIEW / ARMS RELAXED", 4.0),
    Stage("clockwise_left_profile", "CONTINUE TO LEFT PROFILE", 5.0),
    Stage("clockwise_front", "COMPLETE TURN TO FACE FRONT", 5.0),
    Stage("front_reset", "HOLD FRONT / RESET POSTURE", 3.0),
    Stage("counter_left_quarter", "TURN LEFT TO 45 DEGREES", 4.0),
    Stage("counter_left_profile", "CONTINUE TO LEFT PROFILE", 4.0),
    Stage("counter_back", "CONTINUE UNTIL BACK FACES CAMERA", 5.0),
    Stage("back_hold_counter", "HOLD BACK VIEW / ARMS RELAXED", 4.0),
    Stage("counter_right_profile", "CONTINUE TO RIGHT PROFILE", 5.0),
    Stage("counter_front", "COMPLETE TURN TO FACE FRONT", 5.0),
    Stage("lean", "LEAN LEFT / CENTER / RIGHT / CENTER", 6.0),
    Stage("crouch", "CROUCH SLOWLY / HOLD / STAND", 6.0),
    Stage("arms_up", "RAISE BOTH ARMS / LOWER THEM", 5.0),
    Stage("head_occlusion", "MOVE HANDS AROUND HOOD AND HEAD", 6.0),
    Stage("free_motion", "FREE SLOW TURNS / LEANS / CROUCH", 8.0),
)

CSV_FIELDS = (
    "elapsed_seconds",
    "stage",
    "video_frame",
    "sequence",
    "timestamp_ms",
    "detected",
    "center_x",
    "center_y",
    "face_width",
    "face_height",
    "raw_left_eye",
    "raw_right_eye",
    "raw_mouth",
    "raw_pitch",
    "raw_yaw",
    "raw_roll",
    "filtered_left_eye",
    "filtered_right_eye",
    "filtered_mouth",
    "filtered_pitch",
    "filtered_yaw",
    "filtered_roll",
    "actions",
    "pose_timestamp_ms",
    "pose_detected",
    "pose_landmarks",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Camera index or authenticated stream URL.")
    parser.add_argument(
        "--backend",
        choices=[backend.value for backend in CameraBackend],
        default=CameraBackend.AUTO.value,
    )
    parser.add_argument(
        "--rotate",
        choices=[rotation.value for rotation in CameraRotation],
        default=CameraRotation.NONE.value,
    )
    parser.add_argument("--mirror", action="store_true")
    parser.add_argument("--brightness", type=int, default=12)
    parser.add_argument("--tracking-width", type=int, default=640)
    parser.add_argument(
        "--full-body",
        action="store_true",
        help="Record 33-point pose telemetry and open the body-skeleton preview.",
    )
    parser.add_argument(
        "--free-recording",
        action="store_true",
        help="Record without guided stages; only show elapsed and remaining time.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        help="Free-recording duration in seconds (default: 60).",
    )
    parser.add_argument(
        "--face-model",
        type=Path,
        default=Path("models/face_landmarker.task"),
    )
    parser.add_argument(
        "--pose-model",
        type=Path,
        default=Path("models/pose_landmarker_lite.task"),
    )
    parser.add_argument("--pose-tracking-width", type=int, default=320)
    parser.add_argument(
        "--pose-tracking-fps",
        type=float,
        default=10.0,
        help="Maximum pose submissions per second during full-body recording.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("recordings"),
    )
    parser.add_argument(
        "--name",
        default="KardboardCode-canonical-regression",
        help="Output filename stem; a timestamp is appended.",
    )
    parser.add_argument("--countdown", type=float, default=3.0)
    parser.add_argument(
        "--preview-height",
        type=int,
        default=720,
        help="Maximum preview window height in pixels; saved video keeps full resolution.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0 <= args.brightness <= 100:
        raise SystemExit("--brightness must be between 0 and 100")
    if args.countdown < 0:
        raise SystemExit("--countdown cannot be negative")
    if args.preview_height < 240:
        raise SystemExit("--preview-height must be at least 240")
    if args.pose_tracking_width <= 0:
        raise SystemExit("--pose-tracking-width must be positive")
    if args.pose_tracking_fps <= 0:
        raise SystemExit("--pose-tracking-fps must be positive")
    if args.duration <= 0:
        raise SystemExit("--duration must be positive")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = f"{args.name}-{timestamp}"
    video_path = args.output_dir / f"{stem}.mp4"
    telemetry_path = args.output_dir / f"{stem}.csv"

    camera = LatestFrameCamera(
        CameraConfig(
            source=CameraSource.parse(args.source),
            backend=CameraBackend(args.backend),
            rotation=CameraRotation(args.rotate),
            mirror=args.mirror,
        )
    )
    tracker = MediaPipeFaceTracker(
        MediaPipeTrackerConfig(
            model_path=args.face_model,
            input_width=args.tracking_width,
            swap_eyes=args.mirror,
        )
    )
    body_tracker = (
        MediaPipeFullBodyTracker(
            FullBodyTrackerConfig(
                model_path=args.pose_model,
                input_width=args.pose_tracking_width,
                minimum_submit_interval_ms=round(1000.0 / args.pose_tracking_fps),
            )
        )
        if args.full_body
        else None
    )
    detector = FaceActionDetector()
    writer: cv2.VideoWriter | None = None
    window_name = (
        "KardboardCode Free Recording"
        if args.free_recording
        else "KardboardCode Guided Regression Recording"
    )
    last_sequence: int | None = None
    video_frame = 0
    stages = _recording_stages(args.full_body, args.free_recording, args.duration)
    skeleton_window_name = "KardboardCode Recording Body Skeleton"

    try:
        camera.start()
        first = camera.read(timeout=5.0, copy=True)
        if first is None:
            raise RuntimeError("camera did not provide a frame within five seconds")
        fps = camera.snapshot().negotiated_fps
        if not fps or fps <= 0:
            fps = 30.0
        writer = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (first.width, first.height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"could not create video writer for {video_path}")

        countdown_started = time.monotonic()
        while time.monotonic() - countdown_started < args.countdown:
            packet = camera.read(after_sequence=last_sequence, timeout=2.0, copy=True)
            if packet is None:
                continue
            last_sequence = packet.sequence
            preview = _resize_preview(
                _brighten(packet.frame, args.brightness),
                args.preview_height,
            )
            remaining = max(0, math.ceil(args.countdown - (time.monotonic() - countdown_started)))
            _draw_instruction(preview, f"RECORDING STARTS IN {remaining}", "")
            cv2.imshow(window_name, preview)
            if cv2.waitKey(1) & 0xFF in {ord("q"), 27}:
                return 1

        with telemetry_path.open("w", newline="", encoding="utf-8") as telemetry_file:
            csv_writer = csv.DictWriter(telemetry_file, fieldnames=CSV_FIELDS)
            csv_writer.writeheader()
            recording_started = time.monotonic()
            total_duration = sum(stage.duration_seconds for stage in stages)

            while True:
                elapsed = time.monotonic() - recording_started
                if elapsed >= total_duration:
                    break
                packet = camera.read(after_sequence=last_sequence, timeout=2.0, copy=True)
                if packet is None:
                    continue
                last_sequence = packet.sequence
                stage, stage_remaining = _stage_at(elapsed, stages)
                tracking_input = _brighten(packet.frame, args.brightness)
                tracker.submit(tracking_input, packet.captured_at_ns)
                snapshot = tracker.snapshot()
                raw = snapshot.raw_state
                filtered = snapshot.state
                events = detector.update(raw)
                if body_tracker is not None:
                    body_tracker.submit(tracking_input, packet.captured_at_ns)
                    body_state = body_tracker.snapshot()
                else:
                    body_state = FullBodyPoseState.empty(
                        packet.captured_at_ns // 1_000_000
                    )

                writer.write(packet.frame)
                csv_writer.writerow(
                    _telemetry_row(
                        elapsed,
                        stage.name,
                        video_frame,
                        packet.sequence,
                        raw,
                        filtered,
                        events,
                        body_state,
                    )
                )
                video_frame += 1

                preview = _resize_preview(tracking_input, args.preview_height)
                draw_tracking_debug(preview, filtered)
                _draw_instruction(
                    preview,
                    "FREE RECORDING" if args.free_recording else stage.instruction,
                    f"{stage_remaining:0.1f}s  FRAME {video_frame}",
                )
                cv2.imshow(window_name, preview)
                if body_tracker is not None:
                    cv2.imshow(
                        skeleton_window_name,
                        render_pose_skeleton_debug(body_state),
                    )
                if cv2.waitKey(1) & 0xFF in {ord("q"), 27}:
                    break
    finally:
        if writer is not None:
            writer.release()
        if body_tracker is not None:
            body_tracker.close()
        tracker.close()
        camera.stop()
        cv2.destroyAllWindows()

    print(f"video={video_path.resolve()}")
    print(f"telemetry={telemetry_path.resolve()}")
    print(f"frames={video_frame}")
    print(f"routine={'full-body' if args.full_body else 'face'}")
    print(f"guided={not args.free_recording}")
    return 0


def _brighten(frame: ndarray, brightness: int) -> ndarray:
    return cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)


def _resize_preview(frame: ndarray, maximum_height: int) -> ndarray:
    height, width = frame.shape[:2]
    if height <= maximum_height:
        return frame.copy()
    scale = maximum_height / height
    return cv2.resize(
        frame,
        (max(1, round(width * scale)), maximum_height),
        interpolation=cv2.INTER_AREA,
    )


def _stage_at(
    elapsed: float,
    stages: tuple[Stage, ...] = STAGES,
) -> tuple[Stage, float]:
    cursor = 0.0
    for stage in stages:
        stage_end = cursor + stage.duration_seconds
        if elapsed < stage_end:
            return stage, stage_end - elapsed
        cursor = stage_end
    return stages[-1], 0.0


def _recording_stages(
    full_body: bool,
    free_recording: bool,
    duration: float,
) -> tuple[Stage, ...]:
    if free_recording:
        return (Stage("free_session", "", duration),)
    return FULL_BODY_STAGES if full_body else STAGES


def _telemetry_row(
    elapsed: float,
    stage: str,
    video_frame: int,
    sequence: int,
    raw: FaceTrackingState,
    filtered: FaceTrackingState,
    events: tuple[FaceActionEvent, ...],
    body: FullBodyPoseState,
) -> dict[str, object]:
    return {
        "elapsed_seconds": f"{elapsed:.6f}",
        "stage": stage,
        "video_frame": video_frame,
        "sequence": sequence,
        "timestamp_ms": raw.timestamp_ms,
        "detected": raw.detected,
        "center_x": f"{filtered.center_x:.6f}",
        "center_y": f"{filtered.center_y:.6f}",
        "face_width": f"{filtered.face_width:.6f}",
        "face_height": f"{filtered.face_height:.6f}",
        "raw_left_eye": f"{raw.left_eye_open:.6f}",
        "raw_right_eye": f"{raw.right_eye_open:.6f}",
        "raw_mouth": f"{raw.mouth_open:.6f}",
        "raw_pitch": f"{raw.head_pose.pitch_degrees:.6f}",
        "raw_yaw": f"{raw.head_pose.yaw_degrees:.6f}",
        "raw_roll": f"{raw.head_pose.roll_degrees:.6f}",
        "filtered_left_eye": f"{filtered.left_eye_open:.6f}",
        "filtered_right_eye": f"{filtered.right_eye_open:.6f}",
        "filtered_mouth": f"{filtered.mouth_open:.6f}",
        "filtered_pitch": f"{filtered.head_pose.pitch_degrees:.6f}",
        "filtered_yaw": f"{filtered.head_pose.yaw_degrees:.6f}",
        "filtered_roll": f"{filtered.head_pose.roll_degrees:.6f}",
        "actions": "|".join(event.action.value for event in events),
        "pose_timestamp_ms": body.timestamp_ms,
        "pose_detected": body.detected,
        "pose_landmarks": json.dumps(
            [
                [
                    round(point.x, 7),
                    round(point.y, 7),
                    round(point.z, 7),
                    round(point.visibility, 7),
                    round(point.presence, 7),
                ]
                for point in body.landmarks
            ],
            separators=(",", ":"),
        ),
    }


def _draw_instruction(frame: ndarray, headline: str, detail: str) -> None:
    _, width = frame.shape[:2]
    margin = 12
    panel_width = max(
        1,
        min(width - (margin * 2), max(260, round(width * 0.72))),
    )
    headline_scale = _fit_text_scale(headline, panel_width - 24, 0.82, 2)
    detail_scale = _fit_text_scale(detail, panel_width - 24, 0.58, 1)
    panel_height = 94 if detail else 62
    cv2.rectangle(
        frame,
        (margin, margin),
        (margin + panel_width, margin + panel_height),
        (0, 0, 0),
        -1,
    )
    cv2.putText(
        frame,
        headline,
        (margin + 12, margin + 37),
        cv2.FONT_HERSHEY_SIMPLEX,
        headline_scale,
        (80, 255, 80),
        2,
        cv2.LINE_AA,
    )
    if detail:
        cv2.putText(
            frame,
            detail,
            (margin + 12, margin + 76),
            cv2.FONT_HERSHEY_SIMPLEX,
            detail_scale,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )


def _fit_text_scale(
    text: str,
    maximum_width: int,
    preferred_scale: float,
    thickness: int,
) -> float:
    if not text:
        return preferred_scale
    width = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        preferred_scale,
        thickness,
    )[0][0]
    if width <= maximum_width:
        return preferred_scale
    return max(0.35, preferred_scale * maximum_width / width)


if __name__ == "__main__":
    raise SystemExit(main())
