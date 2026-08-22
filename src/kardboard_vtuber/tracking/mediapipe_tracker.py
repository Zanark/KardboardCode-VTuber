"""Asynchronous MediaPipe Face Landmarker adapter."""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy import ndarray

from kardboard_vtuber.tracking.filters import FaceMotionFilter, FaceMotionFilterConfig
from kardboard_vtuber.tracking.models import (
    FaceTrackingState,
    TrackingSnapshot,
    normalize_face,
)

_FACE_OVAL = (
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378,
    400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21,
    54, 103, 67, 109,
)
_LEFT_EYE = (263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466)
_RIGHT_EYE = (33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246)
_LEFT_BROW = (276, 283, 282, 295, 285, 300, 293, 334, 296, 336)
_RIGHT_BROW = (46, 53, 52, 65, 55, 70, 63, 105, 66, 107)
_OUTER_LIPS = (
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375,
    291, 409, 270, 269, 267, 0, 37, 39, 40, 185,
)
_INNER_LIPS = (
    78, 95, 88, 178, 87, 14, 317, 402, 318, 324,
    308, 415, 310, 311, 312, 13, 82, 81, 80, 191,
)
_NOSE_BRIDGE = (168, 6, 197, 195, 5, 4, 1, 19, 94, 2)
_NOSE_BASE = (129, 49, 48, 219, 218, 237, 44, 1, 274, 457, 438, 439, 278, 279, 358)


@dataclass(frozen=True, slots=True)
class MediaPipeTrackerConfig:
    model_path: Path = Path("models/face_landmarker.task")
    input_width: int = 640
    min_face_detection_confidence: float = 0.5
    min_face_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    swap_eyes: bool = False
    motion_filtering: bool = True
    motion_filter: FaceMotionFilterConfig = field(default_factory=FaceMotionFilterConfig)

    def __post_init__(self) -> None:
        if self.input_width <= 0:
            raise ValueError("input_width must be positive")
        for name in (
            "min_face_detection_confidence",
            "min_face_presence_confidence",
            "min_tracking_confidence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


class MediaPipeFaceTracker:
    """Submits current frames asynchronously and retains only the newest result."""

    def __init__(self, config: MediaPipeTrackerConfig) -> None:
        if not config.model_path.is_file():
            raise FileNotFoundError(
                f"Face Landmarker model not found at {config.model_path}. "
                "Run: python scripts/download_face_landmarker_model.py"
            )

        try:
            import mediapipe as mp
        except ImportError as error:
            raise RuntimeError(
                "MediaPipe is not installed. Use Python 3.12 and install .[tracking]."
            ) from error

        self._config = config
        self._mp = mp
        self._lock = threading.Lock()
        self._state = FaceTrackingState.no_face()
        self._raw_state = FaceTrackingState.no_face()
        self._submitted_frames = 0
        self._result_frames = 0
        self._detected_frames = 0
        self._last_error: str | None = None
        self._last_submitted_timestamp_ms = -1
        self._fps_window_started_ns = time.monotonic_ns()
        self._fps_window_frames = 0
        self._measured_fps = 0.0
        self._motion_filter = (
            FaceMotionFilter(config.motion_filter) if config.motion_filtering else None
        )

        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(config.model_path.resolve())),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_faces=1,
            min_face_detection_confidence=config.min_face_detection_confidence,
            min_face_presence_confidence=config.min_face_presence_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            result_callback=self._on_result,
        )
        self._landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)

    @property
    def config(self) -> MediaPipeTrackerConfig:
        return self._config

    def submit(self, frame_bgr: ndarray, captured_at_ns: int) -> None:
        frame_rgb = self._prepare_frame(frame_bgr)
        timestamp_ms = captured_at_ns // 1_000_000
        with self._lock:
            timestamp_ms = max(timestamp_ms, self._last_submitted_timestamp_ms + 1)
            self._last_submitted_timestamp_ms = timestamp_ms
            self._submitted_frames += 1

        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=frame_rgb)
        try:
            self._landmarker.detect_async(image, timestamp_ms)
        except Exception as error:
            with self._lock:
                self._last_error = f"{type(error).__name__}: {error}"
            raise

    def snapshot(self) -> TrackingSnapshot:
        with self._lock:
            return TrackingSnapshot(
                state=self._state,
                raw_state=self._raw_state,
                submitted_frames=self._submitted_frames,
                result_frames=self._result_frames,
                detected_frames=self._detected_frames,
                dropped_or_pending_frames=max(0, self._submitted_frames - self._result_frames),
                measured_fps=self._measured_fps,
                last_error=self._last_error,
            )

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> MediaPipeFaceTracker:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _prepare_frame(self, frame_bgr: ndarray) -> ndarray:
        height, width = frame_bgr.shape[:2]
        if width > self._config.input_width:
            scale = self._config.input_width / width
            frame_bgr = cv2.resize(
                frame_bgr,
                (self._config.input_width, round(height * scale)),
                interpolation=cv2.INTER_AREA,
            )
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return np.ascontiguousarray(frame_rgb)

    def _on_result(self, result: Any, _output_image: Any, timestamp_ms: int) -> None:
        try:
            if not result.face_landmarks:
                raw_state = FaceTrackingState.no_face(timestamp_ms)
            else:
                blendshapes = result.face_blendshapes[0] if result.face_blendshapes else ()
                matrices = result.facial_transformation_matrixes
                matrix = matrices[0] if matrices else None
                raw_state = normalize_face(
                    timestamp_ms=timestamp_ms,
                    landmarks=result.face_landmarks[0],
                    blendshapes=blendshapes,
                    transformation_matrix=matrix,
                    swap_eyes=self._config.swap_eyes,
                )
            state = (
                self._motion_filter.filter(raw_state)
                if self._motion_filter is not None
                else raw_state
            )
            now_ns = time.monotonic_ns()
            with self._lock:
                self._raw_state = raw_state
                self._state = state
                self._result_frames += 1
                if state.detected:
                    self._detected_frames += 1
                self._fps_window_frames += 1
                elapsed = (now_ns - self._fps_window_started_ns) / 1_000_000_000
                if elapsed >= 1.0:
                    self._measured_fps = self._fps_window_frames / elapsed
                    self._fps_window_started_ns = now_ns
                    self._fps_window_frames = 0
                self._last_error = None
        except Exception as error:
            with self._lock:
                self._last_error = f"{type(error).__name__}: {error}"


