"""Adaptive low-pass filtering for normalized face-tracking state."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from kardboard_vtuber.tracking.models import (
    FaceTrackingState,
    HeadPose,
    NormalizedLandmark,
)


@dataclass(frozen=True, slots=True)
class OneEuroParameters:
    """One Euro filter tuning parameters."""

    min_cutoff: float = 1.0
    beta: float = 0.02
    derivative_cutoff: float = 1.0

    def __post_init__(self) -> None:
        if self.min_cutoff <= 0:
            raise ValueError("min_cutoff must be positive")
        if self.beta < 0:
            raise ValueError("beta cannot be negative")
        if self.derivative_cutoff <= 0:
            raise ValueError("derivative_cutoff must be positive")


class OneEuroFilter:
    """Low-pass filter that increases responsiveness when motion accelerates."""

    def __init__(self, parameters: OneEuroParameters | None = None) -> None:
        self._parameters = parameters or OneEuroParameters()
        self._timestamp_seconds: float | None = None
        self._raw_value = 0.0
        self._filtered_value = 0.0
        self._filtered_derivative = 0.0

    def filter(self, value: float, timestamp_seconds: float) -> float:
        if not math.isfinite(value) or not math.isfinite(timestamp_seconds):
            raise ValueError("One Euro inputs must be finite")
        if self._timestamp_seconds is None:
            self._timestamp_seconds = timestamp_seconds
            self._raw_value = value
            self._filtered_value = value
            self._filtered_derivative = 0.0
            return value

        delta_seconds = timestamp_seconds - self._timestamp_seconds
        if delta_seconds <= 0:
            raise ValueError("One Euro timestamps must be strictly increasing")

        derivative = (value - self._raw_value) / delta_seconds
        derivative_alpha = _smoothing_factor(
            delta_seconds,
            self._parameters.derivative_cutoff,
        )
        self._filtered_derivative = _low_pass(
            derivative,
            self._filtered_derivative,
            derivative_alpha,
        )
        cutoff = (
            self._parameters.min_cutoff
            + self._parameters.beta * abs(self._filtered_derivative)
        )
        value_alpha = _smoothing_factor(delta_seconds, cutoff)
        self._filtered_value = _low_pass(value, self._filtered_value, value_alpha)
        self._raw_value = value
        self._timestamp_seconds = timestamp_seconds
        return self._filtered_value


@dataclass(frozen=True, slots=True)
class FaceMotionFilterConfig:
    """Separate One Euro tuning for face geometry, expressions, and pose."""

    landmarks: OneEuroParameters = field(
        default_factory=lambda: OneEuroParameters(min_cutoff=1.2, beta=0.02)
    )
    bounds: OneEuroParameters = field(
        default_factory=lambda: OneEuroParameters(min_cutoff=1.0, beta=0.03)
    )
    expressions: OneEuroParameters = field(
        default_factory=lambda: OneEuroParameters(min_cutoff=3.0, beta=0.2)
    )
    pose: OneEuroParameters = field(
        default_factory=lambda: OneEuroParameters(min_cutoff=1.0, beta=0.02)
    )


class FaceMotionFilter:
    """Filters a complete face state and resets cleanly across tracking loss."""

    _BOUND_NAMES = ("center_x", "center_y", "face_width", "face_height")
    _EXPRESSION_NAMES = ("left_eye_open", "right_eye_open", "mouth_open")
    _POSE_NAMES = (
        "translation_x",
        "translation_y",
        "translation_z",
        "pitch_degrees",
        "yaw_degrees",
        "roll_degrees",
    )

    def __init__(self, config: FaceMotionFilterConfig | None = None) -> None:
        self._config = config or FaceMotionFilterConfig()
        self._landmark_filters: list[tuple[OneEuroFilter, OneEuroFilter, OneEuroFilter]] = []
        self._bounds: dict[str, OneEuroFilter] = {}
        self._expressions: dict[str, OneEuroFilter] = {}
        self._pose: dict[str, OneEuroFilter] = {}

    def filter(self, state: FaceTrackingState) -> FaceTrackingState:
        if not state.detected:
            self.reset()
            return state
        if len(self._landmark_filters) != len(state.landmarks):
            self.reset()
            self._landmark_filters = [
                (
                    OneEuroFilter(self._config.landmarks),
                    OneEuroFilter(self._config.landmarks),
                    OneEuroFilter(self._config.landmarks),
                )
                for _ in state.landmarks
            ]
            self._bounds = {
                name: OneEuroFilter(self._config.bounds) for name in self._BOUND_NAMES
            }
            self._expressions = {
                name: OneEuroFilter(self._config.expressions)
                for name in self._EXPRESSION_NAMES
            }
            self._pose = {
                name: OneEuroFilter(self._config.pose) for name in self._POSE_NAMES
            }

        timestamp_seconds = state.timestamp_ms / 1000.0
        landmarks = tuple(
            NormalizedLandmark(
                x=filters[0].filter(landmark.x, timestamp_seconds),
                y=filters[1].filter(landmark.y, timestamp_seconds),
                z=filters[2].filter(landmark.z, timestamp_seconds),
            )
            for landmark, filters in zip(
                state.landmarks,
                self._landmark_filters,
                strict=True,
            )
        )
        bounds = {
            name: self._bounds[name].filter(getattr(state, name), timestamp_seconds)
            for name in self._BOUND_NAMES
        }
        expressions = {
            name: self._expressions[name].filter(getattr(state, name), timestamp_seconds)
            for name in self._EXPRESSION_NAMES
        }
        pose = {
            name: self._pose[name].filter(getattr(state.head_pose, name), timestamp_seconds)
            for name in self._POSE_NAMES
        }
        return FaceTrackingState(
            timestamp_ms=state.timestamp_ms,
            detected=True,
            landmarks=landmarks,
            center_x=bounds["center_x"],
            center_y=bounds["center_y"],
            face_width=bounds["face_width"],
            face_height=bounds["face_height"],
            left_eye_open=expressions["left_eye_open"],
            right_eye_open=expressions["right_eye_open"],
            mouth_open=expressions["mouth_open"],
            head_pose=HeadPose(**pose),
        )

    def reset(self) -> None:
        self._landmark_filters = []
        self._bounds = {}
        self._expressions = {}
        self._pose = {}


def _smoothing_factor(delta_seconds: float, cutoff: float) -> float:
    time_constant = 1.0 / (2.0 * math.pi * cutoff)
    return 1.0 / (1.0 + time_constant / delta_seconds)


def _low_pass(value: float, previous: float, alpha: float) -> float:
    return alpha * value + (1.0 - alpha) * previous
