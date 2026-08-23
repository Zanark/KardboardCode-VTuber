"""Generate a text-free real-life GIF with the user's face fully covered."""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from kardboard_vtuber.renderer.textured_3d import (
    Textured3DCardboardRenderer,
    Textured3DRendererConfig,
)
from kardboard_vtuber.tracking.green_screen import (
    GreenScreenConfig,
    PersonSegmentationState,
    apply_green_screen,
)
from kardboard_vtuber.tracking.models import HeadPose, normalize_face


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--telemetry", type=Path, required=True)
    parser.add_argument(
        "--face-model",
        type=Path,
        default=Path("models/face_landmarker.task"),
    )
    parser.add_argument(
        "--output",
        type=Path,
    )
    parser.add_argument("--green-screen", action="store_true")
    parser.add_argument(
        "--segmentation-model",
        type=Path,
        default=Path("models/selfie_segmenter.tflite"),
    )
    parser.add_argument("--frames-per-stage", type=int, default=4)
    parser.add_argument("--frame-duration-ms", type=int, default=180)
    parser.add_argument("--brightness", type=int, default=12)
    return parser


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as telemetry_file:
        return list(csv.DictReader(telemetry_file))


def _sample_indices(rows: list[dict[str, str]], count: int) -> list[int]:
    selected: list[int] = []
    for stage in dict.fromkeys(row["stage"] for row in rows):
        stage_indices = [
            index
            for index, row in enumerate(rows)
            if row["stage"] == stage and row["detected"].strip().lower() == "true"
        ]
        if not stage_indices:
            continue
        trim = len(stage_indices) // 8
        candidates = stage_indices[trim : len(stage_indices) - trim or None]
        offsets = np.linspace(0, len(candidates) - 1, count, dtype=np.int32)
        selected.extend(candidates[offset] for offset in offsets)
    return sorted(set(selected))


def _create_landmarker(model_path: Path) -> tuple[object, object]:
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Face Landmarker model not found at {model_path}. "
            "Run: python scripts/download_face_landmarker_model.py"
        )
    try:
        import mediapipe as mp
    except ImportError as error:
        raise RuntimeError("MediaPipe is required; install the tracking extra.") from error

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path.resolve())),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
    )
    return mp, mp.tasks.vision.FaceLandmarker.create_from_options(options)


def _create_segmenter(mp: object, model_path: Path) -> object:
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Selfie Segmenter model not found at {model_path}. "
            "Run: python scripts/download_selfie_segmenter_model.py"
        )
    options = mp.tasks.vision.ImageSegmenterOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path.resolve())),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        output_confidence_masks=True,
        output_category_mask=False,
    )
    return mp.tasks.vision.ImageSegmenter.create_from_options(options)


