"""Body-pose fallback for keeping the cardboard head anchored during face loss."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
from numpy import ndarray

from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    PoseLandmark,
    pose_torso_is_plausible,
)
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose

_LEFT_SHOULDER = 11
_RIGHT_SHOULDER = 12


@dataclass(frozen=True, slots=True)
class BodyHeadFallbackConfig:
    minimum_landmark_confidence: float = 0.45
    coverage_scale: float = 1.12
    calibration_alpha: float = 0.15
    motion_alpha: float = 0.35
    minimum_calibration_samples: int = 5
    activation_missed_results: int = 3
    maximum_calibration_age_ms: int = 250
    maximum_state_age_ms: int = 300

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_landmark_confidence <= 1.0:
            raise ValueError("minimum_landmark_confidence must be between 0 and 1")
        if self.coverage_scale <= 0.0:
            raise ValueError("coverage_scale must be positive")
        for name in ("calibration_alpha", "motion_alpha"):
            if not 0.0 < getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be greater than 0 and at most 1")
        for name in (
            "minimum_calibration_samples",
            "activation_missed_results",
            "maximum_calibration_age_ms",
            "maximum_state_age_ms",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")


@dataclass(slots=True)
class _Calibration:
    center_x_ratio: float
    head_rise_ratio: float
    face_width_ratio: float
    face_height_ratio: float
    shoulder_roll_degrees: float
    shoulder_yaw_degrees: float
    face_pitch_degrees: float
    face_yaw_degrees: float
    face_roll_degrees: float


class BodyHeadFallback:
    """Synthesizes a conservative head observation from visible shoulders."""

    def __init__(self, config: BodyHeadFallbackConfig | None = None) -> None:
        self._config = config or BodyHeadFallbackConfig()
        self._calibration: _Calibration | None = None
        self._calibration_samples = 0
        self._fallback_state: FaceTrackingState | None = None
        self._last_face_timestamp_ms: int | None = None
        self._missed_face_results = 0

    @property
    def calibration_samples(self) -> int:
        return self._calibration_samples

    @property
    def required_calibration_samples(self) -> int:
        return self._config.minimum_calibration_samples

    @property
    def calibration_ready(self) -> bool:
        return (
            self._calibration is not None
            and self._calibration_samples >= self._config.minimum_calibration_samples
        )

    def update(
        self,
        face: FaceTrackingState,
        pose: FullBodyPoseState,
        *,
        current_timestamp_ms: int,
    ) -> FaceTrackingState:
        face_timestamp_ms = face.timestamp_ms
        face_age_ms = current_timestamp_ms - face.timestamp_ms
        if face_age_ms < 0 or face_age_ms > self._config.maximum_state_age_ms:
            face = FaceTrackingState.no_face(current_timestamp_ms)
        pose_age_ms = current_timestamp_ms - pose.timestamp_ms
        if pose_age_ms < 0 or pose_age_ms > self._config.maximum_state_age_ms:
            pose = FullBodyPoseState.empty(current_timestamp_ms)
        shoulders = self._shoulders(pose)
        new_face_result = face_timestamp_ms != self._last_face_timestamp_ms
        if new_face_result:
            self._last_face_timestamp_ms = face_timestamp_ms
        if face.detected:
            self._fallback_state = None
            self._missed_face_results = 0
            if (
                new_face_result
                and shoulders is not None
                and abs(face.timestamp_ms - pose.timestamp_ms)
                <= self._config.maximum_calibration_age_ms
            ):
                self._update_calibration(face, *shoulders)
            return face
        if new_face_result:
            self._missed_face_results += 1
        if (
            shoulders is None
            or self._calibration is None
            or self._calibration_samples < self._config.minimum_calibration_samples
            or self._missed_face_results < self._config.activation_missed_results
        ):
            self._fallback_state = None
            return face

        candidate = self._from_shoulders(pose.timestamp_ms, *shoulders)
        if self._fallback_state is not None:
            candidate = self._smooth(self._fallback_state, candidate)
        self._fallback_state = candidate
        return candidate

    def reset(self) -> None:
        self._calibration = None
        self._calibration_samples = 0
        self._fallback_state = None
        self._last_face_timestamp_ms = None
        self._missed_face_results = 0

    def render_calibration_hold(
        self,
        frame: ndarray,
        pose: FullBodyPoseState,
        *,
        current_timestamp_ms: int,
    ) -> None:
        """Show safe setup feedback while keeping the head region opaque."""

        frame_height = frame.shape[0]
        pose_age_ms = current_timestamp_ms - pose.timestamp_ms
        shoulders = (
            self._shoulders(pose)
            if 0 <= pose_age_ms <= self._config.maximum_state_age_ms
            else None
        )
        if shoulders is None:
            frame.fill(0)
            status = "WAITING FOR BODY"
        else:
            cutoff = round(
                min(
                    1.0,
                    max(shoulders[0].y, shoulders[1].y) + 0.10,
                )
                * frame_height
            )
            frame[:cutoff] = 0
            status = (
                f"CALIBRATING {self.calibration_samples}/"
                f"{self.required_calibration_samples}"
            )

        scale = max(0.65, min(1.25, frame.shape[1] / 1280.0))
        cv2.putText(
            frame,
            "BODY HEAD FALLBACK",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            (80, 255, 80),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            status,
            (24, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale * 0.85,
            (80, 210, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "FACE THE CAMERA FOR ABOUT ONE SECOND",
            (24, 116),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale * 0.72,
            (230, 230, 230),
            2,
            cv2.LINE_AA,
        )

    def _shoulders(
        self,
        pose: FullBodyPoseState,
    ) -> tuple[PoseLandmark, PoseLandmark] | None:
        if not pose.detected or not pose_torso_is_plausible(pose):
            return None
        left = pose.landmarks[_LEFT_SHOULDER]
        right = pose.landmarks[_RIGHT_SHOULDER]
        minimum = self._config.minimum_landmark_confidence
        if any(
            value < minimum
            for point in (left, right)
            for value in (point.visibility, point.presence)
        ):
            return None
        if math.sqrt(
            (right.x - left.x) ** 2
            + (right.y - left.y) ** 2
            + (right.z - left.z) ** 2
        ) < 0.025:
            return None
        return left, right

    def _update_calibration(
        self,
        face: FaceTrackingState,
        left: PoseLandmark,
        right: PoseLandmark,
    ) -> None:
        center_x, center_y, shoulder_width = _shoulder_geometry(left, right)
        sample = _Calibration(
            center_x_ratio=(face.center_x - center_x) / shoulder_width,
            head_rise_ratio=(center_y - face.center_y) / shoulder_width,
            face_width_ratio=face.face_width / shoulder_width,
            face_height_ratio=face.face_height / shoulder_width,
            shoulder_roll_degrees=_shoulder_roll(left, right),
            shoulder_yaw_degrees=_shoulder_yaw(left, right),
            face_pitch_degrees=face.head_pose.pitch_degrees,
            face_yaw_degrees=face.head_pose.yaw_degrees,
            face_roll_degrees=face.head_pose.roll_degrees,
        )
        if not _plausible_calibration(sample):
            return
        self._calibration_samples += 1
        if self._calibration is None:
            self._calibration = sample
            return
        alpha = self._config.calibration_alpha
        current = self._calibration
        self._calibration = _Calibration(
            center_x_ratio=_lerp(current.center_x_ratio, sample.center_x_ratio, alpha),
            head_rise_ratio=_lerp(current.head_rise_ratio, sample.head_rise_ratio, alpha),
            face_width_ratio=_lerp(current.face_width_ratio, sample.face_width_ratio, alpha),
            face_height_ratio=_lerp(current.face_height_ratio, sample.face_height_ratio, alpha),
            shoulder_roll_degrees=_lerp_angle(
                current.shoulder_roll_degrees,
                sample.shoulder_roll_degrees,
                alpha,
            ),
            shoulder_yaw_degrees=_lerp_angle(
                current.shoulder_yaw_degrees,
                sample.shoulder_yaw_degrees,
                alpha,
            ),
            face_pitch_degrees=_lerp(
                current.face_pitch_degrees,
                sample.face_pitch_degrees,
                alpha,
            ),
            face_yaw_degrees=_lerp_angle(
                current.face_yaw_degrees,
                sample.face_yaw_degrees,
                alpha,
            ),
            face_roll_degrees=_lerp_angle(
                current.face_roll_degrees,
                sample.face_roll_degrees,
                alpha,
            ),
        )

    def _from_shoulders(
        self,
        timestamp_ms: int,
        left: PoseLandmark,
        right: PoseLandmark,
    ) -> FaceTrackingState:
        center_x, center_y, shoulder_width = _shoulder_geometry(left, right)
        calibration = self._calibration
        assert calibration is not None
        yaw = _wrap_degrees(
            calibration.face_yaw_degrees
            + _angle_delta(
                _shoulder_yaw(left, right),
                calibration.shoulder_yaw_degrees,
            )
        )
        roll = _wrap_degrees(
            calibration.face_roll_degrees
            + _angle_delta(
                _shoulder_roll(left, right),
                calibration.shoulder_roll_degrees,
            )
        )

        coverage = self._config.coverage_scale
        return FaceTrackingState(
            timestamp_ms=timestamp_ms,
            detected=True,
            landmarks=(),
            center_x=_clamp01(center_x + calibration.center_x_ratio * shoulder_width),
            center_y=_clamp01(center_y - calibration.head_rise_ratio * shoulder_width),
            face_width=min(
                1.0,
                calibration.face_width_ratio * shoulder_width * coverage,
            ),
            face_height=min(
                1.0,
                calibration.face_height_ratio * shoulder_width * coverage,
            ),
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose(
                translation_x=0.0,
                translation_y=0.0,
                translation_z=0.0,
                pitch_degrees=calibration.face_pitch_degrees,
                yaw_degrees=yaw,
                roll_degrees=roll,
            ),
        )

    def _smooth(
        self,
        previous: FaceTrackingState,
        current: FaceTrackingState,
    ) -> FaceTrackingState:
        alpha = self._config.motion_alpha
        return FaceTrackingState(
            timestamp_ms=current.timestamp_ms,
            detected=True,
            landmarks=(),
            center_x=_lerp(previous.center_x, current.center_x, alpha),
            center_y=_lerp(previous.center_y, current.center_y, alpha),
            face_width=_lerp(previous.face_width, current.face_width, alpha),
            face_height=_lerp(previous.face_height, current.face_height, alpha),
            left_eye_open=1.0,
            right_eye_open=1.0,
            mouth_open=0.0,
            head_pose=HeadPose(
                translation_x=0.0,
                translation_y=0.0,
                translation_z=0.0,
                pitch_degrees=_lerp(
                    previous.head_pose.pitch_degrees,
                    current.head_pose.pitch_degrees,
                    alpha,
                ),
                yaw_degrees=_lerp_angle(
                    previous.head_pose.yaw_degrees,
                    current.head_pose.yaw_degrees,
                    alpha,
                ),
                roll_degrees=_lerp_angle(
                    previous.head_pose.roll_degrees,
                    current.head_pose.roll_degrees,
                    alpha,
                ),
            ),
        )


def _shoulder_geometry(
    left: PoseLandmark,
    right: PoseLandmark,
) -> tuple[float, float, float]:
    center_x = (left.x + right.x) / 2.0
    center_y = (left.y + right.y) / 2.0
    shoulder_width = math.sqrt(
        (right.x - left.x) ** 2
        + (right.y - left.y) ** 2
        + (right.z - left.z) ** 2
    )
    return center_x, center_y, shoulder_width


def _shoulder_roll(left: PoseLandmark, right: PoseLandmark) -> float:
    delta_x = right.x - left.x
    delta_y = right.y - left.y
    angle = math.degrees(math.atan2(delta_y, delta_x))
    if angle > 90.0:
        angle -= 180.0
    elif angle < -90.0:
        angle += 180.0
    return angle


def _shoulder_yaw(left: PoseLandmark, right: PoseLandmark) -> float:
    return math.degrees(math.atan2(right.z - left.z, right.x - left.x))


def _plausible_calibration(calibration: _Calibration) -> bool:
    return (
        abs(calibration.center_x_ratio) <= 0.75
        and 0.15 <= calibration.head_rise_ratio <= 1.5
        and 0.15 <= calibration.face_width_ratio <= 0.9
        and 0.2 <= calibration.face_height_ratio <= 1.2
    )


def _angle_delta(value: float, reference: float) -> float:
    return _wrap_degrees(value - reference)


def _lerp(start: float, end: float, alpha: float) -> float:
    return start + (end - start) * alpha


def _lerp_angle(start: float, end: float, alpha: float) -> float:
    return _wrap_degrees(start + _angle_delta(end, start) * alpha)


def _wrap_degrees(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))
