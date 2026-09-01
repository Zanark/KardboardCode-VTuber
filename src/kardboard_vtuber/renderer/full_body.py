"""Pose-driven low-resolution body attached beneath the cardboard head."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy import ndarray

from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    PoseLandmark,
    pose_torso_is_plausible,
)
from kardboard_vtuber.tracking.models import FaceTrackingState

_LEFT_ARM = ((11, 13), (13, 15))
_RIGHT_ARM = ((12, 14), (14, 16))
_LEFT_LEG = ((23, 25), (25, 27))
_RIGHT_LEG = ((24, 26), (26, 28))


@dataclass(frozen=True, slots=True)
class FullBodyRendererConfig:
    pixel_scale: int = 3
    minimum_visibility: float = 0.35

    def __post_init__(self) -> None:
        if self.pixel_scale < 1:
            raise ValueError("pixel_scale must be at least 1")
        if not 0.0 <= self.minimum_visibility <= 1.0:
            raise ValueError("minimum_visibility must be between 0 and 1")


class FullBodyAvatarRenderer:
    """Draws an opaque PS1-style body whose neck extends inside the head shell."""

    def __init__(self, config: FullBodyRendererConfig | None = None) -> None:
        self._config = config or FullBodyRendererConfig()

    def render(
        self,
        frame: ndarray,
        pose: FullBodyPoseState,
        face: FaceTrackingState,
    ) -> None:
        if not pose.detected or not pose_torso_is_plausible(pose):
            return
        frame_height, frame_width = frame.shape[:2]
        low_width = max(1, round(frame_width / self._config.pixel_scale))
        low_height = max(1, round(frame_height / self._config.pixel_scale))
        overlay = np.zeros((low_height, low_width, 3), dtype=np.uint8)
        mask = np.zeros((low_height, low_width), dtype=np.uint8)
        points = self._visible_points(pose.landmarks, low_width, low_height)

        if not all(index in points for index in (11, 12, 23, 24)):
            return
        shoulder_width = max(8.0, float(np.linalg.norm(points[11] - points[12])))
        outline = max(2, round(shoulder_width * 0.09))

        for connections, color in (
            (_LEFT_LEG, (48, 66, 92)),
            (_RIGHT_LEG, (55, 76, 106)),
            (_LEFT_ARM, (60, 82, 112)),
            (_RIGHT_ARM, (68, 92, 124)),
        ):
            for start, end in connections:
                if start not in points or end not in points:
                    continue
                thickness = (
                    shoulder_width * 0.30
                    if connections in (_LEFT_LEG, _RIGHT_LEG)
                    else shoulder_width * 0.22
                )
                _draw_limb(
                    overlay,
                    mask,
                    points[start],
                    points[end],
                    max(4, round(thickness)),
                    color,
                    outline,
                )

        torso = np.asarray(
            (points[11], points[12], points[24], points[23]),
            dtype=np.int32,
        )
        cv2.fillConvexPoly(mask, torso, 255)
        cv2.fillConvexPoly(overlay, torso, (44, 58, 82), cv2.LINE_AA)
        cv2.polylines(overlay, (torso,), True, (16, 21, 30), outline, cv2.LINE_AA)

        shoulder_center = (points[11].astype(np.float64) + points[12]) / 2.0
        if face.detected:
            neck_top = np.asarray(
                (
                    face.center_x * low_width,
                    face.center_y * low_height,
                )
            )
        else:
            neck_top = shoulder_center - np.asarray((0.0, shoulder_width * 0.45))
        _draw_limb(
            overlay,
            mask,
            neck_top,
            shoulder_center,
            max(5, round(shoulder_width * 0.20)),
            (80, 104, 136),
            outline,
        )

        for wrist in (15, 16):
            if wrist in points:
                radius = max(3, round(shoulder_width * 0.11))
                cv2.circle(mask, tuple(points[wrist]), radius, 255, -1, cv2.LINE_AA)
                cv2.circle(
                    overlay,
                    tuple(points[wrist]),
                    radius,
                    (82, 109, 146),
                    -1,
                    cv2.LINE_AA,
                )
        for ankle, heel, toe in ((27, 29, 31), (28, 30, 32)):
            if ankle in points and heel in points and toe in points:
                foot = np.asarray((points[ankle], points[heel], points[toe]), dtype=np.int32)
                cv2.fillConvexPoly(mask, foot, 255)
                cv2.fillConvexPoly(overlay, foot, (24, 28, 38), cv2.LINE_AA)

        full_overlay = cv2.resize(
            overlay,
            (frame_width, frame_height),
            interpolation=cv2.INTER_NEAREST,
        )
        full_mask = cv2.resize(
            mask,
            (frame_width, frame_height),
            interpolation=cv2.INTER_NEAREST,
        )
        cv2.copyTo(full_overlay, full_mask, frame)

    def _visible_points(
        self,
        landmarks: tuple[PoseLandmark, ...],
        width: int,
        height: int,
    ) -> dict[int, ndarray]:
        return {
            index: np.asarray(
                (
                    round(min(1.0, max(0.0, point.x)) * (width - 1)),
                    round(min(1.0, max(0.0, point.y)) * (height - 1)),
                ),
                dtype=np.int32,
            )
            for index, point in enumerate(landmarks)
            if point.visibility >= self._config.minimum_visibility
            and point.presence >= self._config.minimum_visibility
        }


def _draw_limb(
    overlay: ndarray,
    mask: ndarray,
    start: ndarray,
    end: ndarray,
    thickness: int,
    color: tuple[int, int, int],
    outline: int,
) -> None:
    start_point = tuple(np.rint(start).astype(np.int32))
    end_point = tuple(np.rint(end).astype(np.int32))
    cv2.line(
        mask,
        start_point,
        end_point,
        255,
        thickness + outline * 2,
        cv2.LINE_AA,
    )
    cv2.line(
        overlay,
        start_point,
        end_point,
        (16, 21, 30),
        thickness + outline * 2,
        cv2.LINE_AA,
    )
    cv2.line(overlay, start_point, end_point, color, thickness, cv2.LINE_AA)
