"""Asynchronous person segmentation for privacy-safe green-screen output."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy import ndarray


@dataclass(frozen=True, slots=True)
class GreenScreenConfig:
    model_path: Path = Path("models/selfie_segmenter.tflite")
    input_width: int = 384
    person_threshold: float = 0.35
    maximum_mask_age_ms: int = 500

    def __post_init__(self) -> None:
        if self.input_width <= 0:
            raise ValueError("segmentation input width must be positive")
        if not 0.0 <= self.person_threshold <= 1.0:
            raise ValueError("person_threshold must be between 0 and 1")
        if self.maximum_mask_age_ms <= 0:
            raise ValueError("maximum_mask_age_ms must be positive")


@dataclass(frozen=True, slots=True)
class PersonSegmentationState:
    timestamp_ms: int
    person_mask: ndarray | None

    @property
    def detected(self) -> bool:
        return self.person_mask is not None

    @classmethod
    def empty(cls, timestamp_ms: int = 0) -> PersonSegmentationState:
        return cls(timestamp_ms=timestamp_ms, person_mask=None)


class MediaPipePersonSegmenter:
    """Retains the latest asynchronous MediaPipe person-confidence mask."""

    def __init__(self, config: GreenScreenConfig) -> None:
        if not config.model_path.is_file():
            raise FileNotFoundError(
                f"Selfie Segmenter model not found at {config.model_path}. "
                "Run: python scripts/download_selfie_segmenter_model.py"
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
        self._state = PersonSegmentationState.empty()
        self._last_submitted_timestamp_ms = -1
        options = mp.tasks.vision.ImageSegmenterOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(config.model_path.resolve()),
            ),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            output_confidence_masks=True,
            output_category_mask=False,
            result_callback=self._on_result,
        )
        self._segmenter = mp.tasks.vision.ImageSegmenter.create_from_options(options)

    @property
    def config(self) -> GreenScreenConfig:
        return self._config

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
        self._segmenter.segment_async(image, timestamp_ms)

    def snapshot(self) -> PersonSegmentationState:
        with self._lock:
            return self._state

    def close(self) -> None:
        self._segmenter.close()

    def _on_result(self, result: Any, _output_image: Any, timestamp_ms: int) -> None:
        if not result.confidence_masks:
            state = PersonSegmentationState.empty(timestamp_ms)
        else:
            mask = np.asarray(result.confidence_masks[0].numpy_view(), dtype=np.float32).copy()
            mask = np.squeeze(mask)
            if mask.ndim != 2:
                raise ValueError(f"person segmentation mask must be 2D, got {mask.shape}")
            state = PersonSegmentationState(
                timestamp_ms=timestamp_ms,
                person_mask=np.clip(mask, 0.0, 1.0),
            )
        with self._lock:
            self._state = state


def apply_green_screen(
    frame: ndarray,
    state: PersonSegmentationState,
    *,
    current_timestamp_ms: int,
    config: GreenScreenConfig,
) -> None:
    """Preserve person pixels and replace every other pixel with chroma green."""

    source = frame.copy()
    frame[:] = (0, 255, 0)
    if (
        state.person_mask is None
        or current_timestamp_ms < state.timestamp_ms
        or current_timestamp_ms - state.timestamp_ms > config.maximum_mask_age_ms
    ):
        return

    height, width = frame.shape[:2]
    confidence = cv2.resize(
        state.person_mask,
        (width, height),
        interpolation=cv2.INTER_LINEAR,
    )
    person_mask = np.where(confidence >= config.person_threshold, 255, 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    person_mask = cv2.morphologyEx(person_mask, cv2.MORPH_CLOSE, kernel)
    person_mask = cv2.dilate(person_mask, kernel, iterations=1)
    cv2.copyTo(source, person_mask, frame)
