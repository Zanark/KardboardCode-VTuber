"""Record a guided private regression video with synchronized tracking telemetry."""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
from numpy import ndarray

from kardboard_vtuber.camera import CameraBackend, CameraConfig, CameraRotation, CameraSource
from kardboard_vtuber.camera.stream import LatestFrameCamera
from kardboard_vtuber.tracking.events import FaceActionDetector, FaceActionEvent
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
        "--face-model",
        type=Path,
        default=Path("models/face_landmarker.task"),
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0 <= args.brightness <= 100:
        raise SystemExit("--brightness must be between 0 and 100")
    if args.countdown < 0:
        raise SystemExit("--countdown cannot be negative")

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
    detector = FaceActionDetector()
    writer: cv2.VideoWriter | None = None
    window_name = "KardboardCode Guided Regression Recording"
    last_sequence: int | None = None
    video_frame = 0

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
            preview = _brighten(packet.frame, args.brightness)
            remaining = max(0, math_ceil(args.countdown - (time.monotonic() - countdown_started)))
            _draw_instruction(preview, f"RECORDING STARTS IN {remaining}", "")
            cv2.imshow(window_name, preview)
            if cv2.waitKey(1) & 0xFF in {ord("q"), 27}:
                return 1

        with telemetry_path.open("w", newline="", encoding="utf-8") as telemetry_file:
            csv_writer = csv.DictWriter(telemetry_file, fieldnames=CSV_FIELDS)
            csv_writer.writeheader()
            recording_started = time.monotonic()
            total_duration = sum(stage.duration_seconds for stage in STAGES)

            while True:
                elapsed = time.monotonic() - recording_started
                if elapsed >= total_duration:
                    break
                packet = camera.read(after_sequence=last_sequence, timeout=2.0, copy=True)
                if packet is None:
                    continue
                last_sequence = packet.sequence
                stage, stage_remaining = _stage_at(elapsed)
                tracking_input = _brighten(packet.frame, args.brightness)
                tracker.submit(tracking_input, packet.captured_at_ns)
                snapshot = tracker.snapshot()
                raw = snapshot.raw_state
                filtered = snapshot.state
                events = detector.update(raw)

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
                    )
                )
                video_frame += 1

                preview = tracking_input.copy()
                draw_tracking_debug(preview, filtered)
                _draw_instruction(
                    preview,
                    stage.instruction,
                    f"{stage_remaining:0.1f}s  FRAME {video_frame}",
                )
                cv2.imshow(window_name, preview)
                if cv2.waitKey(1) & 0xFF in {ord("q"), 27}:
                    break
    finally:
        if writer is not None:
            writer.release()
        tracker.close()
        camera.stop()
        cv2.destroyAllWindows()

    print(f"video={video_path.resolve()}")
    print(f"telemetry={telemetry_path.resolve()}")
    print(f"frames={video_frame}")
    return 0


def _brighten(frame: ndarray, brightness: int) -> ndarray:
    return cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)


def _stage_at(elapsed: float) -> tuple[Stage, float]:
    cursor = 0.0
    for stage in STAGES:
        stage_end = cursor + stage.duration_seconds
        if elapsed < stage_end:
            return stage, stage_end - elapsed
        cursor = stage_end
    return STAGES[-1], 0.0


def _telemetry_row(
    elapsed: float,
    stage: str,
    video_frame: int,
    sequence: int,
    raw: FaceTrackingState,
    filtered: FaceTrackingState,
    events: tuple[FaceActionEvent, ...],
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
    }


def _draw_instruction(frame: ndarray, headline: str, detail: str) -> None:
    height, width = frame.shape[:2]
    cv2.rectangle(frame, (0, height - 132), (width, height), (0, 0, 0), -1)
    cv2.putText(
        frame,
        headline,
        (28, height - 76),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (80, 255, 80),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        detail,
        (28, height - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (220, 220, 220),
        2,
        cv2.LINE_AA,
    )


def math_ceil(value: float) -> int:
    return int(-(-value // 1))


if __name__ == "__main__":
    raise SystemExit(main())
