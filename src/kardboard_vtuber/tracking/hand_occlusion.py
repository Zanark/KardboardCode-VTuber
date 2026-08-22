"""Asynchronous hand landmarks and foreground compositing for AR-style occlusion."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy import ndarray


@dataclass(frozen=True, slots=True)
class HandOcclusionConfig:
    model_path: Path = Path("models/hand_landmarker.task")
    input_width: int = 320
    max_hands: int = 2
    min_detection_confidence: float = 0.5
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.input_width <= 0:
            raise ValueError("hand input width must be positive")
        if self.max_hands <= 0:
            raise ValueError("max hands must be positive")
        for name in (
            "min_detection_confidence",
            "min_presence_confidence",
            "min_tracking_confidence",
        ):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class HandOcclusionState:
    timestamp_ms: int
    hands: tuple[tuple[tuple[float, float], ...], ...]

    @classmethod
    def empty(cls, timestamp_ms: int = 0) -> HandOcclusionState:
        return cls(timestamp_ms=timestamp_ms, hands=())


class MediaPipeHandOccluder:
    """Retains the latest asynchronous hand landmarks for foreground compositing."""

    def __init__(self, config: HandOcclusionConfig) -> None:
        if not config.model_path.is_file():
            raise FileNotFoundError(
                f"Hand Landmarker model not found at {config.model_path}. "
                "Run: python scripts/download_hand_landmarker_model.py"
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
        self._state = HandOcclusionState.empty()
        self._last_submitted_timestamp_ms = -1
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(config.model_path.resolve()),
            ),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=config.max_hands,
            min_hand_detection_confidence=config.min_detection_confidence,
            min_hand_presence_confidence=config.min_presence_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
            result_callback=self._on_result,
        )
        self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def submit(self, frame_bgr: ndarray, captured_at_ns: int) -> None:
        height, width = frame_bgr.shape[:2]
        if width > self._config.input_width:
            scale = self._config.input_width / width
            frame_bgr = cv2.resize(
                frame_bgr,
                (self._config.input_width, round(height * scale)),
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

    def snapshot(self) -> HandOcclusionState:
        with self._lock:
            return self._state

    def close(self) -> None:
        self._landmarker.close()

    def _on_result(self, result: Any, _output_image: Any, timestamp_ms: int) -> None:
        hands = tuple(
            tuple((float(point.x), float(point.y)) for point in landmarks)
            for landmarks in result.hand_landmarks
        )
        with self._lock:
            self._state = HandOcclusionState(timestamp_ms=timestamp_ms, hands=hands)


def composite_hand_foreground(
    rendered_frame: ndarray,
    source_frame: ndarray,
    state: HandOcclusionState,
) -> None:
    """Restore detected hand pixels over an already-rendered avatar frame."""

    if not state.hands:
        return
    mask = build_hand_mask(rendered_frame.shape[:2], state)
    cv2.copyTo(source_frame, mask, rendered_frame)


def build_hand_mask(
    frame_shape: tuple[int, int],
    state: HandOcclusionState,
) -> ndarray:
    height, width = frame_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    for hand in state.hands:
        if len(hand) < 21:
            continue
        hand_mask = np.zeros_like(mask)
        points = np.asarray(
            [
                (
                    round(min(1.0, max(0.0, x)) * (width - 1)),
                    round(min(1.0, max(0.0, y)) * (height - 1)),
                )
                for x, y in hand
            ],
            dtype=np.int32,
        )
        hull = cv2.convexHull(points)
        cv2.fillConvexPoly(hand_mask, hull, 255)

        hand_extent = max(
            int(np.ptp(points[:, 0])),
            int(np.ptp(points[:, 1])),
        )
        padding = max(3, round(hand_extent * 0.05))
        for point in points:
            cv2.circle(hand_mask, tuple(point), padding, 255, -1, cv2.LINE_AA)

        wrist = points[0].astype(np.float64)
        palm_center = (points[5].astype(np.float64) + points[17].astype(np.float64)) / 2.0
        direction = wrist - palm_center
        direction_length = float(np.linalg.norm(direction))
        wrist_width = float(np.linalg.norm(points[5] - points[17]))
        if direction_length > 1.0 and wrist_width > 1.0:
            direction /= direction_length
            perpendicular = np.asarray((-direction[1], direction[0]))
            wrist_half_width = wrist_width * 0.42
            forearm_end = wrist + direction * wrist_width * 1.2
            forearm_half_width = wrist_half_width * 1.15
            forearm = np.asarray(
                (
                    wrist - perpendicular * wrist_half_width,
                    wrist + perpendicular * wrist_half_width,
                    forearm_end + perpendicular * forearm_half_width,
                    forearm_end - perpendicular * forearm_half_width,
                ),
                dtype=np.int32,
            )
            cv2.fillConvexPoly(hand_mask, forearm, 255)

        kernel_size = padding * 2 + 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )
        hand_mask = cv2.dilate(hand_mask, kernel)
        mask = cv2.bitwise_or(mask, hand_mask)
    return mask
