"""Command-line camera preview and diagnostics."""

from __future__ import annotations

import argparse
import math
import signal
import sys
import time
from collections.abc import Callable
from contextlib import ExitStack
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
from kardboard_vtuber.runtime import LiveTuning, RuntimeBridge, RuntimeTelemetry
from kardboard_vtuber.tracking.eyes import EyeSensitivity
from kardboard_vtuber.virtual_camera import VirtualCameraConfig, VirtualCameraOutput

if TYPE_CHECKING:
    from kardboard_vtuber.renderer import PS1CardboardRenderer, Textured3DCardboardRenderer
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
        help=(
            "Brightness offset applied only to internal tracking input, "
            "from 0 to 100 (default: 12)."
        ),
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
        "--blink-threshold",
        type=_unit_interval,
        default=0.35,
        help="Both eyes must be at or below this openness to blink (default: 0.35).",
    )
    parser.add_argument(
        "--wink-threshold",
        type=_unit_interval,
        default=0.70,
        help="A winked eye must be at or below this openness (default: 0.70).",
    )
    parser.add_argument(
        "--left-blink-threshold", type=_unit_interval,
        help="Anatomical left-eye blink override; defaults to --blink-threshold.",
    )
    parser.add_argument(
        "--right-blink-threshold", type=_unit_interval,
        help="Anatomical right-eye blink override; defaults to --blink-threshold.",
    )
    parser.add_argument(
        "--eye-open-threshold",
        type=_unit_interval,
        default=0.65,
        help="The opposite eye must be at or above this openness for a wink (default: 0.65).",
    )
    parser.add_argument(
        "--wink-min-difference",
        type=_unit_interval,
        default=0.15,
        help="Minimum openness difference between eyes for a wink (default: 0.15).",
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
            "Track the body and open a separate 33-point line-skeleton window "
            "without compositing a body onto the camera preview."
        ),
    )
    parser.add_argument(
        "--body-head-fallback",
        action="store_true",
        help=(
            "Keep the cardboard head attached to a shoulder-derived pose when face "
            "tracking is lost. Automatically enables cardboard, face, and body-pose tracking."
        ),
    )
    parser.add_argument(
        "--hood-marker-tracking",
        action="store_true",
        help=(
            "Track green anatomical-left and blue anatomical-right hood squares. "
            "Body-only tracking with no side marker is treated as a rear view."
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
        "--virtual-camera",
        action="store_true",
        help=(
            "Send the clean cardboard composite directly to OBS Virtual Camera "
            "(requires the virtual-camera extra and installed OBS camera component)."
        ),
    )
    parser.add_argument(
        "--virtual-camera-width",
        type=int,
        default=1280,
        help="Virtual-camera output width; positive even number (default: 1280).",
    )
    parser.add_argument(
        "--virtual-camera-height",
        type=int,
        default=720,
        help="Virtual-camera output height; positive even number (default: 720).",
    )
    parser.add_argument(
        "--virtual-camera-fps",
        type=float,
        default=30.0,
        help="Virtual-camera advertised FPS, from 1 to 60 (default: 30).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help=(
            "Do not open preview windows. With --virtual-camera, continue rendering "
            "and sending the clean camera output."
        ),
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Exit after this many seconds. By default, run until Q or Escape.",
    )
    return parser


def validate_options(
    args: argparse.Namespace,
    *,
    inspect_source: bool = True,
) -> tuple[CameraConfig, VirtualCameraConfig | None]:
    """Validate shared CLI/GUI settings before allocating native resources."""
    virtual_camera_config = None
    if args.virtual_camera:
        args.render_cardboard = True
        virtual_camera_config = VirtualCameraConfig(
            width=args.virtual_camera_width,
            height=args.virtual_camera_height,
            fps=args.virtual_camera_fps,
        )
    if args.body_head_fallback and args.hood_marker_tracking:
        raise ValueError("--body-head-fallback and --hood-marker-tracking cannot be combined")
    if args.hand_occlusion and not (
        args.render_cardboard
        or args.full_body
        or args.body_head_fallback
        or args.hood_marker_tracking
    ):
        raise ValueError(
            "--hand-occlusion requires --render-cardboard, --full-body, "
            "--body-head-fallback, or --hood-marker-tracking"
        )
    if args.physics and args.cardboard_renderer != "textured-3d":
        raise ValueError("--physics requires --cardboard-renderer textured-3d")
    live_tuning(args)
    if min(
        args.tracking_width, args.hand_tracking_width,
        args.segmentation_width, args.pose_tracking_width,
    ) <= 0:
        raise ValueError("tracking input widths must be positive")
    if args.fps is not None and (not math.isfinite(args.fps) or args.fps <= 0):
        raise ValueError("requested FPS must be finite and positive")
    if args.duration is not None and (not math.isfinite(args.duration) or args.duration < 0):
        raise ValueError("duration must be finite and nonnegative")
    try:
        source = CameraSource.parse(args.source)
    except ValueError as error:
        raise ValueError(
            f"Invalid --source: {error}. Supply a camera URL or device index. "
            "If using $env:KARDBOARD_CAMERA_URL, set it in this PowerShell session first."
        ) from error
    recorded_file = (
        inspect_source and isinstance(source.value, str) and Path(source.value).is_file()
    )
    return CameraConfig(
        source=source,
        backend=CameraBackend(args.backend),
        requested_width=args.width,
        requested_height=args.height,
        requested_fps=args.fps,
        rotation=CameraRotation(args.rotate),
        mirror=args.mirror,
        realtime_playback=recorded_file,
        stop_at_end=recorded_file,
    ), virtual_camera_config


