"""Normalized tracking data structures independent of MediaPipe."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class NormalizedLandmark:
    """One face landmark in normalized image coordinates."""

    x: float
    y: float
    z: float


@dataclass(frozen=True, slots=True)
class HeadPose:
    """Renderer-friendly head transform derived from a 4x4 matrix."""

    translation_x: float
    translation_y: float
    translation_z: float
    pitch_degrees: float
    yaw_degrees: float
    roll_degrees: float

    @classmethod
    def identity(cls) -> HeadPose:
        return cls(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_matrix(cls, matrix: Sequence[Sequence[float]] | NDArray[np.floating]) -> HeadPose:
        array = np.asarray(matrix, dtype=np.float64)
        if array.shape != (4, 4):
            raise ValueError(f"head transformation matrix must be 4x4, got {array.shape}")
        pitch, yaw, roll = cv2.RQDecomp3x3(array[:3, :3])[0]
        return cls(
            translation_x=float(array[0, 3]),
            translation_y=float(array[1, 3]),
            translation_z=float(array[2, 3]),
            pitch_degrees=float(pitch),
            yaw_degrees=float(yaw),
            roll_degrees=float(roll),
        )


@dataclass(frozen=True, slots=True)
class FaceTrackingState:
    """One normalized face observation consumed by future rendering."""

    timestamp_ms: int
    detected: bool
    landmarks: tuple[NormalizedLandmark, ...]
    center_x: float
    center_y: float
    face_width: float
    face_height: float
    left_eye_open: float
    right_eye_open: float
    mouth_open: float
    head_pose: HeadPose

    @classmethod
    def no_face(cls, timestamp_ms: int = 0) -> FaceTrackingState:
        return cls(
            timestamp_ms=timestamp_ms,
            detected=False,
            landmarks=(),
            center_x=0.5,
            center_y=0.5,
            face_width=0.0,
            face_height=0.0,
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose.identity(),
        )


@dataclass(frozen=True, slots=True)
class TrackingSnapshot:
    """Immutable tracker diagnostics plus the latest normalized result."""

    state: FaceTrackingState
    submitted_frames: int
    result_frames: int
    detected_frames: int
    dropped_or_pending_frames: int
    measured_fps: float
    last_error: str | None


def normalize_face(
    *,
    timestamp_ms: int,
    landmarks: Iterable[object],
    blendshapes: Iterable[object],
    transformation_matrix: Sequence[Sequence[float]] | NDArray[np.floating] | None,
) -> FaceTrackingState:
    """Convert MediaPipe-shaped values into stable project contracts."""

    normalized_landmarks = tuple(
        NormalizedLandmark(float(point.x), float(point.y), float(point.z)) for point in landmarks
    )
    if not normalized_landmarks:
        return FaceTrackingState.no_face(timestamp_ms)

    scores = _blendshape_scores(blendshapes)
    xs = [point.x for point in normalized_landmarks]
    ys = [point.y for point in normalized_landmarks]
    pose = (
        HeadPose.from_matrix(transformation_matrix)
        if transformation_matrix is not None
        else HeadPose.identity()
    )
    return FaceTrackingState(
        timestamp_ms=timestamp_ms,
        detected=True,
        landmarks=normalized_landmarks,
        center_x=(min(xs) + max(xs)) / 2,
        center_y=(min(ys) + max(ys)) / 2,
        face_width=max(xs) - min(xs),
        face_height=max(ys) - min(ys),
        left_eye_open=1.0 - _clamp01(scores.get("eyeBlinkLeft", 0.0)),
        right_eye_open=1.0 - _clamp01(scores.get("eyeBlinkRight", 0.0)),
        mouth_open=_clamp01(scores.get("jawOpen", 0.0)),
        head_pose=pose,
    )


def _blendshape_scores(categories: Iterable[object]) -> Mapping[str, float]:
    scores: dict[str, float] = {}
    for category in categories:
        name = getattr(category, "category_name", None)
        score = getattr(category, "score", None)
        if name is not None and score is not None:
            scores[str(name)] = float(score)
    return scores


def _clamp01(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return min(1.0, max(0.0, value))