def draw_tracking_debug(
    frame: ndarray,
    state: FaceTrackingState,
    *,
    action: str | None = None,
    draw_frame_geometry: bool = True,
) -> None:
    """Draw sparse landmarks, face bounds, expression bars, and pose values."""

    height, width = frame.shape[:2]
    _draw_face_mesh_inset(frame, state)
    if not state.detected:
        cv2.putText(
            frame,
            "FACE: not detected",
            (16, 64),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (60, 60, 255),
            2,
            cv2.LINE_AA,
        )
        return

    if draw_frame_geometry:
        for landmark in state.landmarks[::8]:
            point = (round(landmark.x * width), round(landmark.y * height))
            cv2.circle(frame, point, 1, (255, 180, 40), -1, cv2.LINE_AA)

        x1 = round((state.center_x - state.face_width / 2) * width)
        y1 = round((state.center_y - state.face_height / 2) * height)
        x2 = round((state.center_x + state.face_width / 2) * width)
        y2 = round((state.center_y + state.face_height / 2) * height)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 255, 80), 2)

    pose = state.head_pose
    label = (
        f"L-eye {state.left_eye_open:.2f}  R-eye {state.right_eye_open:.2f}  "
        f"mouth {state.mouth_open:.2f}"
    )
    pose_label = (
        f"pitch {pose.pitch_degrees:+.1f}  yaw {pose.yaw_degrees:+.1f}  "
        f"roll {pose.roll_degrees:+.1f}"
    )
    cv2.putText(
        frame,
        label,
        (16, 64),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (80, 255, 80),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        pose_label,
        (16, 92),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (80, 255, 80),
        2,
        cv2.LINE_AA,
    )
    if action is not None:
        cv2.putText(
            frame,
            f"ACTION = {action.replace('_', ' ').upper()}",
            (16, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (80, 255, 80),
            2,
            cv2.LINE_AA,
        )


def _draw_face_mesh_inset(frame: ndarray, state: FaceTrackingState) -> None:
    frame_height, frame_width = frame.shape[:2]
    inset_width = min(max(220, round(frame_width * 0.30)), 420, frame_width - 32)
    inset_height = min(round(inset_width * 0.85), max(120, frame_height // 3))
    origin_x = frame_width - inset_width - 16
    origin_y = 16
    x2 = origin_x + inset_width
    y2 = origin_y + inset_height
    cv2.rectangle(frame, (origin_x, origin_y), (x2, y2), (0, 0, 0), -1)
    cv2.rectangle(frame, (origin_x, origin_y), (x2, y2), (80, 255, 80), 2)
    cv2.putText(
        frame,
        "FACE MESH DEBUG",
        (origin_x + 10, origin_y + 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (80, 255, 80),
        1,
        cv2.LINE_AA,
    )
    if not state.detected or not state.landmarks:
        cv2.putText(
            frame,
            "NO FACE",
            (origin_x + 10, origin_y + 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (60, 60, 255),
            2,
            cv2.LINE_AA,
        )
        return

    axis_area_width = min(96, max(72, inset_width // 4))
    padding_left = axis_area_width + 12
    padding_right = 18
    padding_top = 34
    padding_bottom = 14
    usable_width = inset_width - padding_left - padding_right
    usable_height = inset_height - padding_top - padding_bottom
    face_width_px = state.face_width * frame_width
    face_height_px = state.face_height * frame_height
    scale = min(
        usable_width / max(face_width_px, 1e-6),
        usable_height / max(face_height_px, 1e-6),
    )
    center_px = (
        origin_x + padding_left + usable_width / 2,
        origin_y + padding_top + usable_height / 2,
    )

    def point(index: int) -> tuple[int, int]:
        landmark = state.landmarks[index]
        return (
            round(center_px[0] + (landmark.x - state.center_x) * frame_width * scale),
            round(center_px[1] + (landmark.y - state.center_y) * frame_height * scale),
        )

    groups = (
        (_FACE_OVAL, (80, 255, 80)),
        (_LEFT_EYE, (255, 180, 40)),
        (_RIGHT_EYE, (255, 180, 40)),
        (_LEFT_BROW, (200, 130, 255)),
        (_RIGHT_BROW, (200, 130, 255)),
        (_OUTER_LIPS, (80, 100, 255)),
        (_INNER_LIPS, (80, 100, 255)),
        (_NOSE_BRIDGE, (255, 220, 80)),
        (_NOSE_BASE, (255, 220, 80)),
    )
    if len(state.landmarks) >= 478:
        for indices, color in groups:
            _draw_closed_path(frame, indices, point, color)

    for landmark in state.landmarks[::12]:
        px = round(center_px[0] + (landmark.x - state.center_x) * frame_width * scale)
        py = round(center_px[1] + (landmark.y - state.center_y) * frame_height * scale)
        cv2.circle(frame, (px, py), 1, (120, 120, 120), -1, cv2.LINE_AA)

    _draw_pose_axis_gizmo(
        frame,
        state,
        (origin_x + axis_area_width // 2 + 6, origin_y + inset_height // 2 + 12),
        min(34, axis_area_width // 3),
    )


def _draw_pose_axis_gizmo(
    frame: ndarray,
    state: FaceTrackingState,
    origin: tuple[int, int],
    length: int,
) -> None:
    pitch = math.radians(state.head_pose.pitch_degrees)
    yaw = math.radians(state.head_pose.yaw_degrees)
    roll = math.radians(state.head_pose.roll_degrees)
    sin_pitch, cos_pitch = math.sin(pitch), math.cos(pitch)
    sin_yaw, cos_yaw = math.sin(yaw), math.cos(yaw)
    sin_roll, cos_roll = math.sin(roll), math.cos(roll)
    rotation_x = np.array(
        ((1.0, 0.0, 0.0), (0.0, cos_pitch, -sin_pitch), (0.0, sin_pitch, cos_pitch))
    )
    rotation_y = np.array(
        ((cos_yaw, 0.0, sin_yaw), (0.0, 1.0, 0.0), (-sin_yaw, 0.0, cos_yaw))
    )
    rotation_z = np.array(
        ((cos_roll, -sin_roll, 0.0), (sin_roll, cos_roll, 0.0), (0.0, 0.0, 1.0))
    )
    rotation = rotation_z @ rotation_y @ rotation_x
    axes = (
        ("X", np.array((1.0, 0.0, 0.0)), (80, 80, 255)),
        ("Y", np.array((0.0, 1.0, 0.0)), (80, 255, 80)),
        ("Z", np.array((0.0, 0.0, 1.0)), (255, 180, 40)),
    )
    cv2.putText(
        frame,
        "POSE",
        (origin[0] - 22, origin[1] - length - 14),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )
    for label, axis, color in axes:
        vector = rotation @ axis
        end = (
            round(origin[0] + length * (vector[0] - 0.45 * vector[2])),
            round(origin[1] + length * (vector[1] - 0.45 * vector[2])),
        )
        cv2.arrowedLine(frame, origin, end, color, 2, cv2.LINE_AA, tipLength=0.22)
        cv2.putText(
            frame,
            label,
            (end[0] + 3, end[1] - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1,
            cv2.LINE_AA,
        )


def _draw_closed_path(
    frame: ndarray,
    indices: tuple[int, ...],
    point: Any,
    color: tuple[int, int, int],
) -> None:
    for start, end in zip(indices, (*indices[1:], indices[0]), strict=True):
        cv2.line(frame, point(start), point(end), color, 1, cv2.LINE_AA)