def live_tuning(args: argparse.Namespace) -> LiveTuning:
    return LiveTuning(
        eyes=EyeSensitivity(
            args.blink_threshold
            if args.left_blink_threshold is None else args.left_blink_threshold,
            args.blink_threshold
            if args.right_blink_threshold is None else args.right_blink_threshold,
            args.eye_open_threshold, args.wink_threshold, args.wink_min_difference,
        ),
        brightness=args.brightness,
        action_hold_ms=args.action_hold_ms,
        eye_hold_ms=args.eye_action_hold_ms,
    )


def main(argv: list[str] | None = None, *, runtime: RuntimeBridge | None = None) -> int:
    args = build_parser().parse_args(argv)

    def report(message: str, *, error: bool = False) -> None:
        if runtime is not None:
            runtime.log(message)
        else:
            print(message, file=sys.stderr if error else sys.stdout, flush=True)

    try:
        config, virtual_camera_config = validate_options(args)
    except ValueError as error:
        report(str(error), error=True)
        return 2
    camera = LatestFrameCamera(config)
    resources = ExitStack()
    resources.callback(camera.stop)
    try:
        tracker = (
            _create_tracker(args)
            if args.track_face
            or args.render_cardboard
            or args.debug_face_preview
            or args.full_body
            or args.body_head_fallback
            or args.hood_marker_tracking
            or args.physics
            or args.tracking_debug
            else None
        )
        if tracker is not None:
            resources.callback(tracker.close)
        hand_occluder = _create_hand_occluder(args) if args.hand_occlusion else None
        if hand_occluder is not None:
            resources.callback(hand_occluder.close)
        person_segmenter = _create_person_segmenter(args) if args.green_screen else None
        if person_segmenter is not None:
            resources.callback(person_segmenter.close)
        body_tracker = (
            _create_full_body_tracker(args)
            if args.full_body or args.body_head_fallback or args.hood_marker_tracking
            else None
        )
        if body_tracker is not None:
            resources.callback(body_tracker.close)
        if args.body_head_fallback:
            from kardboard_vtuber.tracking import BodyHeadFallback

            body_head_fallback = BodyHeadFallback()
        else:
            body_head_fallback = None
        if args.hood_marker_tracking:
            from kardboard_vtuber.tracking import HoodMarkerHeadTracker

            hood_marker_tracker = HoodMarkerHeadTracker()
        else:
            hood_marker_tracker = None
        action_detector = _create_action_detector(args) if tracker is not None else None
        renderer = (
            (_create_renderer(args) if runtime is None else _create_renderer(args, report=report))
            if (
                args.render_cardboard
                or args.full_body
                or args.body_head_fallback
                or args.hood_marker_tracking
                or args.physics
            )
            else None
        )
        if renderer is not None:
            resources.callback(renderer.close)
    except (OSError, RuntimeError, ValueError) as error:
        resources.close()
        report(str(error), error=True)
        return 1
    except BaseException:
        resources.close()
        raise
    started_at = time.monotonic()
    last_sequence: int | None = None
    last_report_at = 0.0
    latest_action: str | None = None
    window_name = "KardboardCode Camera Preview"
    skeleton_window_name = "KardboardCode Full Body Skeleton"
    shutdown = _ShutdownSignal()
    previous_sigint_handler = (
        signal.signal(signal.SIGINT, shutdown) if runtime is None else None
    )
    virtual_camera: VirtualCameraOutput | None = None
    current_tuning = live_tuning(args)
    last_unavailable_at = -math.inf

    try:
        if runtime is not None and runtime.stop_event.is_set():
            return 0
        if args.virtual_camera:
            assert virtual_camera_config is not None
            virtual_camera = VirtualCameraOutput(virtual_camera_config)
            resources.callback(virtual_camera.close)
            report(
                f"virtual_camera={virtual_camera.device} | "
                f"output={virtual_camera_config.width}x{virtual_camera_config.height}"
                f"@{virtual_camera_config.fps:g} | clean_composite=True",
            )
        if runtime is not None and runtime.stop_event.is_set():
            return 0
        camera.start()
        while not shutdown.requested and not (
            runtime is not None and runtime.stop_event.is_set()
        ):
            if runtime is not None:
                tuning = runtime.tuning()
                if tuning != current_tuning:
                    if action_detector is not None:
                        action_detector.set_thresholds(tuning.action_thresholds())
                    if renderer is not None:
                        renderer.set_eye_sensitivity(tuning.eyes)
                    current_tuning = tuning
            packet = camera.read(
                after_sequence=last_sequence, timeout=0.1 if runtime is not None else 2.0,
                copy=False,
            )
            now = time.monotonic()
            if packet is None:
                if virtual_camera is not None:
                    virtual_camera.repeat()
                snapshot = camera.snapshot()
                if now - last_unavailable_at >= 2.0:
                    report(
                        f"camera unavailable: state={snapshot.state.value} "
                        f"error={snapshot.last_error}", error=True,
                    )
                    last_unavailable_at = now
                if snapshot.state.value == "failed":
                    return 1
                if snapshot.state is CaptureState.STOPPED and last_sequence is not None:
                    break
                if args.duration is not None and now - started_at >= args.duration:
                    break
                continue

            last_sequence = packet.sequence
            processing_frame = _apply_brightness(packet.frame, current_tuning.brightness)
            if hand_occluder is not None:
                hand_occluder.submit(processing_frame, packet.captured_at_ns)
                hand_state = hand_occluder.snapshot()
            if person_segmenter is not None:
                person_segmenter.submit(processing_frame, packet.captured_at_ns)
                segmentation_state = person_segmenter.snapshot()
            if body_tracker is not None:
                body_tracker.submit(processing_frame, packet.captured_at_ns)
                body_state = body_tracker.snapshot()
            if tracker is not None:
                tracker.submit(processing_frame, packet.captured_at_ns)
                face_snapshot = tracker.snapshot()
                tracking_state = face_snapshot.state
                from kardboard_vtuber.tracking.eyes import render_eye_state

                render_tracking_state = render_eye_state(tracking_state, face_snapshot.raw_state)
                if virtual_camera is not None or runtime is not None:
                    from kardboard_vtuber.tracking.models import FaceTrackingState

                    timestamp_ms = packet.captured_at_ns // 1_000_000
                    if not 0 <= timestamp_ms - tracking_state.timestamp_ms <= 500:
                        render_tracking_state = FaceTrackingState.no_face(timestamp_ms)
                if hood_marker_tracker is not None:
                    render_tracking_state = hood_marker_tracker.update(
                        processing_frame,
                        timestamp_ms=packet.captured_at_ns // 1_000_000,
                        face=render_tracking_state,
                        pose=body_state,
                    )
                elif body_head_fallback is not None:
                    render_tracking_state = body_head_fallback.update(
                        render_tracking_state,
                        body_state,
                        current_timestamp_ms=packet.captured_at_ns // 1_000_000,
                    )
                if action_detector is not None:
                    events = action_detector.update(face_snapshot.raw_state)
                    if events:
                        latest_action = events[0].action.value
                    for event in events:
                        report(event.format_log())
            if now - last_report_at >= 2.0:
                if runtime is None:
                    _print_snapshot(camera)
                    if tracker is not None:
                        _print_tracking_snapshot(tracker)
                    if body_tracker is not None:
                        _print_full_body_snapshot(body_tracker)
                else:
                    _print_snapshot(camera, emit=report)
                    if tracker is not None:
                        _print_tracking_snapshot(tracker, emit=report)
                    if body_tracker is not None:
                        _print_full_body_snapshot(body_tracker, emit=report)
                if body_head_fallback is not None:
                    report(
                        "body_head_fallback_ready="
                        f"{body_head_fallback.calibration_ready} | "
                        f"calibration_samples={body_head_fallback.calibration_samples}/"
                        f"{body_head_fallback.required_calibration_samples}",
                    )
                if hood_marker_tracker is not None:
                    marker_snapshot = hood_marker_tracker.snapshot()
                    colors = ",".join(
                        observation.color.value
                        for observation in marker_snapshot.observations
                    )
                    report(
                        f"hood_markers={colors or 'none'} | "
                        f"hood_tracking_source={marker_snapshot.source.value} | "
                        f"marker_head_detected={marker_snapshot.head_state.detected}",
                    )
                last_report_at = now

            if not args.headless or virtual_camera is not None:
                frame = packet.frame.copy()
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
                    calibration_hold = (
                        body_head_fallback is not None
                        and not body_head_fallback.calibration_ready
                        and not render_tracking_state.detected
                    )
                    if calibration_hold:
                        body_head_fallback.render_calibration_hold(
                            frame,
                            body_state,
                            current_timestamp_ms=(
                                packet.captured_at_ns // 1_000_000
                            ),
                            show_status=runtime is None and virtual_camera is None,
                        )
                    else:
                        if renderer is not None:
                            renderer.render(frame, render_tracking_state)
                        if (
                            hand_occluder is not None
                            and foreground_source is not None
                            and render_tracking_state.detected
                        ):
                            from kardboard_vtuber.tracking.hand_occlusion import (
                                composite_hand_foreground,
                            )

                            composite_hand_foreground(
                                frame,
                                foreground_source,
                                hand_state,
                            )
                if virtual_camera is not None:
                    virtual_camera.send(frame)
            if not args.headless:
                if tracker is not None and runtime is None:
                    from kardboard_vtuber.tracking.mediapipe_tracker import draw_tracking_debug

                    if args.tracking_debug:
                        draw_tracking_debug(
                            frame,
                            tracking_state,
                            action=latest_action,
                            draw_frame_geometry=renderer is None,
                        )
                        if hood_marker_tracker is not None:
                            hood_marker_tracker.draw_debug(
                                frame,
                                hood_marker_tracker.snapshot(),
                            )
                    if args.debug_face_preview and foreground_source is not None:
                        _draw_debug_face_preview(frame, foreground_source, tracking_state)
                if args.tracking_debug and runtime is None:
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
                skeleton_frame = None
                if args.full_body:
                    from kardboard_vtuber.tracking.full_body import (
                        render_pose_skeleton_debug,
                    )

                    skeleton_frame = render_pose_skeleton_debug(body_state)
                if runtime is None:
                    cv2.imshow(window_name, display_frame)
                    if skeleton_frame is not None:
                        cv2.imshow(skeleton_window_name, skeleton_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in {ord("q"), 27}:
                        break
            if runtime is not None:
                from kardboard_vtuber.tracking.mediapipe_tracker import render_face_mesh_panel
                from kardboard_vtuber.tracking.models import FaceTrackingState

                camera_snapshot = camera.snapshot()
                runtime.publish(
                    None if args.headless else display_frame,
                    RuntimeTelemetry(
                        face=tracking_state if tracker is not None
                        else FaceTrackingState.no_face(),
                        raw_face=face_snapshot.raw_state if tracker is not None
                        else FaceTrackingState.no_face(),
                        effective_detected=render_tracking_state.detected
                        if tracker is not None else False,
                        camera_fps=camera_snapshot.measured_fps,
                        tracking_fps=tracker.snapshot().measured_fps
                        if tracker is not None else 0.0,
                        frame_age_ms=(time.monotonic_ns() - packet.captured_at_ns) / 1_000_000,
                        frame_size=(packet.width, packet.height),
                        capture_state=camera_snapshot.state.value,
                        action=latest_action or "",
                        output_device=virtual_camera.device if virtual_camera is not None else "",
                        masking_enabled=renderer is not None,
                        raw_preview=args.debug_face_preview,
                        calibration_status=(
                            f"BODY CALIBRATION {body_head_fallback.calibration_samples}/"
                            f"{body_head_fallback.required_calibration_samples} / FACE CAMERA"
                            if body_head_fallback is not None
                            and not body_head_fallback.calibration_ready else ""
                        ),
                        render_face=render_tracking_state if tracker is not None else None,
                    ),
                    None if args.headless else skeleton_frame,
                    clean_frame=frame if not args.headless and renderer is not None else None,
                    face_mesh=(
                        render_face_mesh_panel(tracking_state, (packet.width, packet.height))
                        if tracker is not None and args.tracking_debug and not args.headless
                        else None
                    ),
                    raw_face=(
                        _raw_face_crop(packet.frame, tracking_state)
                        if tracker is not None and args.debug_face_preview and not args.headless
                        else None
                    ),
                )

            if args.duration is not None and now - started_at >= args.duration:
                break
    except KeyboardInterrupt:
        shutdown.request()
    except RuntimeError as error:
        report(str(error), error=True)
        return 1
    finally:
        try:
            resources.close()
        finally:
            if runtime is None:
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


def _unit_interval(raw: str) -> float:
    value = float(raw)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("value must be finite and between 0 and 1")
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


def _raw_face_crop(source: ndarray, state: FaceTrackingState) -> ndarray | None:
    if not state.detected:
        return None
    height, width = source.shape[:2]
    left = max(0, round((state.center_x - state.face_width * 0.72) * width))
    right = min(width, round((state.center_x + state.face_width * 0.72) * width))
    top = max(0, round((state.center_y - state.face_height * 0.90) * height))
    bottom = min(height, round((state.center_y + state.face_height * 0.90) * height))
    if right <= left or bottom <= top:
        return None
    crop = source[top:bottom, left:right]
    return _resize_preview(crop, 360).copy()


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


def _print_snapshot(
    camera: LatestFrameCamera, *, emit: Callable[[str], None] = print,
) -> None:
    snapshot = camera.snapshot()
    emit(
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
    from kardboard_vtuber.tracking.events import FaceActionDetector

    return FaceActionDetector(live_tuning(args).action_thresholds())


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
            input_width=(
                args.pose_tracking_width
                if args.full_body
                else min(args.pose_tracking_width, 256)
            ),
            minimum_submit_interval_ms=0 if args.full_body else 125,
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


def _create_renderer(
    args: argparse.Namespace, *, report: Callable[..., None] | None = None,
) -> PS1CardboardRenderer | Textured3DCardboardRenderer:
    from kardboard_vtuber.renderer import (
        CardboardRendererConfig,
        PS1CardboardRenderer,
        Textured3DCardboardRenderer,
        Textured3DRendererConfig,
    )

    if args.cardboard_renderer == "procedural-2d":
        return PS1CardboardRenderer(
            CardboardRendererConfig(
                mirrored=args.mirror,
                eye_closed_threshold=args.blink_threshold,
                eye_open_threshold=args.eye_open_threshold,
                wink_closed_threshold=args.wink_threshold,
                wink_min_difference=args.wink_min_difference,
                left_eye_closed_threshold=args.left_blink_threshold,
                right_eye_closed_threshold=args.right_blink_threshold,
            )
        )
    try:
        return Textured3DCardboardRenderer(
            Textured3DRendererConfig(
                mirrored=args.mirror,
                physics_enabled=args.physics,
                perspective_depth_offset=args.box_depth_offset,
                eye_closed_threshold=args.blink_threshold,
                eye_open_threshold=args.eye_open_threshold,
                wink_closed_threshold=args.wink_threshold,
                wink_min_difference=args.wink_min_difference,
                left_eye_closed_threshold=args.left_blink_threshold,
                right_eye_closed_threshold=args.right_blink_threshold,
            )
        )
    except RuntimeError as error:
        if args.physics:
            raise RuntimeError(
                f"flap physics requires the textured 3D renderer: {error}"
            ) from error
        message = f"3D renderer unavailable ({error}); using privacy-safe 2D fallback"
        if report is None:
            print(message, file=sys.stderr)
        else:
            report(message, error=True)
        return PS1CardboardRenderer(
            CardboardRendererConfig(
                mirrored=args.mirror,
                eye_closed_threshold=args.blink_threshold,
                eye_open_threshold=args.eye_open_threshold,
                wink_closed_threshold=args.wink_threshold,
                wink_min_difference=args.wink_min_difference,
                left_eye_closed_threshold=args.left_blink_threshold,
                right_eye_closed_threshold=args.right_blink_threshold,
            )
        )


def _print_tracking_snapshot(
    tracker: MediaPipeFaceTracker, *, emit: Callable[[str], None] = print,
) -> None:
    snapshot = tracker.snapshot()
    state = snapshot.state
    emit(
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


def _print_full_body_snapshot(
    tracker: MediaPipeFullBodyTracker, *, emit: Callable[[str], None] = print,
) -> None:
    state = tracker.snapshot()
    visible_landmarks = sum(
        point.visibility >= 0.35 and point.presence >= 0.35
        for point in state.landmarks
    )
    emit(
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
