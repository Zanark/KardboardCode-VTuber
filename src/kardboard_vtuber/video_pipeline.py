"""Shared, Qt-free avatar processing for Studio and command-line video exports."""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from contextlib import ExitStack

from numpy import ndarray

from kardboard_vtuber import cli
from kardboard_vtuber.runtime import RuntimeBridge, RuntimeTelemetry
from kardboard_vtuber.tracking.eyes import render_eye_state
from kardboard_vtuber.tracking.green_screen import (
    GreenScreenConfig,
    MediaPipePersonSegmenter,
    apply_green_screen,
)
from kardboard_vtuber.tracking.hand_occlusion import (
    HandOcclusionConfig,
    MediaPipeHandOccluder,
    composite_hand_foreground,
)
from kardboard_vtuber.tracking.mediapipe_tracker import MediaPipeFaceTracker, MediaPipeTrackerConfig
from kardboard_vtuber.video import (
    ExportCancelled,
    VideoExportOptions,
    VideoExportResult,
    VideoProgress,
    export_video,
)

VIDEO_FIELDS = frozenset({
    "physics", "cardboard_renderer", "box_depth_offset", "tracking_width", "face_model",
    "hand_model", "segmentation_model", "brightness", "green_screen", "segmentation_width",
    "hand_occlusion", "hand_tracking_width", "no_motion_filter", "blink_threshold",
    "left_blink_threshold", "right_blink_threshold", "eye_open_threshold", "wink_threshold",
    "wink_min_difference", "action_hold_ms", "eye_action_hold_ms", "input_already_mirrored",
})


def render_avatar_video(
    args: argparse.Namespace, options: VideoExportOptions, bridge: RuntimeBridge,
    progress: Callable[[VideoProgress], None],
) -> VideoExportResult:
    options.validate()
    if bridge.stop_event.is_set():
        raise ExportCancelled()
    required = [args.face_model]
    if args.hand_occlusion:
        required.append(args.hand_model)
    if args.green_screen:
        required.append(args.segmentation_model)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError("Missing models: " + ", ".join(missing) + ". Verify them in Models.")
    bridge.log(
        "[VIDEO] Every frame, original size/timing; compatible audio streams copied. "
        + ("Lossless FFV1/MKV; large files." if options.quality == "lossless"
           else "High-quality H.264/MP4 CRF 17; this format is lossy."),
    )
    bridge.log(
        "[VIDEO] Live capture transforms, virtual output and experimental body/marker modes "
        "are not used. Input pixels are not mirrored or rotated.",
    )
    with ExitStack() as resources:
        tracker = MediaPipeFaceTracker(MediaPipeTrackerConfig(
            model_path=args.face_model, input_width=args.tracking_width,
            swap_eyes=args.input_already_mirrored, motion_filtering=not args.no_motion_filter,
            video_mode=True,
        ))
        resources.callback(tracker.close)
        if bridge.stop_event.is_set():
            raise ExportCancelled()
        renderer = cli._create_renderer(
            args, report=lambda message, **_: bridge.log(message),
        )
        resources.callback(renderer.close)
        segmenter = None
        if args.green_screen:
            segmenter = MediaPipePersonSegmenter(GreenScreenConfig(
                model_path=args.segmentation_model, input_width=args.segmentation_width,
                video_mode=True,
            ))
            resources.callback(segmenter.close)
        hands = None
        if args.hand_occlusion:
            hands = MediaPipeHandOccluder(HandOcclusionConfig(
                model_path=args.hand_model, input_width=args.hand_tracking_width,
                video_mode=True,
            ))
            resources.callback(hands.close)
        last_preview = 0.0

        def process(frame: ndarray, timestamp_ms: int) -> None:
            nonlocal last_preview
            analysis = cli._apply_brightness(frame, args.brightness)
            tracker.submit(analysis, timestamp_ms * 1_000_000)
            snapshot = tracker.snapshot()
            state = render_eye_state(snapshot.state, snapshot.raw_state)
            if segmenter is not None:
                segmenter.submit(analysis, timestamp_ms * 1_000_000)
                apply_green_screen(
                    frame, segmenter.snapshot(), current_timestamp_ms=timestamp_ms,
                    config=segmenter.config,
                )
            foreground = frame.copy() if hands is not None else None
            renderer.render(frame, state)
            if hands is not None and foreground is not None and state.detected:
                hands.submit(analysis, timestamp_ms * 1_000_000)
                composite_hand_foreground(frame, foreground, hands.snapshot())
            now = time.monotonic()
            if not args.headless and now - last_preview >= 0.1:
                bridge.publish(frame, RuntimeTelemetry(
                    face=snapshot.state, raw_face=snapshot.raw_state,
                    effective_detected=state.detected,
                    frame_size=(frame.shape[1], frame.shape[0]),
                    capture_state="processing video", action="offline export",
                    render_face=state,
                ))
                last_preview = now

        result = export_video(
            options, process, cancel=bridge.stop_event, progress=progress,
        )
        bridge.log(
            f"[VIDEO] Saved {result.frames} frames at {result.width}x{result.height}; "
            f"{result.audio_streams} audio streams copied: {result.path}",
        )
        return result