def _segment_person(
    mp: object,
    segmenter: object,
    frame: np.ndarray,
    timestamp_ms: int,
    config: GreenScreenConfig,
) -> PersonSegmentationState:
    height, width = frame.shape[:2]
    segmentation_frame = frame
    if width > config.input_width:
        scale = config.input_width / width
        segmentation_frame = cv2.resize(
            frame,
            (config.input_width, max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    frame_rgb = cv2.cvtColor(segmentation_frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame_rgb))
    result = segmenter.segment_for_video(image, timestamp_ms)
    if not result.confidence_masks:
        return PersonSegmentationState.empty(timestamp_ms)
    mask = np.asarray(result.confidence_masks[0].numpy_view(), dtype=np.float32).copy()
    mask = np.squeeze(mask)
    if mask.ndim != 2:
        raise ValueError(f"person segmentation mask must be 2D, got {mask.shape}")
    return PersonSegmentationState(
        timestamp_ms=timestamp_ms,
        person_mask=np.clip(mask, 0.0, 1.0),
    )


def _tracked_state(
    mp: object,
    landmarker: object,
    frame: np.ndarray,
    row: dict[str, str],
    timestamp_ms: int,
    brightness: int,
):
    tracking_frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)
    frame_rgb = cv2.cvtColor(tracking_frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame_rgb))
    result = landmarker.detect_for_video(image, timestamp_ms)
    if not result.face_landmarks:
        return None, tracking_frame
    blendshapes = result.face_blendshapes[0] if result.face_blendshapes else ()
    matrices = result.facial_transformation_matrixes
    normalized = normalize_face(
        timestamp_ms=timestamp_ms,
        landmarks=result.face_landmarks[0],
        blendshapes=blendshapes,
        transformation_matrix=matrices[0] if matrices else None,
        swap_eyes=True,
    )
    state = replace(
        normalized,
        face_width=normalized.face_width * 1.05,
        face_height=normalized.face_height * 1.05,
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
    return state, tracking_frame


def _landmarks_are_covered(mask_frame: np.ndarray, state) -> bool:
    covered = np.any(mask_frame != 0, axis=2)
    height, width = covered.shape
    hits = 0
    for landmark in state.landmarks:
        x = _clamp(landmark.x * width, 0, width - 1)
        y = _clamp(landmark.y * height, 0, height - 1)
        x1 = max(0, round(x) - 3)
        x2 = min(width, round(x) + 4)
        y1 = max(0, round(y) - 3)
        y2 = min(height, round(y) + 4)
        hits += int(np.any(covered[y1:y2, x1:x2]))
    return hits / max(len(state.landmarks), 1) >= 0.98


def _apply_head_safety_mask(frame: np.ndarray, state) -> None:
    height, width = frame.shape[:2]
    face_width = state.face_width * width
    face_height = state.face_height * height
    backdrop = tuple(
        int(channel)
        for channel in np.median(frame[: max(1, height // 10)], axis=(0, 1))
    )
    center = (
        round(state.center_x * width),
        round((state.center_y - state.face_height * 0.22) * height),
    )
    axes = (
        max(1, round(face_width * 0.85)),
        max(1, round(face_height * 1.20)),
    )
    cv2.ellipse(frame, center, axes, 0, 0, 360, backdrop, cv2.FILLED)


def generate_animation(
    video_path: Path,
    telemetry_path: Path,
    model_path: Path,
    output_path: Path,
    *,
    frames_per_stage: int,
    frame_duration_ms: int,
    brightness: int,
    green_screen: bool,
    segmentation_model_path: Path,
) -> None:
    if frames_per_stage < 2:
        raise ValueError("frames_per_stage must be at least 2")
    if frame_duration_ms <= 0:
        raise ValueError("frame_duration_ms must be positive")
    if not 0 <= brightness <= 100:
        raise ValueError("brightness must be between 0 and 100")
    rows = _read_rows(telemetry_path)
    selected_indices = _sample_indices(rows, frames_per_stage)
    selected_set = set(selected_indices)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"could not open video: {video_path}")
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    if abs(frame_count - len(rows)) > 1:
        raise ValueError(
            f"video/telemetry mismatch: {frame_count} frames versus {len(rows)} rows"
        )

    mp, landmarker = _create_landmarker(model_path)
    green_screen_config = GreenScreenConfig(model_path=segmentation_model_path)
    segmenter = (
        _create_segmenter(mp, segmentation_model_path) if green_screen else None
    )
    demo_config = Textured3DRendererConfig(
        box_width_multiplier=1.85,
        box_height_multiplier=1.80,
        upward_bias=0.0,
    )
    renderer = Textured3DCardboardRenderer(
        replace(demo_config, physics_enabled=True)
    )
    privacy_renderer = Textured3DCardboardRenderer(demo_config)
    frames: list[np.ndarray] = []
    try:
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index not in selected_set:
                frame_index += 1
                continue
            timestamp_ms = max(1, round(frame_index * 1000.0 / fps))
            state, visible_frame = _tracked_state(
                mp,
                landmarker,
                frame,
                rows[frame_index],
                timestamp_ms,
                brightness,
            )
            if state is None:
                frame_index += 1
                continue
            privacy_mask = np.zeros_like(visible_frame)
            privacy_renderer.render(privacy_mask, state)
            if not _landmarks_are_covered(privacy_mask, state):
                raise RuntimeError(f"privacy coverage failed at video frame {frame_index}")
            if segmenter is not None:
                segmentation_state = _segment_person(
                    mp,
                    segmenter,
                    visible_frame,
                    timestamp_ms,
                    green_screen_config,
                )
                apply_green_screen(
                    visible_frame,
                    segmentation_state,
                    current_timestamp_ms=timestamp_ms,
                    config=green_screen_config,
                )
            _apply_head_safety_mask(visible_frame, state)
            renderer.render(visible_frame, state)
            frames.append(
                cv2.resize(
                    visible_frame,
                    (360, 640),
                    interpolation=cv2.INTER_AREA,
                )
            )
            frame_index += 1
    finally:
        capture.release()
        renderer.close()
        privacy_renderer.close()
        landmarker.close()
        if segmenter is not None:
            segmenter.close()

    if len(frames) < len(selected_indices) * 0.9:
        raise RuntimeError(
            f"too many selected frames lacked a safe face state: "
            f"{len(frames)} of {len(selected_indices)} rendered"
        )
    animation = cv2.Animation()
    animation.frames = frames
    animation.durations = [frame_duration_ms] * len(frames)
    animation.loop_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parameters = (
        cv2.IMWRITE_GIF_DITHER,
        cv2.IMWRITE_GIF_FAST_FLOYD_DITHER,
        cv2.IMWRITE_GIF_QUALITY,
        cv2.IMWRITE_GIF_COLORTABLE_SIZE_64,
    )
    if not cv2.imwriteanimation(str(output_path), animation, parameters):
        raise RuntimeError(f"could not write real-life animation: {output_path}")
    print(
        f"{output_path}: {len(frames)} frames, "
        f"{frame_duration_ms} ms/frame, {output_path.stat().st_size} bytes"
    )


def main() -> None:
    args = build_parser().parse_args()
    output_path = args.output or Path(
        "docs/images/kardboardcode-green-screen-demo.gif"
        if args.green_screen
        else "docs/images/kardboardcode-real-life-demo.gif"
    )
    generate_animation(
        args.video,
        args.telemetry,
        args.face_model,
        output_path,
        frames_per_stage=args.frames_per_stage,
        frame_duration_ms=args.frame_duration_ms,
        brightness=args.brightness,
        green_screen=args.green_screen,
        segmentation_model_path=args.segmentation_model,
    )


if __name__ == "__main__":
    main()
