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
    box_height_multiplier: float = 1.75
    opacity: float = 1.0
    mirrored: bool = False
    neutral_pitch_degrees: float = -10.0

    def __post_init__(self) -> None:
        if self.pixel_scale < 1:
            raise ValueError("pixel_scale must be at least 1")
        if self.box_width_multiplier <= 0 or self.box_height_multiplier <= 0:
            raise ValueError("box size multipliers must be positive")
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError("opacity must be between 0 and 1")
        if not math.isfinite(self.neutral_pitch_degrees):
            raise ValueError("neutral_pitch_degrees must be finite")


class PS1CardboardRenderer:
    """Renders one fixed KardboardCode box over a tracked face."""

    def __init__(self, config: CardboardRendererConfig | None = None) -> None:
        self._config = config or CardboardRendererConfig()
        flap_parameters = SpringParameters(frequency_hz=5.0, damping_ratio=0.62)
        self._mouth_flap = DampedSpring(parameters=flap_parameters)
        self._side_flap = DampedSpring(parameters=SpringParameters(3.0, 0.48))
        self._last_timestamp_ms: int | None = None
        self._last_safe_frame: ndarray | None = None

    def render(self, frame: ndarray, state: FaceTrackingState) -> None:
        if not state.detected:
            self._render_tracking_loss(frame)
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
        center_y -= box_height * 0.10
        yaw = max(-1.0, min(1.0, state.head_pose.yaw_degrees / 45.0))
        pitch = max(
            -1.0,
            min(
                1.0,
                (state.head_pose.pitch_degrees - self._config.neutral_pitch_degrees) / 35.0,
            ),
        )
        look_down = max(0.0, pitch)
        look_up = max(0.0, -pitch)
        front_width = box_width * (1.0 - 0.22 * abs(yaw))
        front_height = box_height * (1.0 - 0.10 * abs(pitch))
        top_half_width = front_width * (0.5 + 0.04 * pitch)
        bottom_half_width = front_width * (0.5 - 0.04 * pitch)
        top = center_y - front_height / 2
        bottom = center_y + front_height / 2
        front = np.array(
            [
                [round(center_x - top_half_width), round(top)],
                [round(center_x + top_half_width), round(top)],
                [round(center_x + bottom_half_width), round(bottom)],
                [round(center_x - bottom_half_width), round(bottom)],
            ],
            dtype=np.int32,
        )

        cardboard = (86, 142, 184)
        cardboard_light = (105, 164, 205)
        cardboard_dark = (58, 103, 139)
        outline = (24, 34, 43)
        full_alpha = round(255 * self._config.opacity)
        top_depth = round(box_height * (0.025 * (1.0 - look_up) + 0.16 * look_down))
        bottom_depth = round(box_height * 0.16 * look_up)
        side_width = round(box_width * 0.22 * side_open)
        depth_x = (
            -round(math.copysign(side_width, yaw))
            if side_open > 0.08 and abs(yaw) > 0.01
            else 0
        )
        if top_depth > 1:
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

        if side_open > 0.08 and yaw > 0:
            side = np.array(
                [
                    [front[0][0] + depth_x, front[0][1] - top_depth],
                    front[0],
                    front[3],
                    [front[3][0] + depth_x, front[3][1] + bottom_depth],
                ],
                dtype=np.int32,
            )
        elif side_open > 0.08 and yaw < 0:
            side = np.array(
                [
                    front[1],
                    [front[1][0] + depth_x, front[1][1] - top_depth],
                    [front[2][0] + depth_x, front[2][1] + bottom_depth],
                    front[2],
                ],
                dtype=np.int32,
            )
        else:
            side = None
        if side is not None:
            cv2.fillConvexPoly(overlay, side, cardboard_dark)
            cv2.fillConvexPoly(alpha, side, full_alpha)
            cv2.polylines(overlay, [side], True, outline, 2, cv2.LINE_8)

        if bottom_depth > 1:
            center_bottom_x = round(float(front[2:4, 0].mean()))
            bottom_y = round(float(front[2:4, 1].mean()))
            neck_half_width = round(box_width * 0.16)
            underside_planes = (
                np.array(
                    [
                        front[3],
                        [center_bottom_x - neck_half_width, bottom_y],
                        [
                            center_bottom_x - neck_half_width + depth_x,
                            bottom_y + bottom_depth,
                        ],
                        [front[3][0] + depth_x, front[3][1] + bottom_depth],
                    ],
                    dtype=np.int32,
                ),
                np.array(
                    [
                        [center_bottom_x + neck_half_width, bottom_y],
                        front[2],
                        [front[2][0] + depth_x, front[2][1] + bottom_depth],
                        [
                            center_bottom_x + neck_half_width + depth_x,
                            bottom_y + bottom_depth,
                        ],
                    ],
                    dtype=np.int32,
                ),
            )
            for underside in underside_planes:
                cv2.fillConvexPoly(overlay, underside, cardboard_dark)
                cv2.fillConvexPoly(alpha, underside, full_alpha)
                cv2.polylines(overlay, [underside], True, outline, 2, cv2.LINE_8)

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
            bottom_depth,
            depth_x,
        )
        roll = max(-60.0, min(60.0, state.head_pose.roll_degrees))
        if abs(roll) > 0.5:
            rotation = cv2.getRotationMatrix2D((center_x, center_y), roll, 1.0)
            overlay = cv2.warpAffine(
                overlay,
                rotation,
                (low_width, low_height),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0),
            )
            alpha = cv2.warpAffine(
                alpha,
                rotation,
                (low_width, low_height),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
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
        self._last_safe_frame = frame.copy()

    def reset(self) -> None:
        self._mouth_flap.reset(0.0)
        self._side_flap.reset(0.0)
        self._last_timestamp_ms = None
        self._last_safe_frame = None

    def _render_tracking_loss(self, frame: ndarray) -> None:
        if self._last_safe_frame is None or self._last_safe_frame.shape != frame.shape:
            frame.fill(0)
            return
        frame[:] = self._last_safe_frame

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
        radius_x = max(9, round(box_width * 0.16))
        radius_y = max(5, round(box_height * 0.07))
        opening = np.array(
            [
                [center_x - radius_x, bottom + 2],
                [center_x, bottom - radius_y],
                [center_x + radius_x, bottom + 2],
            ],
            dtype=np.int32,
        )
        cv2.fillConvexPoly(alpha, opening, 0)
        cv2.fillConvexPoly(overlay, opening, (0, 0, 0))
        rim_color = (42, 72, 92)
        cv2.polylines(overlay, [opening], False, rim_color, 2, cv2.LINE_8)
        cv2.polylines(alpha, [opening], False, full_alpha, 2, cv2.LINE_8)
        left_interior = np.array(
            [
                front[3],
                [center_x - radius_x, bottom],
                [center_x - radius_x + 3, bottom - radius_y // 3],
                [front[3][0] + round(box_width * 0.08), front[3][1] - 2],
            ],
            dtype=np.int32,
        )
        right_interior = np.array(
            [
                [center_x + radius_x, bottom],
                front[2],
                [front[2][0] - round(box_width * 0.08), front[2][1] - 2],
                [center_x + radius_x - 3, bottom - radius_y // 3],
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
            ("K", state.left_eye_open, state.right_eye_open),
            ("C", state.right_eye_open, state.left_eye_open),
        )
        for direction, (letter, openness, other_openness) in zip(
            (-1, 1),
            screen_eyes,
            strict=True,
        ):
            eye_x = round(center_x + direction * box_width * 0.22)
            if self._eye_closed(openness, other_openness):
                half_width = max(4, round(box_width * 0.08))
                arc_height = max(2, round(box_height * 0.025))
                cv2.ellipse(
                    overlay,
                    (eye_x, eye_y + arc_height),
                    (half_width, arc_height * 2),
                    0,
                    180,
                    360,
                    (18, 26, 33),
                    2,
                    cv2.LINE_8,
                )
                cv2.ellipse(
                    alpha,
                    (eye_x, eye_y + arc_height),
                    (half_width, arc_height * 2),
                    0,
                    180,
                    360,
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
    def _eye_closed(openness: float, other_openness: float) -> bool:
        if openness <= 0.35:
            return True
        return openness <= 0.70 and other_openness >= 0.65 and (
            other_openness - openness >= 0.15
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
        bottom_depth: int,
        depth_x: int,
    ) -> None:
        center_x = float(front[2:4, 0].mean()) + depth_x
        left = float(front[3][0]) + depth_x
        right = float(front[2][0]) + depth_x
        hinge_y = round(float(front[2:4, 1].mean())) + bottom_depth
        neck_half_width = box_width * 0.16
        openness = max(0.0, min(1.0, mouth_open))
        drop = box_height * (0.025 + 0.16 * openness)
        spread = box_width * 0.10 * openness
        left_flap = np.array(
            [
                [round(left), hinge_y],
                [round(center_x - neck_half_width), hinge_y],
                [round(center_x - neck_half_width - box_width * 0.03), round(hinge_y + drop)],
                [round(left - spread), round(hinge_y + drop * 0.72)],
            ],
            dtype=np.int32,
        )
        right_flap = np.array(
            [
                [round(center_x + neck_half_width), hinge_y],
                [round(right), hinge_y],
                [round(right + spread), round(hinge_y + drop * 0.72)],
                [round(center_x + neck_half_width + box_width * 0.03), round(hinge_y + drop)],
            ],
            dtype=np.int32,
        )
        for flap, color in ((left_flap, (71, 126, 169)), (right_flap, (78, 134, 177))):
            cv2.fillConvexPoly(overlay, flap, color)
            cv2.fillConvexPoly(alpha, flap, full_alpha)
            cv2.polylines(overlay, [flap], True, (24, 34, 43), 1, cv2.LINE_8)
