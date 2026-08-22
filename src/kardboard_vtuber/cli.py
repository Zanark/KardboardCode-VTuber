"""Command-line camera preview and diagnostics."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2

from kardboard_vtuber.camera import CameraBackend, CameraConfig, CameraRotation, CameraSource
from kardboard_vtuber.camera.stream import LatestFrameCamera

if TYPE_CHECKING:
    from kardboard_vtuber.tracking.events import FaceActionDetector
    from kardboard_vtuber.tracking.mediapipe_tracker import MediaPipeFaceTracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kardboard-camera",
        description="Preview a local or phone-hosted camera stream with low-latency buffering.",
    )
    parser.add_argument(
        "--source",
        default="0",
        help="Local device index or URL, for example http://PHONE_IP:8080/video.",
    )
    parser.add_argument(
        "--backend",
        choices=[backend.value for backend in CameraBackend],
        default=CameraBackend.AUTO.value,
        help="OpenCV backend. Use ffmpeg for network streams if auto fails.",
    )
    parser.add_argument("--width", type=int, help="Requested capture width.")
    parser.add_argument("--height", type=int, help="Requested capture height.")
    parser.add_argument("--fps", type=float, help="Requested capture FPS.")
    parser.add_argument(
        "--rotate",
        choices=[rotation.value for rotation in CameraRotation],
        default=CameraRotation.NONE.value,
        help="Rotate frames left, right, or 180 degrees after capture.",
    )
    parser.add_argument("--mirror", action="store_true", help="Mirror frames horizontally.")
    parser.add_argument(
        "--track-face",
        action="store_true",
        help="Run MediaPipe Face Landmarker and draw a tracking debug overlay.",
    )
    parser.add_argument(
        "--face-model",
        type=Path,
        default=Path("models/face_landmarker.task"),
        help="Path to the MediaPipe Face Landmarker .task model.",
    )
    parser.add_argument(
        "--tracking-width",
        type=int,
        default=640,
        help="Maximum frame width submitted to face tracking.",
    )
    parser.add_argument(
        "--action-hold-ms",
        type=int,
        default=100,
        help="How long an expression must remain stable before an action log is emitted.",
    )
    parser.add_argument(
        "--eye-action-hold-ms",
        type=int,
        default=40,
        help="How long an eye state must remain stable before blink/wink logging.",
    )
    parser.add_argument(
        "--no-motion-filter",
        action="store_true",
        help="Disable One Euro smoothing and expose raw tracking values.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Capture and print diagnostics without opening a preview window.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Exit after this many seconds. By default, run until Q or Escape.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CameraConfig(
        source=CameraSource.parse(args.source),
        backend=CameraBackend(args.backend),
        requested_width=args.width,
        requested_height=args.height,
        requested_fps=args.fps,
        rotation=CameraRotation(args.rotate),
        mirror=args.mirror,
    )
    camera = LatestFrameCamera(config)
    try:
        tracker = _create_tracker(args) if args.track_face else None
        action_detector = _create_action_detector(args) if tracker is not None else None
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    started_at = time.monotonic()
    last_sequence: int | None = None
    last_report_at = 0.0
    latest_action: str | None = None
    window_name = "KardboardCode Camera Preview"

    try:
        camera.start()
        while True:
            packet = camera.read(after_sequence=last_sequence, timeout=2.0, copy=False)
            now = time.monotonic()
            if packet is None:
                snapshot = camera.snapshot()
                print(
                    f"camera unavailable: state={snapshot.state.value} "
                    f"error={snapshot.last_error}",
                    file=sys.stderr,
                )
                if snapshot.state.value == "failed":
                    return 1
                continue

            last_sequence = packet.sequence
            if tracker is not None:
                tracker.submit(packet.frame, packet.captured_at_ns)
                tracking_state = tracker.snapshot().raw_state
                if action_detector is not None:
                    events = action_detector.update(tracking_state)
                    if events:
                        latest_action = events[0].action.value
                    for event in events:
                        print(event.format_log(), flush=True)
            if now - last_report_at >= 2.0:
                _print_snapshot(camera)
                if tracker is not None:
                    _print_tracking_snapshot(tracker)
                last_report_at = now

            if not args.headless:
                frame = packet.frame
                if tracker is not None:
                    from kardboard_vtuber.tracking.mediapipe_tracker import draw_tracking_debug

                    draw_tracking_debug(
                        frame,
                        tracker.snapshot().state,
                        action=latest_action,
                    )
                snapshot = camera.snapshot()
                latency_ms = (time.monotonic_ns() - packet.captured_at_ns) / 1_000_000
                label = (
                    f"{packet.width}x{packet.height}  "
                    f"{snapshot.measured_fps:.1f} FPS  "
                    f"{latency_ms:.1f} ms frame age"
                )
                cv2.putText(
                    frame,
                    label,
                    (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (80, 255, 80),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in {ord("q"), 27}:
                    break

            if args.duration is not None and now - started_at >= args.duration:
                break
    except KeyboardInterrupt:
        pass
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if tracker is not None:
            tracker.close()
        camera.stop()
        cv2.destroyAllWindows()
    return 0


def _print_snapshot(camera: LatestFrameCamera) -> None:
    snapshot = camera.snapshot()
    print(
        " | ".join(
            [
                f"state={snapshot.state.value}",
                f"source={snapshot.source}",
                f"backend={snapshot.backend.value}",
                f"negotiated={snapshot.negotiated_width}x{snapshot.negotiated_height}"
                f"@{snapshot.negotiated_fps:.2f}",
                f"measured_fps={snapshot.measured_fps:.2f}",
                f"received={snapshot.received_frames}",
                f"overwritten={snapshot.overwritten_frames}",
                f"failures={snapshot.read_failures}",
                f"reconnects={snapshot.reconnects}",
            ]
        )
    )


def _create_tracker(args: argparse.Namespace) -> MediaPipeFaceTracker:
    from kardboard_vtuber.tracking.mediapipe_tracker import (
        MediaPipeFaceTracker,
        MediaPipeTrackerConfig,
    )

    return MediaPipeFaceTracker(
        MediaPipeTrackerConfig(
            model_path=args.face_model,
            input_width=args.tracking_width,
            swap_eyes=args.mirror,
            motion_filtering=not args.no_motion_filter,
        )
    )


def _create_action_detector(args: argparse.Namespace) -> FaceActionDetector:
    from kardboard_vtuber.tracking.events import ActionThresholds, FaceActionDetector

    return FaceActionDetector(
        ActionThresholds(
            hold_ms=args.action_hold_ms,
            eye_hold_ms=args.eye_action_hold_ms,
        )
    )


def _print_tracking_snapshot(tracker: MediaPipeFaceTracker) -> None:
    snapshot = tracker.snapshot()
    state = snapshot.state
    print(
        " | ".join(
            [
                f"tracking_detected={state.detected}",
                f"tracking_fps={snapshot.measured_fps:.2f}",
                f"submitted={snapshot.submitted_frames}",
                f"results={snapshot.result_frames}",
                f"pending_or_dropped={snapshot.dropped_or_pending_frames}",
                f"left_eye={state.left_eye_open:.2f}",
                f"right_eye={state.right_eye_open:.2f}",
                f"mouth={state.mouth_open:.2f}",
                f"pitch={state.head_pose.pitch_degrees:+.1f}",
                f"yaw={state.head_pose.yaw_degrees:+.1f}",
                f"roll={state.head_pose.roll_degrees:+.1f}",
                f"tracking_error={snapshot.last_error}",
            ]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
