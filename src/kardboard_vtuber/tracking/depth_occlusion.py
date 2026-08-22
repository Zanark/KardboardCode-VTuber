"""Asynchronous monocular depth and privacy-safe held-object occlusion."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy import ndarray

from kardboard_vtuber.tracking.hand_occlusion import (
    HandOcclusionState,
    build_hand_mask,
)
from kardboard_vtuber.tracking.models import FaceTrackingState

_IMAGE_MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
_IMAGE_STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


@dataclass(frozen=True, slots=True)
class DepthOcclusionConfig:
    model_path: Path = Path("models/depth_anything_v2_small_fp16.onnx")
    input_long_side: int = 196
    maximum_age_ms: int = 250

    def __post_init__(self) -> None:
        if self.input_long_side < 98 or self.input_long_side % 14:
            raise ValueError("depth input size must be a multiple of 14 and at least 98")
        if self.maximum_age_ms <= 0:
            raise ValueError("maximum depth age must be positive")


@dataclass(frozen=True, slots=True)
class DepthOcclusionState:
    timestamp_ms: int
    depth: ndarray | None
    last_error: str | None = None

    @classmethod
    def empty(cls) -> DepthOcclusionState:
        return cls(timestamp_ms=0, depth=None)


class AsyncDepthEstimator:
    """Runs latest-only Depth Anything V2 inference on a worker thread."""

    def __init__(self, config: DepthOcclusionConfig) -> None:
        if not config.model_path.is_file():
            raise FileNotFoundError(
                f"Depth model not found at {config.model_path}. "
                "Run: python scripts/download_depth_occlusion_model.py"
            )
        try:
            import onnxruntime as ort
        except ImportError as error:
            raise RuntimeError(
                "ONNX Runtime DirectML is not installed. Install the .[occlusion] extra."
            ) from error

        session_options = ort.SessionOptions()
        session_options.enable_mem_pattern = False
        session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        providers = ort.get_available_providers()
        preferred = (
            ["DmlExecutionProvider", "CPUExecutionProvider"]
            if "DmlExecutionProvider" in providers
            else ["CPUExecutionProvider"]
        )
        self._session = ort.InferenceSession(
            str(config.model_path.resolve()),
            sess_options=session_options,
            providers=preferred,
        )
        self._input_name = self._session.get_inputs()[0].name
        self._config = config
        self._condition = threading.Condition()
        self._pending: tuple[int, ndarray] | None = None
        self._state = DepthOcclusionState.empty()
        self._stopping = False
        self._thread = threading.Thread(
            target=self._run,
            name="kardboard-depth-occlusion",
            daemon=True,
        )
        self._thread.start()

    @property
    def provider(self) -> str:
        return self._session.get_providers()[0]

    def submit(self, frame_bgr: ndarray, captured_at_ns: int) -> None:
        prepared = _prepare_depth_input(frame_bgr, self._config.input_long_side)
        with self._condition:
            self._pending = (captured_at_ns // 1_000_000, prepared)
            self._condition.notify()

    def snapshot(self) -> DepthOcclusionState:
        with self._condition:
            return self._state

    def close(self) -> None:
        with self._condition:
            self._stopping = True
            self._condition.notify()
        self._thread.join(timeout=5.0)

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._stopping:
                    self._condition.wait()
                if self._stopping:
                    return
                timestamp_ms, prepared = self._pending
                self._pending = None
            try:
                output = self._session.run(None, {self._input_name: prepared})[0]
                state = DepthOcclusionState(
                    timestamp_ms=timestamp_ms,
                    depth=np.asarray(output[0], dtype=np.float32),
                )
            except Exception as error:
                state = DepthOcclusionState(
                    timestamp_ms=timestamp_ms,
                    depth=None,
                    last_error=f"{type(error).__name__}: {error}",
                )
            with self._condition:
                self._state = state


def composite_depth_foreground(
    rendered_frame: ndarray,
    source_frame: ndarray,
    depth_state: DepthOcclusionState,
    hand_state: HandOcclusionState,
    face_state: FaceTrackingState,
    maximum_age_ms: int = 250,
) -> None:
    mask = build_depth_occlusion_mask(
        rendered_frame.shape[:2],
        depth_state,
        hand_state,
        face_state,
        maximum_age_ms=maximum_age_ms,
    )
    cv2.copyTo(source_frame, mask, rendered_frame)


def build_depth_occlusion_mask(
    frame_shape: tuple[int, int],
    depth_state: DepthOcclusionState,
    hand_state: HandOcclusionState,
    face_state: FaceTrackingState,
    *,
    maximum_age_ms: int = 250,
) -> ndarray:
    height, width = frame_shape
    hand_mask = build_hand_mask(frame_shape, hand_state)
    if (
        depth_state.depth is None
        or not hand_state.hands
        or not face_state.detected
        or abs(hand_state.timestamp_ms - depth_state.timestamp_ms) > maximum_age_ms
    ):
        return hand_mask

    depth = cv2.resize(
        depth_state.depth,
        (width, height),
        interpolation=cv2.INTER_CUBIC,
    )
    hand_values = depth[hand_mask > 0]
    face_mask = _face_reference_mask(frame_shape, face_state)
    face_values = depth[(face_mask > 0) & (hand_mask == 0)]
    if hand_values.size < 32 or face_values.size < 32:
        return hand_mask

    hand_depth = float(np.percentile(hand_values, 55))
    face_depth = float(np.median(face_values))
    depth_range = float(np.percentile(depth, 95) - np.percentile(depth, 5))
    separation = hand_depth - face_depth
    if separation <= max(0.08, depth_range * 0.06):
        return hand_mask

    threshold = face_depth + separation * 0.58
    near_mask = np.where(depth >= threshold, 255, 0).astype(np.uint8)
    strict_face_threshold = face_depth + separation * 0.72
    near_mask[(face_mask > 0) & (depth < strict_face_threshold)] = 0

    region_mask = _hand_region_mask(frame_shape, hand_state)
    candidate = cv2.bitwise_and(near_mask, region_mask)
    candidate = cv2.bitwise_or(candidate, hand_mask)
    close_size = max(5, round(max(height, width) * 0.009))
    if close_size % 2 == 0:
        close_size += 1
    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (close_size, close_size),
    )
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, close_kernel)
    return _components_touching_hand(candidate, hand_mask)


def _prepare_depth_input(frame_bgr: ndarray, long_side: int) -> ndarray:
    height, width = frame_bgr.shape[:2]
    if height >= width:
        target_height = long_side
        target_width = max(14, round(width / height * long_side / 14) * 14)
    else:
        target_width = long_side
        target_height = max(14, round(height / width * long_side / 14) * 14)
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(
        rgb,
        (target_width, target_height),
        interpolation=cv2.INTER_AREA,
    )
    normalized = resized.astype(np.float32) / 255.0
    normalized = (normalized - _IMAGE_MEAN) / _IMAGE_STD
    return np.ascontiguousarray(np.transpose(normalized, (2, 0, 1))[None])


def _face_reference_mask(
    frame_shape: tuple[int, int],
    state: FaceTrackingState,
) -> ndarray:
    height, width = frame_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    half_width = state.face_width * width * 0.68
    half_height = state.face_height * height * 0.92
    center = (
        round(state.center_x * width),
        round((state.center_y - state.face_height * 0.12) * height),
    )
    axes = (max(1, round(half_width)), max(1, round(half_height)))
    cv2.ellipse(mask, center, axes, 0.0, 0.0, 360.0, 255, -1)
    return mask


def _hand_region_mask(
    frame_shape: tuple[int, int],
    state: HandOcclusionState,
) -> ndarray:
    height, width = frame_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    for hand in state.hands:
        points = np.asarray(
            [(x * width, y * height) for x, y in hand],
            dtype=np.float32,
        )
        left, top = np.min(points, axis=0)
        right, bottom = np.max(points, axis=0)
        hand_width = right - left
        hand_height = bottom - top
        left = max(0, round(left - hand_width * 1.35))
        right = min(width - 1, round(right + hand_width * 1.35))
        top = max(0, round(top - hand_height * 0.85))
        bottom = min(height - 1, round(bottom + hand_height * 0.55))
        cv2.rectangle(mask, (left, top), (right, bottom), 255, -1)
    return mask


def _components_touching_hand(candidate: ndarray, hand_mask: ndarray) -> ndarray:
    count, labels = cv2.connectedComponents(candidate)
    output = np.zeros_like(candidate)
    for label in range(1, count):
        component = labels == label
        if np.any(hand_mask[component] > 0):
            output[component] = 255
    return output
