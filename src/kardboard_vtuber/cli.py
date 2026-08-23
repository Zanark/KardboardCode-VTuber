"""Command-line camera preview and diagnostics."""

from __future__ import annotations

import argparse
import math
import signal
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from numpy import ndarray

from kardboard_vtuber.camera import (
    CameraBackend,
    CameraConfig,
    CameraRotation,
    CameraSource,
    CaptureState,
)
from kardboard_vtuber.camera.stream import LatestFrameCamera

if TYPE_CHECKING:
    from kardboard_vtuber.tracking.events import FaceActionDetector
    from kardboard_vtuber.tracking.full_body import MediaPipeFullBodyTracker
    from kardboard_vtuber.tracking.green_screen import MediaPipePersonSegmenter
    from kardboard_vtuber.tracking.hand_occlusion import MediaPipeHandOccluder
    from kardboard_vtuber.tracking.mediapipe_tracker import MediaPipeFaceTracker
    from kardboard_vtuber.tracking.models import FaceTrackingState


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
        "--input-already-mirrored",
        action="store_true",
        help="Treat an already-mirrored recording as anatomical without flipping it again.",
    )
    parser.add_argument(
        "--brightness",
        type=_brightness_offset,
        default=12,
        help="Brightness offset applied before tracking and preview, from 0 to 100 (default: 12).",
    )
    parser.add_argument(
        "--track-face",
        action="store_true",
        help="Run MediaPipe Face Landmarker without adding visual diagnostics.",
    )
    parser.add_argument(
        "--tracking-debug",
        action="store_true",
        help="Show the face mesh, pose inset, action labels, and camera diagnostic text.",
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
        "--render-cardboard",
        action="store_true",
        help="Overlay the low-resolution PS1-style KardboardCode box on the tracked face.",
    )
    parser.add_argument(
        "--cardboard-renderer",
        choices=("textured-3d", "procedural-2d"),
        default="textured-3d",
        help="Cardboard renderer used with --render-cardboard (default: textured-3d).",
    )
    parser.add_argument(
        "--box-depth-offset",
        type=_box_depth_offset,
        default=0.16,
        help=(
            "Perspective Z offset for the textured box; positive moves it backward "
            "without an upper cap (default: 0.16, use 0 to restore the previous position)."
        ),
    )
    parser.add_argument(
        "--physics",
        action="store_true",
        help="Enable spring-driven hinge physics on every cardboard flap.",
    )
    parser.add_argument(
        "--debug-face-preview",
        action="store_true",
        help="Show an opt-in raw live face crop at the top center of the preview.",
    )
    parser.add_argument(
        "--hand-occlusion",
        action="store_true",
        help="Composite detected hand/forearm pixels over the avatar for AR-style occlusion.",
    )
    parser.add_argument(
        "--hand-model",
        type=Path,
        default=Path("models/hand_landmarker.task"),
        help="Path to the MediaPipe Hand Landmarker .task model.",
    )
    parser.add_argument(
        "--hand-tracking-width",
        type=int,
        default=320,
        help="Maximum frame width submitted to hand tracking (default: 320).",
    )
    parser.add_argument(
        "--green-screen",
        action="store_true",
        help="Keep the detected person and replace the background with pure chroma green.",
    )
    parser.add_argument(
        "--segmentation-model",
        type=Path,
        default=Path("models/selfie_segmenter.tflite"),
        help="Path to the MediaPipe Selfie Segmenter .tflite model.",
    )
    parser.add_argument(
        "--segmentation-width",
        type=int,
        default=384,
        help="Maximum frame width submitted to person segmentation (default: 384).",
    )
    parser.add_argument(
        "--full-body",
        action="store_true",
        help=(
            "Render a pose-driven full body beneath the cardboard head and open "
            "a separate 33-point skeleton window."
        ),
    )
    parser.add_argument(
        "--pose-model",
        type=Path,
        default=Path("models/pose_landmarker_lite.task"),
        help="Path to the MediaPipe Pose Landmarker .task model.",
    )
    parser.add_argument(
        "--pose-tracking-width",
        type=int,
        default=480,
        help="Maximum frame width submitted to full-body pose tracking (default: 480).",
    )
    parser.add_argument(
        "--preview-height",
        type=_preview_height,
        help=(
            "Resize only the displayed preview to this maximum height; "
            "processing stays full-size."
        ),
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
    if args.hand_occlusion and not (args.render_cardboard or args.full_body):
        print("--hand-occlusion requires --render-cardboard or --full-body", file=sys.stderr)
        return 2
    if args.physics and args.cardboard_renderer != "textured-3d":
        print("--physics requires --cardboard-renderer textured-3d", file=sys.stderr)
        return 2
    source = CameraSource.parse(args.source)
    recorded_file = isinstance(source.value, str) and Path(source.value).is_file()
    config = CameraConfig(
        source=source,
        backend=CameraBackend(args.backend),
        requested_width=args.width,
        requested_height=args.height,
        requested_fps=args.fps,
        rotation=CameraRotation(args.rotate),
        mirror=args.mirror,
        realtime_playback=recorded_file,
        stop_at_end=recorded_file,
    )
    camera = LatestFrameCamera(config)
    try:
        tracker = (
            _create_tracker(args)
            if args.track_face
            or args.render_cardboard
            or args.debug_face_preview
            or args.full_body
            or args.physics
            or args.tracking_debug
            else None
        )
        hand_occluder = _create_hand_occluder(args) if args.hand_occlusion else None
        person_segmenter = _create_person_segmenter(args) if args.green_screen else None
        body_tracker = _create_full_body_tracker(args) if args.full_body else None
        action_detector = _create_action_detector(args) if tracker is not None else None
        renderer = (
            _create_renderer(args)
            if args.render_cardboard or args.full_body or args.physics
            else None
        )
        if args.full_body:
            from kardboard_vtuber.renderer import FullBodyAvatarRenderer

            body_renderer = FullBodyAvatarRenderer()
        else:
            body_renderer = None
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    started_at = time.monotonic()
    last_sequence: int | None = None
    last_report_at = 0.0
    latest_action: str | None = None
    window_name = "KardboardCode Camera Preview"
    skeleton_window_name = "KardboardCode Full Body Skeleton"
    shutdown = _ShutdownSignal()
    previous_sigint_handler = signal.signal(signal.SIGINT, shutdown)

    try:
        camera.start()
        while not shutdown.requested:
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
                if snapshot.state is CaptureState.STOPPED and last_sequence is not None:
                    break
                continue

            last_sequence = packet.sequence
            camera_frame = _apply_brightness(packet.frame, args.brightness)
            if hand_occluder is not None:
                hand_occluder.submit(camera_frame, packet.captured_at_ns)
                hand_state = hand_occluder.snapshot()
            if person_segmenter is not None:
                person_segmenter.submit(camera_frame, packet.captured_at_ns)
                segmentation_state = person_segmenter.snapshot()
            if body_tracker is not None:
                body_tracker.submit(camera_frame, packet.captured_at_ns)
                body_state = body_tracker.snapshot()
            if tracker is not None:
                tracker.submit(camera_frame, packet.captured_at_ns)
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
                if body_tracker is not None:
                    _print_full_body_snapshot(body_tracker)
                last_report_at = now

            if not args.headless:
                frame = camera_frame
                if person_segmenter is not None:
                    from kardboard_vtuber.tracking.green_screen import apply_green_screen

                    apply_green_screen(
                        frame,
                        segmentation_state,
                        current_timestamp_ms=packet.captured_at_ns // 1_000_000,
                        config=person_segmenter.config,
                    )
                foreground_source = (
                    frame.copy()
                    if args.debug_face_preview or hand_occluder is not None
                    else None
                )
                if tracker is not None:
                    from kardboard_vtuber.tracking.mediapipe_tracker import draw_tracking_debug

                    tracking_state = tracker.snapshot().state
                    if body_renderer is not None:
                        body_renderer.render(frame, body_state, tracking_state)
                    if renderer is not None:
                        renderer.render(frame, tracking_state)
                        if hand_occluder is not None and foreground_source is not None:
                            from kardboard_vtuber.tracking.hand_occlusion import (
                                composite_hand_foreground,
                            )

                            composite_hand_foreground(frame, foreground_source, hand_state)
                    if args.tracking_debug:
                        draw_tracking_debug(
                            frame,
                            tracking_state,
                            action=latest_action,
                            draw_frame_geometry=renderer is None,
                        )
                    if args.debug_face_preview and foreground_source is not None:
                        _draw_debug_face_preview(frame, foreground_source, tracking_state)
                if args.tracking_debug:
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
                display_frame = (
                    _resize_preview(frame, args.preview_height)
                    if args.preview_height is not None
                    else frame
                )
                cv2.imshow(window_name, display_frame)
                if body_tracker is not None:
                    from kardboard_vtuber.tracking.full_body import (
                        render_pose_skeleton_debug,
                    )

                    cv2.imshow(
                        skeleton_window_name,
                        render_pose_skeleton_debug(body_state),
                    )
                key = cv2.waitKey(1) & 0xFF
                if key in {ord("q"), 27}:
                    break

            if args.duration is not None and now - started_at >= args.duration:
                break
    except KeyboardInterrupt:
        shutdown.request()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if renderer is not None:
            renderer.close()
        if hand_occluder is not None:
            hand_occluder.close()
        if person_segmenter is not None:
            person_segmenter.close()
        if body_tracker is not None:
            body_tracker.close()
        if tracker is not None:
            tracker.close()
        camera.stop()
        cv2.destroyAllWindows()
        signal.signal(signal.SIGINT, previous_sigint_handler)
    return 0


class _ShutdownSignal:
    def __init__(self) -> None:
        self.requested = False

    def __call__(self, _signum: int, _frame: object | None) -> None:
        self.request()

    def request(self) -> None:
        if not self.requested:
            print("\nCtrl+C received; closing cleanly...", flush=True)
        self.requested = True


def _brightness_offset(raw: str) -> int:
    value = int(raw)
    if not 0 <= value <= 100:
        raise argparse.ArgumentTypeError("brightness must be between 0 and 100")
    return value


def _box_depth_offset(raw: str) -> float:
    value = float(raw)
    if not math.isfinite(value) or value < -1.0:
        raise argparse.ArgumentTypeError("box depth offset must be finite and at least -1")
    return value


def _preview_height(raw: str) -> int:
    value = int(raw)
    if value < 240:
        raise argparse.ArgumentTypeError("preview height must be at least 240")
    return value


def _apply_brightness(frame: ndarray, brightness: int) -> ndarray:
    if brightness == 0:
        return frame.copy()
    return cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)


