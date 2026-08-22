"""Procedural low-resolution cardboard-head overlay."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from numpy import ndarray

from kardboard_vtuber.motion import DampedSpring, SpringParameters
from kardboard_vtuber.tracking.models import FaceTrackingState


@dataclass(frozen=True, slots=True)
class CardboardRendererConfig:
    """Visual and motion tuning for the first PS1-style renderer."""

    pixel_scale: int = 4
    box_width_multiplier: float = 2.05
    box_height_multiplier: float = 1.52
    opacity: float = 1.0
    mirrored: bool = False

    def __post_init__(self) -> None:
        if self.pixel_scale < 1:
            raise ValueError("pixel_scale must be at least 1")
        if self.box_width_multiplier <= 0 or self.box_height_multiplier <= 0:
            raise ValueError("box size multipliers must be positive")
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError("opacity must be between 0 and 1")


class PS1CardboardRenderer:
    """Renders one fixed KardboardCode box over a tracked face."""

    def __init__(self, config: CardboardRendererConfig | None = None) -> None:
        self._config = config or CardboardRendererConfig()
        flap_parameters = SpringParameters(frequency_hz=5.0, damping_ratio=0.62)
        self._mouth_flap = DampedSpring(parameters=flap_parameters)
        self._side_flap = DampedSpring(parameters=SpringParameters(3.0, 0.48))
        self._last_timestamp_ms: int | None = None

    def render(self, frame: ndarray, state: FaceTrackingState) -> None:
        if not state.detected:
            self.reset()
            return
        frame_height, frame_width = frame.shape[:2]
        low_width = max(1, math.ceil(frame_width / self._config.pixel_scale))
        low_height = max(1, math.ceil(frame_height / self._config.pixel_scale))
        overlay = np.zeros((low_height, low_width, 3), dtype=np.uint8)
        alpha = np.zeros((low_height, low_width), dtype=np.uint8)

        delta_seconds = self._delta_seconds(state.timestamp_ms)
        mouth_open = self._mouth_flap.step(state.mouth_open, delta_seconds)
        side_target = min(1.0, abs(state.head_pose.yaw_degrees) / 35.0)
        side_open = self._side_flap.step(side_target, delta_seconds)

        center_x = state.center_x * low_width
        center_y = state.center_y * low_height
        box_width = max(24.0, state.face_width * low_width * self._config.box_width_multiplier)
        box_height = max(28.0, state.face_height * low_height * self._config.box_height_multiplier)
        center_y -= box_height * 0.06
        yaw = max(-1.0, min(1.0, state.head_pose.yaw_degrees / 45.0))
        skew = yaw * box_width * 0.08
        left = center_x - box_width / 2
        right = center_x + box_width / 2
        top = center_y - box_height / 2
        bottom = center_y + box_height / 2
        front = np.array(
            [
                [round(left + skew), round(top)],
                [round(right + skew), round(top)],
                [round(right - skew), round(bottom)],
                [round(left - skew), round(bottom)],
            ],
            dtype=np.int32,
        )

        cardboard = (86, 142, 184)
        cardboard_light = (105, 164, 205)
        cardboard_dark = (58, 103, 139)
        outline = (24, 34, 43)
        full_alpha = round(255 * self._config.opacity)
        top_depth = max(5, round(box_height * 0.13))
        depth_x = round(-yaw * box_width * 0.10)
        top_plane = np.array(
            [
                front[0],
                front[1],
                [front[1][0] + depth_x, front[1][1] - top_depth],
                [front[0][0] + depth_x, front[0][1] - top_depth],
            ],
            dtype=np.int32,
        )
        cv2.fillConvexPoly(overlay, top_plane, cardboard_light)
        cv2.fillConvexPoly(alpha, top_plane, full_alpha)
        cv2.polylines(overlay, [top_plane], True, outline, 2, cv2.LINE_8)

        side_width = max(6, round(box_width * (0.15 + 0.07 * side_open)))
        if yaw >= 0:
            side = np.array(
                [
                    front[1],
                    [front[1][0] + side_width, front[1][1] - top_depth // 2],
                    [front[2][0] + side_width, front[2][1] - top_depth // 5],
                    front[2],
                ],
                dtype=np.int32,
            )
        else:
            side = np.array(
                [
                    [front[0][0] - side_width, front[0][1] - top_depth // 2],
                    front[0],
                    front[3],
                    [front[3][0] - side_width, front[3][1] - top_depth // 5],
                ],
                dtype=np.int32,
            )
        cv2.fillConvexPoly(overlay, side, cardboard_dark)
        cv2.fillConvexPoly(alpha, side, full_alpha)
        cv2.polylines(overlay, [side], True, outline, 2, cv2.LINE_8)

        cv2.fillConvexPoly(overlay, front, cardboard)
        cv2.fillConvexPoly(alpha, front, full_alpha)
        cv2.polylines(overlay, [front], True, outline, 2, cv2.LINE_8)
        self._add_cardboard_texture(overlay, alpha)
        self._cut_neck_opening(
            overlay,
            alpha,
            front,
            box_width,
            box_height,
            full_alpha,
        )
        self._draw_eyes(overlay, alpha, front, box_width, box_height, full_alpha, state)
        self._draw_flaps(
            overlay,
            alpha,
            front,
            box_width,
            box_height,
            full_alpha,
            mouth_open,
        )

        overlay_full = cv2.resize(
            overlay,
            (frame_width, frame_height),
            interpolation=cv2.INTER_NEAREST,
        )
        alpha_full = cv2.resize(
            alpha,
            (frame_width, frame_height),
            interpolation=cv2.INTER_NEAREST,
        ).astype(np.float32)[:, :, None] / 255.0
        frame[:] = (
            overlay_full.astype(np.float32) * alpha_full
            + frame.astype(np.float32) * (1.0 - alpha_full)
        ).astype(np.uint8)

    def reset(self) -> None:
        self._mouth_flap.reset(0.0)
        self._side_flap.reset(0.0)
        self._last_timestamp_ms = None

    def _delta_seconds(self, timestamp_ms: int) -> float:
        if self._last_timestamp_ms is None:
            self._last_timestamp_ms = timestamp_ms
            return 1.0 / 30.0
        delta_seconds = max(0.0, min(0.1, (timestamp_ms - self._last_timestamp_ms) / 1000.0))
        self._last_timestamp_ms = timestamp_ms
        return delta_seconds

    @staticmethod
    def _add_cardboard_texture(overlay: ndarray, alpha: ndarray) -> None:
        y_coordinates, x_coordinates = np.indices(alpha.shape)
        covered = alpha > 0
        light_fibers = covered & ((x_coordinates * 7 + y_coordinates * 11) % 37 == 0)
        dark_fibers = covered & ((x_coordinates * 13 + y_coordinates * 5) % 53 == 0)
        overlay[light_fibers] = np.minimum(
            overlay[light_fibers].astype(np.int16) + 12,
            255,
        ).astype(np.uint8)
        overlay[dark_fibers] = np.maximum(
            overlay[dark_fibers].astype(np.int16) - 14,
            0,
        ).astype(np.uint8)

    @staticmethod
    def _cut_neck_opening(
        overlay: ndarray,
        alpha: ndarray,
        front: ndarray,
        box_width: float,
        box_height: float,
        full_alpha: int,
    ) -> None:
        center_x = round(float(front[:, 0].mean()))
        bottom = round(float(front[:, 1].max()))
        radius_x = max(9, round(box_width * 0.27))
        radius_y = max(7, round(box_height * 0.20))
        opening_center = (center_x, bottom + 2)
        cv2.ellipse(
            alpha,
            opening_center,
            (radius_x, radius_y),
            0,
            180,
            360,
            0,
            -1,
            cv2.LINE_8,
        )
        cv2.ellipse(
            overlay,
            opening_center,
            (radius_x, radius_y),
            0,
            180,
            360,
            (0, 0, 0),
            -1,
            cv2.LINE_8,
        )
        rim_color = (42, 72, 92)
        cv2.ellipse(
            overlay,
            opening_center,
            (radius_x, radius_y),
            0,
            180,
            360,
            rim_color,
            2,
            cv2.LINE_8,
        )
        cv2.ellipse(
            alpha,
            opening_center,
            (radius_x, radius_y),
            0,
            180,
            360,
            full_alpha,
            2,
            cv2.LINE_8,
        )
        left_interior = np.array(
            [
                front[3],
                [center_x - radius_x, bottom],
                [center_x - radius_x + 3, bottom - radius_y // 2],
                [front[3][0] + round(box_width * 0.08), front[3][1] - 2],
            ],
            dtype=np.int32,
        )
        right_interior = np.array(
            [
                [center_x + radius_x, bottom],
                front[2],
                [front[2][0] - round(box_width * 0.08), front[2][1] - 2],
                [center_x + radius_x - 3, bottom - radius_y // 2],
            ],
            dtype=np.int32,
        )
        for interior in (left_interior, right_interior):
            cv2.fillConvexPoly(overlay, interior, rim_color)
            cv2.fillConvexPoly(alpha, interior, full_alpha)
            cv2.polylines(overlay, [interior], True, (24, 34, 43), 1, cv2.LINE_8)

    def _draw_eyes(
        self,
        overlay: ndarray,
        alpha: ndarray,
        front: ndarray,
        box_width: float,
        box_height: float,
        full_alpha: int,
        state: FaceTrackingState,
    ) -> None:
        center_x = float(front[:, 0].mean())
        top = float(front[:, 1].min())
        eye_y = round(top + box_height * 0.41)
        screen_eyes = (
            (("C", state.right_eye_open), ("K", state.left_eye_open))
            if self._config.mirrored
            else (("K", state.left_eye_open), ("C", state.right_eye_open))
        )
        for direction, (letter, openness) in zip((-1, 1), screen_eyes, strict=True):
            eye_x = round(center_x + direction * box_width * 0.22)
            if openness <= 0.45:
                half_width = max(4, round(box_width * 0.08))
                cv2.line(
                    overlay,
                    (eye_x - half_width, eye_y),
                    (eye_x + half_width, eye_y),
                    (18, 26, 33),
                    2,
                    cv2.LINE_8,
                )
                cv2.line(
                    alpha,
                    (eye_x - half_width, eye_y),
                    (eye_x + half_width, eye_y),
                    full_alpha,
                    2,
                    cv2.LINE_8,
                )
                continue
            font_scale = max(0.45, box_width / 105.0)
            thickness = max(2, round(box_width / 62.0))
            (text_width, text_height), _ = cv2.getTextSize(
                letter,
                cv2.FONT_HERSHEY_DUPLEX,
                font_scale,
                thickness,
            )
            origin = (round(eye_x - text_width / 2), round(eye_y + text_height / 2))
            cv2.putText(
                overlay,
                letter,
                origin,
                cv2.FONT_HERSHEY_DUPLEX,
                font_scale,
                (18, 26, 33),
                thickness,
                cv2.LINE_8,
            )
            cv2.putText(
                alpha,
                letter,
                origin,
                cv2.FONT_HERSHEY_DUPLEX,
                font_scale,
                full_alpha,
                thickness,
                cv2.LINE_8,
            )

    @staticmethod
    def _draw_flaps(
        overlay: ndarray,
        alpha: ndarray,
        front: ndarray,
        box_width: float,
        box_height: float,
        full_alpha: int,
        mouth_open: float,
    ) -> None:
        center_x = float(front[:, 0].mean())
        top = float(front[:, 1].min())
        hinge_y = round(top + box_height * 0.68)
        half_width = box_width * 0.24
        opening = box_height * 0.16 * max(0.0, min(1.0, mouth_open))
        left_flap = np.array(
            [
                [round(center_x - half_width), hinge_y],
                [round(center_x), hinge_y],
                [round(center_x - box_width * 0.04), round(hinge_y + opening + 3)],
                [round(center_x - half_width * 1.08), round(hinge_y + opening)],
            ],
            dtype=np.int32,
        )
        right_flap = np.array(
            [
                [round(center_x), hinge_y],
                [round(center_x + half_width), hinge_y],
                [round(center_x + half_width * 1.08), round(hinge_y + opening)],
                [round(center_x + box_width * 0.04), round(hinge_y + opening + 3)],
            ],
            dtype=np.int32,
        )
        for flap, color in ((left_flap, (71, 126, 169)), (right_flap, (78, 134, 177))):
            cv2.fillConvexPoly(overlay, flap, color)
            cv2.fillConvexPoly(alpha, flap, full_alpha)
            cv2.polylines(overlay, [flap], True, (24, 34, 43), 1, cv2.LINE_8)
