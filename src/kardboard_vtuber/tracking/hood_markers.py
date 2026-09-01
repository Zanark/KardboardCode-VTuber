"""Colour-square hood tracking for rear and profile head poses."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum

import cv2
import numpy as np
from numpy import ndarray

from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    PoseLandmark,
    pose_torso_is_plausible,
)
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose

_LEFT_SHOULDER = 11
_RIGHT_SHOULDER = 12


class HoodMarkerColor(StrEnum):
    GREEN = "green"
    BLUE = "blue"


class HoodTrackingSource(StrEnum):
    NONE = "none"
    FACE = "face"
    MARKER = "marker"
    REAR = "rear"
    PREDICTION = "prediction"


@dataclass(frozen=True, slots=True)
class HoodMarkerObservation:
    color: HoodMarkerColor
    center_x: float
    center_y: float
    side_width: float
    side_height: float
    confidence: float


@dataclass(frozen=True, slots=True)
class HoodMarkerSnapshot:
    timestamp_ms: int
    observations: tuple[HoodMarkerObservation, ...]
    head_state: FaceTrackingState
    source: HoodTrackingSource

    @property
    def detected(self) -> bool:
        return bool(self.observations)

    @property
    def predicted(self) -> bool:
        return self.source is HoodTrackingSource.PREDICTION


@dataclass(frozen=True, slots=True)
class HoodMarkerTrackerConfig:
    input_width: int = 640
    minimum_saturation: int = 65
    minimum_value: int = 48
    minimum_area_pixels: float = 55.0
    maximum_area_fraction: float = 0.025
    minimum_extent: float = 0.46
    minimum_solidity: float = 0.78
    maximum_aspect_ratio: float = 1.85
    minimum_side_fraction: float = 0.006
    maximum_side_fraction: float = 0.09
    search_radius_multiplier: float = 2.0
    stale_after_ms: int = 700
    side_marker_hold_ms: int = 250
    maximum_face_age_ms: int = 300
    maximum_pose_age_ms: int = 300
    smoothing_alpha: float = 0.42
    default_head_width_marker_ratio: float = 1.55
    default_head_height_to_width: float = 1.25
    default_marker_vertical_offset: float = 0.78
    coverage_scale: float = 1.12

    def __post_init__(self) -> None:
        if self.input_width <= 0:
            raise ValueError("input_width must be positive")
        for name in ("minimum_saturation", "minimum_value"):
            if not 0 <= getattr(self, name) <= 255:
                raise ValueError(f"{name} must be between 0 and 255")
        if self.minimum_area_pixels <= 0:
            raise ValueError("minimum_area_pixels must be positive")
        if not 0.0 < self.maximum_area_fraction <= 1.0:
            raise ValueError("maximum_area_fraction must be greater than 0 and at most 1")
        for name in ("minimum_extent", "minimum_solidity", "smoothing_alpha"):
            if not 0.0 < getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be greater than 0 and at most 1")
        for name in (
            "maximum_aspect_ratio",
            "search_radius_multiplier",
            "default_head_width_marker_ratio",
            "default_head_height_to_width",
            "default_marker_vertical_offset",
            "coverage_scale",
        ):
            if getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be positive")
        for name in ("stale_after_ms", "side_marker_hold_ms"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        for name in ("maximum_face_age_ms", "maximum_pose_age_ms"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if not 0.0 < self.minimum_side_fraction < self.maximum_side_fraction <= 1.0:
            raise ValueError(
                "side fractions must satisfy 0 < minimum < maximum <= 1"
            )


@dataclass(slots=True)
class _MarkerCalibration:
    center_x_offset: float
    center_y_offset: float
    face_width_ratio: float
    face_height_ratio: float
    samples: int = 1


@dataclass(frozen=True, slots=True)
class _SearchAnchor:
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float


class HoodMarkerHeadTracker:
    """Tracks coloured hood squares and resolves them into a renderer head state."""

    _HUE_RANGES = {
        HoodMarkerColor.GREEN: ((34, 90),),
        HoodMarkerColor.BLUE: ((91, 139),),
    }
    _COLOR_MINIMUM_SATURATION = {
        HoodMarkerColor.GREEN: 65,
        HoodMarkerColor.BLUE: 90,
    }
    _DEFAULT_YAW = {
        # Positive yaw exposes the physical left side; negative exposes the right.
        HoodMarkerColor.GREEN: 90.0,
        HoodMarkerColor.BLUE: -90.0,
    }

    def __init__(self, config: HoodMarkerTrackerConfig | None = None) -> None:
        self._config = config or HoodMarkerTrackerConfig()
        self._calibrations: dict[HoodMarkerColor, _MarkerCalibration] = {}
        self._last_observations: dict[HoodMarkerColor, HoodMarkerObservation] = {}
        self._last_head_state: FaceTrackingState | None = None
        self._last_head_timestamp_ms: int | None = None
        self._last_marker_timestamp_ms: int | None = None
        self._last_shoulder_center: tuple[float, float] | None = None
        self._last_reference_size: tuple[float, float] | None = None
        self._snapshot = HoodMarkerSnapshot(
            timestamp_ms=0,
            observations=(),
            head_state=FaceTrackingState.no_face(),
            source=HoodTrackingSource.NONE,
        )

    def update(
        self,
        frame_bgr: ndarray,
        *,
        timestamp_ms: int,
        face: FaceTrackingState,
        pose: FullBodyPoseState,
    ) -> FaceTrackingState:
        face_age_ms = timestamp_ms - face.timestamp_ms
        if face_age_ms < 0 or face_age_ms > self._config.maximum_face_age_ms:
            face = FaceTrackingState.no_face(timestamp_ms)
        pose_age_ms = timestamp_ms - pose.timestamp_ms
        if pose_age_ms < 0 or pose_age_ms > self._config.maximum_pose_age_ms:
            pose = FullBodyPoseState.empty(timestamp_ms)
        if (
            self._last_marker_timestamp_ms is not None
            and timestamp_ms - self._last_marker_timestamp_ms
            > self._config.stale_after_ms
        ):
            self._last_observations.clear()
        if (
            self._last_head_timestamp_ms is not None
            and timestamp_ms - self._last_head_timestamp_ms
            > self._config.stale_after_ms
        ):
            self._last_head_state = None
            self._last_head_timestamp_ms = None
            self._last_shoulder_center = None
            self._last_reference_size = None
        anchor = self._search_anchor(face, pose)
        observations = self._detect(frame_bgr, anchor)
        if face.detected:
            for observation in observations:
                self._update_calibration(observation, face)
            self._last_observations = {
                observation.color: observation for observation in observations
            }
            self._last_head_state = face
            self._last_reference_size = (face.face_width, face.face_height)
            if observations:
                self._last_head_timestamp_ms = timestamp_ms
                self._last_marker_timestamp_ms = timestamp_ms
            else:
                self._last_head_timestamp_ms = timestamp_ms
            self._last_shoulder_center = _shoulder_center(pose)
            self._snapshot = HoodMarkerSnapshot(
                timestamp_ms=timestamp_ms,
                observations=observations,
                head_state=face,
                source=HoodTrackingSource.FACE,
            )
            return face

        if observations:
            pose_reference = self._head_from_pose(
                pose,
                timestamp_ms,
                frame_bgr.shape[1],
                frame_bgr.shape[0],
            )
            if pose_reference.detected and self._last_reference_size is None:
                self._last_reference_size = (
                    pose_reference.face_width,
                    pose_reference.face_height,
                )
            head = self._head_from_observations(
                observations,
                timestamp_ms,
                frame_bgr.shape[1],
                frame_bgr.shape[0],
            )
            if self._last_reference_size is not None:
                head = replace(
                    head,
                    face_width=self._last_reference_size[0],
                    face_height=self._last_reference_size[1],
                )
            if self._last_head_state is not None:
                head = _smooth_state(
                    self._last_head_state,
                    head,
                    self._config.smoothing_alpha,
                )
            self._last_observations = {
                observation.color: observation for observation in observations
            }
            self._last_head_state = head
            self._last_head_timestamp_ms = timestamp_ms
            self._last_marker_timestamp_ms = timestamp_ms
            self._last_shoulder_center = _shoulder_center(pose)
            self._snapshot = HoodMarkerSnapshot(
                timestamp_ms=timestamp_ms,
                observations=observations,
                head_state=head,
                source=HoodTrackingSource.MARKER,
            )
            return head

        marker_age_ms = (
            timestamp_ms - self._last_marker_timestamp_ms
            if self._last_marker_timestamp_ms is not None
            else self._config.side_marker_hold_ms + 1
        )
        if marker_age_ms <= self._config.side_marker_hold_ms:
            predicted = self._predict_from_shoulders(timestamp_ms, pose)
            if predicted.detected:
                self._snapshot = HoodMarkerSnapshot(
                    timestamp_ms=timestamp_ms,
                    observations=(),
                    head_state=predicted,
                    source=HoodTrackingSource.PREDICTION,
                )
                return predicted

        pose_head = self._head_from_pose(
            pose,
            timestamp_ms,
            frame_bgr.shape[1],
            frame_bgr.shape[0],
        )
        if pose_head.detected:
            if self._last_head_state is not None:
                pose_head = _smooth_state(
                    self._last_head_state,
                    pose_head,
                    self._config.smoothing_alpha,
                )
            self._last_head_state = pose_head
            self._last_head_timestamp_ms = timestamp_ms
            self._last_shoulder_center = _shoulder_center(pose)
            self._last_reference_size = (
                pose_head.face_width,
                pose_head.face_height,
            )
            self._snapshot = HoodMarkerSnapshot(
                timestamp_ms=timestamp_ms,
                observations=(),
                head_state=pose_head,
                source=HoodTrackingSource.REAR,
            )
            return pose_head

        predicted = self._predict_from_shoulders(timestamp_ms, pose)
        self._snapshot = HoodMarkerSnapshot(
            timestamp_ms=timestamp_ms,
            observations=(),
            head_state=predicted,
            source=(
                HoodTrackingSource.PREDICTION
                if predicted.detected
                else HoodTrackingSource.NONE
            ),
        )
        return predicted

    def snapshot(self) -> HoodMarkerSnapshot:
        return self._snapshot

    def reset(self) -> None:
        self._calibrations.clear()
        self._last_observations.clear()
        self._last_head_state = None
        self._last_head_timestamp_ms = None
        self._last_marker_timestamp_ms = None
        self._last_shoulder_center = None
        self._last_reference_size = None
        self._snapshot = HoodMarkerSnapshot(
            timestamp_ms=0,
            observations=(),
            head_state=FaceTrackingState.no_face(),
            source=HoodTrackingSource.NONE,
        )

    @staticmethod
    def draw_debug(frame: ndarray, snapshot: HoodMarkerSnapshot) -> None:
        colors = {
            HoodMarkerColor.GREEN: (0, 255, 0),
            HoodMarkerColor.BLUE: (255, 120, 0),
        }
        height, width = frame.shape[:2]
        for observation in snapshot.observations:
            center_x = round(observation.center_x * width)
            center_y = round(observation.center_y * height)
            half = max(5, round(observation.side_width * width / 2.0))
            color = colors[observation.color]
            cv2.rectangle(
                frame,
                (center_x - half, center_y - half),
                (center_x + half, center_y + half),
                color,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                observation.color.value.upper(),
                (center_x - half, max(18, center_y - half - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                color,
                2,
                cv2.LINE_AA,
            )

    def _search_anchor(
        self,
        face: FaceTrackingState,
        pose: FullBodyPoseState,
    ) -> _SearchAnchor | None:
        if face.detected:
            return _SearchAnchor(
                center_x=face.center_x,
                center_y=face.center_y,
                radius_x=max(0.10, face.face_width * 1.8),
                radius_y=max(0.15, face.face_height * 1.6),
            )
        shoulders = _visible_shoulders(pose)
        if shoulders is not None:
            left, right = shoulders
            width = max(0.06, math.hypot(right.x - left.x, right.y - left.y))
            visible_head = [
                pose.landmarks[index]
                for index in (0, 7, 8)
                if pose.landmarks[index].visibility >= 0.20
                and pose.landmarks[index].presence >= 0.20
            ]
            if visible_head:
                center_x = sum(point.x for point in visible_head) / len(visible_head)
                center_y = sum(point.y for point in visible_head) / len(visible_head)
            else:
                center_x = (left.x + right.x) / 2.0
                center_y = (left.y + right.y) / 2.0 - width * 0.72
            pose_anchor = _SearchAnchor(
                center_x=center_x,
                center_y=center_y,
                radius_x=width * 0.62,
                radius_y=width * 0.82,
            )
            if self._last_head_state is not None:
                movement = math.hypot(
                    pose_anchor.center_x - self._last_head_state.center_x,
                    pose_anchor.center_y - self._last_head_state.center_y,
                )
                if movement > max(0.10, width * 0.80):
                    state = self._last_head_state
                    return _SearchAnchor(
                        center_x=state.center_x,
                        center_y=state.center_y,
                        radius_x=max(0.10, state.face_width * 1.8),
                        radius_y=max(0.14, state.face_height * 1.8),
                    )
            return pose_anchor
        if self._last_head_state is not None:
            state = self._last_head_state
            return _SearchAnchor(
                center_x=state.center_x,
                center_y=state.center_y,
                radius_x=max(0.12, state.face_width * self._config.search_radius_multiplier),
                radius_y=max(0.18, state.face_height * self._config.search_radius_multiplier),
            )
        return None

    def _detect(
        self,
        frame_bgr: ndarray,
        anchor: _SearchAnchor | None,
    ) -> tuple[HoodMarkerObservation, ...]:
        frame_height, frame_width = frame_bgr.shape[:2]
        scale = min(1.0, self._config.input_width / frame_width)
        if scale < 1.0:
            working = cv2.resize(
                frame_bgr,
                (self._config.input_width, max(1, round(frame_height * scale))),
                interpolation=cv2.INTER_AREA,
            )
        else:
            working = frame_bgr
        height, width = working.shape[:2]
        hsv = cv2.cvtColor(working, cv2.COLOR_BGR2HSV)
        observations: list[HoodMarkerObservation] = []
        for color in HoodMarkerColor:
            candidates = self._color_candidates(hsv, color, anchor)
            if not candidates:
                continue
            observations.append(max(candidates, key=lambda item: item.confidence))
        return tuple(observations)

    def _color_candidates(
        self,
        hsv: ndarray,
        color: HoodMarkerColor,
        anchor: _SearchAnchor | None,
    ) -> list[HoodMarkerObservation]:
        height, width = hsv.shape[:2]
        saturation = max(
            self._config.minimum_saturation,
            self._COLOR_MINIMUM_SATURATION[color],
        )
        value = self._config.minimum_value
        mask = np.zeros((height, width), dtype=np.uint8)
        for hue_minimum, hue_maximum in self._HUE_RANGES[color]:
            mask |= cv2.inRange(
                hsv,
                np.asarray((hue_minimum, saturation, value), dtype=np.uint8),
                np.asarray((hue_maximum, 255, 255), dtype=np.uint8),
            )
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        maximum_area = width * height * self._config.maximum_area_fraction
        previous = self._last_observations.get(color)
        candidates: list[HoodMarkerObservation] = []
        for contour in cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )[0]:
            area = float(cv2.contourArea(contour))
            if not self._config.minimum_area_pixels <= area <= maximum_area:
                continue
            x, y, box_width, box_height = cv2.boundingRect(contour)
            aspect = box_width / max(1.0, float(box_height))
            if not 1.0 / self._config.maximum_aspect_ratio <= aspect <= (
                self._config.maximum_aspect_ratio
            ):
                continue
            extent = area / max(1.0, float(box_width * box_height))
            if extent < self._config.minimum_extent:
                continue
            hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
            solidity = area / max(1.0, hull_area)
            if solidity < self._config.minimum_solidity:
                continue
            center_x = (x + box_width / 2.0) / width
            center_y = (y + box_height / 2.0) / height
            side_pixels = max(box_width, box_height)
            side_width = side_pixels / width
            if not (
                self._config.minimum_side_fraction
                <= side_width
                <= self._config.maximum_side_fraction
            ):
                continue
            if previous is not None and not (
                previous.side_width * 0.52
                <= side_width
                <= previous.side_width * 1.92
            ):
                continue
            proximity = _candidate_proximity(center_x, center_y, anchor, previous)
            if proximity <= 0.0:
                continue
            squareness = min(aspect, 1.0 / aspect)
            confidence = (
                0.30 * squareness
                + 0.25 * min(1.0, extent)
                + 0.20 * min(1.0, solidity)
                + 0.25 * proximity
            )
            candidates.append(
                HoodMarkerObservation(
                    color=color,
                    center_x=center_x,
                    center_y=center_y,
                    side_width=side_width,
                    side_height=side_pixels / height,
                    confidence=confidence,
                )
            )
        return candidates

    def _update_calibration(
        self,
        observation: HoodMarkerObservation,
        face: FaceTrackingState,
    ) -> None:
        if observation.side_width <= 0.0 or observation.side_height <= 0.0:
            return
        sample = _MarkerCalibration(
            center_x_offset=(
                face.center_x - observation.center_x
            )
            / observation.side_width,
            center_y_offset=(
                face.center_y - observation.center_y
            )
            / observation.side_height,
            face_width_ratio=face.face_width / observation.side_width,
            face_height_ratio=face.face_height / observation.side_height,
        )
        current = self._calibrations.get(observation.color)
        if current is None:
            self._calibrations[observation.color] = sample
            return
        alpha = 0.18
        current.center_x_offset = _lerp(
            current.center_x_offset,
            sample.center_x_offset,
            alpha,
        )
        current.center_y_offset = _lerp(
            current.center_y_offset,
            sample.center_y_offset,
            alpha,
        )
        current.face_width_ratio = _lerp(
            current.face_width_ratio,
            sample.face_width_ratio,
            alpha,
        )
        current.face_height_ratio = _lerp(
            current.face_height_ratio,
            sample.face_height_ratio,
            alpha,
        )
        current.samples += 1

    def _head_from_observations(
        self,
        observations: tuple[HoodMarkerObservation, ...],
        timestamp_ms: int,
        frame_width: int,
        frame_height: int,
    ) -> FaceTrackingState:
        weighted: list[tuple[float, float, float, float, float, float]] = []
        for observation in observations:
            calibration = self._calibrations.get(observation.color)
            if calibration is None:
                center_x_offset = 0.0
                center_y_offset = self._config.default_marker_vertical_offset
                face_width_ratio = self._config.default_head_width_marker_ratio
                face_height_ratio = (
                    face_width_ratio
                    * self._config.default_head_height_to_width
                )
            else:
                center_x_offset = calibration.center_x_offset
                center_y_offset = calibration.center_y_offset
                face_width_ratio = calibration.face_width_ratio
                face_height_ratio = calibration.face_height_ratio
            weight = max(0.05, observation.confidence)
            weighted.append(
                (
                    observation.center_x + center_x_offset * observation.side_width,
                    observation.center_y + center_y_offset * observation.side_height,
                    observation.side_width * face_width_ratio,
                    observation.side_height * face_height_ratio,
                    self._DEFAULT_YAW[observation.color],
                    weight,
                )
            )
        total_weight = sum(item[5] for item in weighted)
        center_x = sum(item[0] * item[5] for item in weighted) / total_weight
        center_y = sum(item[1] * item[5] for item in weighted) / total_weight
        face_width = max(
            0.035,
            min(
                0.24,
                sum(item[2] * item[5] for item in weighted) / total_weight,
            ),
        )
        face_height = max(
            0.055,
            min(
                0.34,
                sum(item[3] * item[5] for item in weighted) / total_weight,
            ),
        )
        yaw = _weighted_angle((item[4], item[5]) for item in weighted)
        coverage = self._config.coverage_scale
        return FaceTrackingState(
            timestamp_ms=timestamp_ms,
            detected=True,
            landmarks=(),
            center_x=_clamp01(center_x),
            center_y=_clamp01(center_y),
            face_width=min(1.0, face_width * coverage),
            face_height=min(1.0, face_height * coverage),
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose(0.0, 0.0, 0.0, 0.0, yaw, 0.0),
        )

    def _predict_from_shoulders(
        self,
        timestamp_ms: int,
        pose: FullBodyPoseState,
    ) -> FaceTrackingState:
        state = self._last_head_state
        head_timestamp = self._last_head_timestamp_ms
        marker_timestamp = self._last_marker_timestamp_ms
        if (
            state is None
            or head_timestamp is None
            or marker_timestamp is None
            or timestamp_ms - head_timestamp > self._config.stale_after_ms
            or timestamp_ms - marker_timestamp > self._config.stale_after_ms
        ):
            return FaceTrackingState.no_face(timestamp_ms)
        shoulder_center = _shoulder_center(pose)
        if shoulder_center is None or self._last_shoulder_center is None:
            return FaceTrackingState(
                timestamp_ms=timestamp_ms,
                detected=True,
                landmarks=(),
                center_x=state.center_x,
                center_y=state.center_y,
                face_width=state.face_width,
                face_height=state.face_height,
                left_eye_open=1.0,
                right_eye_open=1.0,
                mouth_open=0.0,
                head_pose=state.head_pose,
            )
        delta_x = shoulder_center[0] - self._last_shoulder_center[0]
        delta_y = shoulder_center[1] - self._last_shoulder_center[1]
        self._last_shoulder_center = shoulder_center
        predicted = FaceTrackingState(
            timestamp_ms=timestamp_ms,
            detected=True,
            landmarks=(),
            center_x=_clamp01(state.center_x + delta_x),
            center_y=_clamp01(state.center_y + delta_y),
            face_width=state.face_width,
            face_height=state.face_height,
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=state.head_pose,
        )
        self._last_head_state = predicted
        return predicted

    def _head_from_pose(
        self,
        pose: FullBodyPoseState,
        timestamp_ms: int,
        frame_width: int,
        frame_height: int,
    ) -> FaceTrackingState:
        pose_age_ms = timestamp_ms - pose.timestamp_ms
        if pose_age_ms < 0 or pose_age_ms > self._config.maximum_pose_age_ms:
            return FaceTrackingState.no_face(timestamp_ms)
        shoulders = _visible_shoulders(pose)
        if shoulders is None:
            return FaceTrackingState.no_face(timestamp_ms)
        head_points = [
            pose.landmarks[index]
            for index in (0, 2, 5, 7, 8)
            if pose.landmarks[index].visibility >= 0.35
            and pose.landmarks[index].presence >= 0.35
        ]
        left, right = shoulders
        shoulder_width = math.hypot(right.x - left.x, right.y - left.y)
        if shoulder_width < 0.04:
            return FaceTrackingState.no_face(timestamp_ms)
        if len(head_points) >= 2:
            center_x = sum(point.x for point in head_points) / len(head_points)
            center_y = sum(point.y for point in head_points) / len(head_points)
        else:
            center_x = (left.x + right.x) / 2.0
            center_y = (left.y + right.y) / 2.0 - shoulder_width * 0.72
        face_width = shoulder_width * 0.36
        if (
            pose.landmarks[7].visibility >= 0.35
            and pose.landmarks[8].visibility >= 0.35
        ):
            ear_width = math.hypot(
                pose.landmarks[8].x - pose.landmarks[7].x,
                pose.landmarks[8].y - pose.landmarks[7].y,
            )
            face_width = max(face_width * 0.75, min(face_width * 1.35, ear_width * 1.08))
        face_height = (
            face_width
            * frame_width
            / frame_height
            * self._config.default_head_height_to_width
        )
        roll = 0.0
        if (
            pose.landmarks[7].visibility >= 0.35
            and pose.landmarks[8].visibility >= 0.35
        ):
            roll = math.degrees(
                math.atan2(
                    pose.landmarks[8].y - pose.landmarks[7].y,
                    pose.landmarks[8].x - pose.landmarks[7].x,
                )
            )
            if roll > 90.0:
                roll -= 180.0
            elif roll < -90.0:
                roll += 180.0
        return FaceTrackingState(
            timestamp_ms=timestamp_ms,
            detected=True,
            landmarks=(),
            center_x=_clamp01(center_x),
            center_y=_clamp01(center_y),
            face_width=max(
                0.035,
                min(0.24, face_width * self._config.coverage_scale),
            ),
            face_height=max(
                0.055,
                min(0.34, face_height * self._config.coverage_scale),
            ),
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose(0.0, 0.0, 0.0, 0.0, 179.0, roll),
        )


def _candidate_proximity(
    center_x: float,
    center_y: float,
    anchor: _SearchAnchor | None,
    previous: HoodMarkerObservation | None,
) -> float:
    if anchor is not None:
        delta_x = (center_x - anchor.center_x) / max(0.01, anchor.radius_x)
        delta_y = (center_y - anchor.center_y) / max(0.01, anchor.radius_y)
        distance = math.hypot(delta_x, delta_y)
        anchor_score = max(0.0, 1.0 - distance)
        if anchor_score <= 0.0:
            return 0.0
        if previous is None:
            return anchor_score
        distance = math.hypot(
            center_x - previous.center_x,
            center_y - previous.center_y,
        )
        temporal_score = max(0.0, 1.0 - distance / 0.16)
        return 0.72 * anchor_score + 0.28 * temporal_score
    if previous is not None:
        distance = math.hypot(
            center_x - previous.center_x,
            center_y - previous.center_y,
        )
        return max(0.0, 1.0 - distance / 0.16)
    return 0.0


def _visible_shoulders(
    pose: FullBodyPoseState,
) -> tuple[PoseLandmark, PoseLandmark] | None:
    if not pose.detected or not pose_torso_is_plausible(pose):
        return None
    left = pose.landmarks[_LEFT_SHOULDER]
    right = pose.landmarks[_RIGHT_SHOULDER]
    if any(
        value < 0.30
        for point in (left, right)
        for value in (point.visibility, point.presence)
    ):
        return None
    return left, right


def _shoulder_center(pose: FullBodyPoseState) -> tuple[float, float] | None:
    shoulders = _visible_shoulders(pose)
    if shoulders is None:
        return None
    left, right = shoulders
    return ((left.x + right.x) / 2.0, (left.y + right.y) / 2.0)


def _smooth_state(
    previous: FaceTrackingState,
    current: FaceTrackingState,
    alpha: float,
) -> FaceTrackingState:
    return FaceTrackingState(
        timestamp_ms=current.timestamp_ms,
        detected=True,
        landmarks=(),
        center_x=_lerp(previous.center_x, current.center_x, alpha),
        center_y=_lerp(previous.center_y, current.center_y, alpha),
        face_width=_lerp(previous.face_width, current.face_width, alpha),
        face_height=_lerp(previous.face_height, current.face_height, alpha),
        left_eye_open=current.left_eye_open,
        right_eye_open=current.right_eye_open,
        mouth_open=current.mouth_open,
        head_pose=HeadPose(
            0.0,
            0.0,
            0.0,
            _lerp(previous.head_pose.pitch_degrees, current.head_pose.pitch_degrees, alpha),
            _lerp_angle(previous.head_pose.yaw_degrees, current.head_pose.yaw_degrees, alpha),
            _lerp_angle(previous.head_pose.roll_degrees, current.head_pose.roll_degrees, alpha),
        ),
    )


def _weighted_angle(values: Iterable[tuple[float, float]]) -> float:
    sine = 0.0
    cosine = 0.0
    for angle, weight in values:
        radians = math.radians(angle)
        sine += math.sin(radians) * weight
        cosine += math.cos(radians) * weight
    return math.degrees(math.atan2(sine, cosine))


def _lerp(start: float, end: float, alpha: float) -> float:
    return start + (end - start) * alpha


def _lerp_angle(start: float, end: float, alpha: float) -> float:
    delta = (end - start + 180.0) % 360.0 - 180.0
    return (start + delta * alpha + 180.0) % 360.0 - 180.0


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))