def _resize_preview(frame: ndarray, maximum_height: int) -> ndarray:
    if maximum_height < 240:
        raise ValueError("--preview-height must be at least 240")
    height, width = frame.shape[:2]
    if height <= maximum_height:
        return frame
    scale = maximum_height / height
    return cv2.resize(
        frame,
        (max(1, round(width * scale)), maximum_height),
        interpolation=cv2.INTER_AREA,
    )


def _draw_debug_face_preview(
    frame: ndarray,
    source_frame: ndarray,
    state: FaceTrackingState,
) -> None:
    frame_height, frame_width = frame.shape[:2]
    panel_width = min(250, max(120, frame_width // 3))
    panel_height = round(panel_width * 1.08)
    panel_x = min(
        frame_width - panel_width - 12,
        max(12, round(frame_width * 0.44)),
    )
    panel_y = 16
    panel_bottom = min(frame_height - 1, panel_y + panel_height)
    panel_height = panel_bottom - panel_y
    if panel_height <= 0:
        return

    frame[panel_y:panel_bottom, panel_x : panel_x + panel_width] = 0
    if state.detected:
        source_height, source_width = source_frame.shape[:2]
        crop_left = max(0, round((state.center_x - state.face_width * 0.72) * source_width))
        crop_right = min(
            source_width,
            round((state.center_x + state.face_width * 0.72) * source_width),
        )
        crop_top = max(0, round((state.center_y - state.face_height * 0.90) * source_height))
        crop_bottom = min(
            source_height,
            round((state.center_y + state.face_height * 0.90) * source_height),
        )
        if crop_right > crop_left and crop_bottom > crop_top:
            crop = source_frame[crop_top:crop_bottom, crop_left:crop_right]
            crop_aspect = crop.shape[1] / crop.shape[0]
            panel_aspect = panel_width / panel_height
            if crop_aspect > panel_aspect:
                target_width = max(1, round(crop.shape[0] * panel_aspect))
                start = (crop.shape[1] - target_width) // 2
                crop = crop[:, start : start + target_width]
            else:
                target_height = max(1, round(crop.shape[1] / panel_aspect))
                start = (crop.shape[0] - target_height) // 2
                crop = crop[start : start + target_height, :]
            frame[panel_y:panel_bottom, panel_x : panel_x + panel_width] = cv2.resize(
                crop,
                (panel_width, panel_height),
                interpolation=cv2.INTER_AREA,
            )

    cv2.rectangle(
        frame,
        (panel_x, panel_y),
        (panel_x + panel_width, panel_bottom),
        (0, 0, 255),
        5,
    )
    cv2.putText(
        frame,
        "RAW FACE DEBUG",
        (panel_x + 10, panel_y + 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 165, 255),
        2,
        cv2.LINE_AA,
    )


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
            swap_eyes=args.mirror or args.input_already_mirrored,
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


def _create_hand_occluder(args: argparse.Namespace) -> MediaPipeHandOccluder:
    from kardboard_vtuber.tracking.hand_occlusion import (
        HandOcclusionConfig,
        MediaPipeHandOccluder,
    )

    return MediaPipeHandOccluder(
        HandOcclusionConfig(
            model_path=args.hand_model,
            input_width=args.hand_tracking_width,
        )
    )


def _create_full_body_tracker(args: argparse.Namespace) -> MediaPipeFullBodyTracker:
    from kardboard_vtuber.tracking.full_body import (
        FullBodyTrackerConfig,
        MediaPipeFullBodyTracker,
    )

    return MediaPipeFullBodyTracker(
        FullBodyTrackerConfig(
            model_path=args.pose_model,
            input_width=args.pose_tracking_width,
        )
    )


def _create_person_segmenter(args: argparse.Namespace) -> MediaPipePersonSegmenter:
    from kardboard_vtuber.tracking.green_screen import (
        GreenScreenConfig,
        MediaPipePersonSegmenter,
    )

    return MediaPipePersonSegmenter(
        GreenScreenConfig(
            model_path=args.segmentation_model,
            input_width=args.segmentation_width,
        )
    )


def _create_renderer(args: argparse.Namespace) -> object:
    from kardboard_vtuber.renderer import (
        CardboardRendererConfig,
        PS1CardboardRenderer,
        Textured3DCardboardRenderer,
        Textured3DRendererConfig,
    )

    if args.cardboard_renderer == "procedural-2d":
        return PS1CardboardRenderer(CardboardRendererConfig(mirrored=args.mirror))
    try:
        return Textured3DCardboardRenderer(
            Textured3DRendererConfig(
                mirrored=args.mirror,
                physics_enabled=args.physics,
                perspective_depth_offset=args.box_depth_offset,
            )
        )
    except RuntimeError as error:
        if args.physics:
            raise RuntimeError(
                f"flap physics requires the textured 3D renderer: {error}"
            ) from error
        print(
            f"3D renderer unavailable ({error}); using privacy-safe 2D fallback",
            file=sys.stderr,
        )
        return PS1CardboardRenderer(CardboardRendererConfig(mirrored=args.mirror))


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


def _print_full_body_snapshot(tracker: MediaPipeFullBodyTracker) -> None:
    state = tracker.snapshot()
    visible_landmarks = sum(
        point.visibility >= 0.35 and point.presence >= 0.35
        for point in state.landmarks
    )
    print(
        " | ".join(
            [
                f"full_body_detected={state.detected}",
                f"pose_landmarks={len(state.landmarks)}",
                f"visible_landmarks={visible_landmarks}",
            ]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
