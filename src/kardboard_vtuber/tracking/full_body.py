"""Asynchronous MediaPipe full-body pose tracking."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy import ndarray

POSE_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (27, 31),
    (29, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (28, 32),
    (30, 32),
)


@dataclass(frozen=True, slots=True)
class PoseLandmark:
    x: float
    y: float
    z: float
    visibility: float
    presence: float


@dataclass(frozen=True, slots=True)
class FullBodyPoseState:
    timestamp_ms: int
    landmarks: tuple[PoseLandmark, ...]

    @property
    def detected(self) -> bool:
        return len(self.landmarks) == 33

    @classmethod
    def empty(cls, timestamp_ms: int = 0) -> FullBodyPoseState:
        return cls(timestamp_ms=timestamp_ms, landmarks=())


@dataclass(frozen=True, slots=True)
class FullBodyTrackerConfig:
    model_path: Path = Path("models/pose_landmarker_lite.task")
    input_width: int = 480
    min_detection_confidence: float = 0.5
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.input_width <= 0:
            raise ValueError("pose input width must be positive")
        for name in (
            "min_detection_confidence",
            "min_presence_confidence",
            "min_tracking_confidence",
        ):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


class MediaPipeFullBodyTracker:
    """Retains the latest 33-point full-body pose from MediaPipe."""

    def __init__(self, config: FullBodyTrackerConfig) -> None:
        if not config.model_path.is_file():
            raise FileNotFoundError(
                f"Pose Landmarker model not found at {config.model_path}. "
                "Run: python scripts/download_pose_landmarker_model.py"
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
        self._state = FullBodyPoseState.empty()
        self._last_submitted_timestamp_ms = -1
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(config.model_path.resolve()),
            ),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_poses=1,
            min_pose_detection_confidence=config.min_detection_confidence,
            min_pose_presence_confidence=config.min_presence_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
            result_callback=self._on_result,
        )
        self._landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)

    def submit(self, frame_bgr: ndarray, captured_at_ns: int) -> None:
        height, width = frame_bgr.shape[:2]
        if width > self._config.input_width:
            scale = self._config.input_width / width
            frame_bgr = cv2.resize(
                frame_bgr,
                (self._config.input_width, max(1, round(height * scale))),
                interpolation=cv2.INTER_AREA,
            )
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        timestamp_ms = captured_at_ns // 1_000_000
        with self._lock:
            timestamp_ms = max(timestamp_ms, self._last_submitted_timestamp_ms + 1)
            self._last_submitted_timestamp_ms = timestamp_ms
        image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(frame_rgb),
        )
        self._landmarker.detect_async(image, timestamp_ms)

    def snapshot(self) -> FullBodyPoseState:
        with self._lock:
            return self._state

    def close(self) -> None:
        self._landmarker.close()

    def _on_result(self, result: Any, _output_image: Any, timestamp_ms: int) -> None:
        if not result.pose_landmarks:
            state = FullBodyPoseState.empty(timestamp_ms)
        else:
            landmarks = tuple(
                PoseLandmark(
                    x=float(point.x),
                    y=float(point.y),
                    z=float(point.z),
                    visibility=float(point.visibility or 0.0),
                    presence=float(point.presence or 0.0),
                )
                for point in result.pose_landmarks[0]
            )
            state = FullBodyPoseState(timestamp_ms=timestamp_ms, landmarks=landmarks)
        with self._lock:
            self._state = state


def render_pose_skeleton_debug(
    state: FullBodyPoseState,
    *,
    width: int = 360,
    height: int = 480,
) -> ndarray:
    """Render all visible pose points and connections on a black diagnostic canvas."""

    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(
        canvas,
        "33-POINT BODY SKELETON",
        (12, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (80, 255, 80),
        1,
        cv2.LINE_AA,
    )
    if not state.detected:
        cv2.putText(
            canvas,
            "NO FULL BODY",
            (12, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (60, 60, 255),
            2,
            cv2.LINE_AA,
        )
        return canvas

    visible = [
        index
        for index, point in enumerate(state.landmarks)
        if point.visibility >= 0.35 and point.presence >= 0.35
    ]
    if not visible:
        return canvas
    source_points = np.asarray(
        [(state.landmarks[index].x, state.landmarks[index].y) for index in visible],
        dtype=np.float64,
    )
    minimum = source_points.min(axis=0)
    maximum = source_points.max(axis=0)
    span = np.maximum(maximum - minimum, 1e-4)
    padding = np.asarray((34.0, 46.0))
    usable = np.asarray((width, height), dtype=np.float64) - padding * 2.0
    scale = min(usable[0] / span[0], usable[1] / span[1])
    offset = padding + (usable - span * scale) / 2.0

    points: dict[int, tuple[int, int]] = {}
    for index in visible:
        landmark = state.landmarks[index]
        projected = (np.asarray((landmark.x, landmark.y)) - minimum) * scale + offset
        points[index] = (round(projected[0]), round(projected[1]))

    for start, end in POSE_CONNECTIONS:
        if start in points and end in points:
            cv2.line(canvas, points[start], points[end], (180, 120, 255), 2, cv2.LINE_AA)
    for index, point in points.items():
        cv2.circle(canvas, point, 4, (80, 255, 80), -1, cv2.LINE_AA)
        cv2.putText(
            canvas,
            str(index),
            (point[0] + 5, point[1] - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.28,
            (210, 210, 210),
            1,
            cv2.LINE_AA,
        )
    return canvas
