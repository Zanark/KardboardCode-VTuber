"""GPU-rendered textured low-poly KardboardCode head."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import moderngl
import numpy as np
from numpy import ndarray

from kardboard_vtuber.motion import DampedSpring, SpringParameters
from kardboard_vtuber.tracking.models import FaceTrackingState


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


_VERTEX_SHADER = """
#version 330

uniform mat4 u_projection;
uniform mat4 u_model;
uniform vec3 u_flap_angles;
uniform vec2 u_outer_flap_angles;

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;
in vec3 in_color;
in float in_textured;
in float in_hinge;

out vec3 v_normal;
out vec2 v_uv;
out vec3 v_color;
out float v_textured;

vec3 rotate_x(vec3 value, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec3(value.x, value.y * c - value.z * s, value.y * s + value.z * c);
}

vec3 rotate_z(vec3 value, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec3(value.x * c - value.y * s, value.x * s + value.y * c, value.z);
}

void main() {
    vec3 position = in_position;
    vec3 normal = in_normal;
    if (in_hinge > 0.5 && in_hinge < 1.5) {
        vec3 pivot = vec3(-0.5, -0.5, 0.0);
        position = pivot + rotate_z(position - pivot, u_flap_angles.x);
        normal = rotate_z(normal, u_flap_angles.x);
    } else if (in_hinge > 1.5 && in_hinge < 2.5) {
        vec3 pivot = vec3(0.5, -0.5, 0.0);
        position = pivot + rotate_z(position - pivot, u_flap_angles.y);
        normal = rotate_z(normal, u_flap_angles.y);
    } else if (in_hinge > 2.5 && in_hinge < 3.5) {
        vec3 pivot = vec3(0.0, -0.49, 0.51);
        position = pivot + rotate_x(position - pivot, u_flap_angles.z);
        normal = rotate_x(normal, u_flap_angles.z);
    } else if (in_hinge > 3.5 && in_hinge < 4.5) {
        vec3 pivot = vec3(-0.5, -0.5, 0.0);
        position = pivot + rotate_z(position - pivot, u_outer_flap_angles.x);
        normal = rotate_z(normal, u_outer_flap_angles.x);
    } else if (in_hinge > 4.5) {
        vec3 pivot = vec3(0.5, -0.5, 0.0);
        position = pivot + rotate_z(position - pivot, u_outer_flap_angles.y);
        normal = rotate_z(normal, u_outer_flap_angles.y);
    }
    gl_Position = u_projection * u_model * vec4(position, 1.0);
    v_normal = normalize(mat3(u_model) * normal);
    v_uv = in_uv;
    v_color = in_color;
    v_textured = in_textured;
}
"""

_FRAGMENT_SHADER = """
#version 330

uniform sampler2D u_texture;

in vec3 v_normal;
in vec2 v_uv;
in vec3 v_color;
in float v_textured;

out vec4 frag_color;

void main() {
    vec3 texture_color = texture(u_texture, v_uv).rgb;
    vec3 base_color = mix(v_color, texture_color, step(0.5, v_textured));
    vec3 light_direction = normalize(vec3(-0.45, 0.72, 0.85));
    float diffuse = max(dot(normalize(v_normal), light_direction), 0.0);
    float lighting = 0.42 + diffuse * 0.78;
    lighting = floor(lighting * 5.0 + 0.5) / 5.0;
    vec3 color = floor(clamp(base_color * lighting, 0.0, 1.0) * 31.0) / 31.0;
    frag_color = vec4(color, 1.0);
}
"""


@dataclass(frozen=True, slots=True)
class Textured3DRendererConfig:
    """Visual and projection tuning for the GPU renderer."""

    pixel_scale: int = 3
    box_width_multiplier: float = 2.25
    box_height_multiplier: float = 2.05
    upward_bias: float = 0.12
    fov_degrees: float = 42.0
    perspective_depth_offset: float = 0.16
    mirrored: bool = False
    physics_enabled: bool = False

    def __post_init__(self) -> None:
        if self.pixel_scale < 1:
            raise ValueError("pixel_scale must be at least 1")
        if min(
            self.box_width_multiplier,
            self.box_height_multiplier,
        ) <= 0:
            raise ValueError("box dimensions must be positive")
        if not 10.0 <= self.fov_degrees <= 100.0:
            raise ValueError("fov_degrees must be between 10 and 100")
        if (
            not math.isfinite(self.perspective_depth_offset)
            or self.perspective_depth_offset < -1.0
        ):
            raise ValueError("perspective_depth_offset must be finite and at least -1")


class Textured3DCardboardRenderer:
    """Renders a textured 3D cardboard head into an offscreen OpenGL framebuffer."""

    def __init__(self, config: Textured3DRendererConfig | None = None) -> None:
        self._config = config or Textured3DRendererConfig()
        self._flap_physics = _FlapPhysics() if self._config.physics_enabled else None
        try:
            self._context = moderngl.create_standalone_context(require=330)
        except Exception as error:
            raise RuntimeError(f"could not create offscreen OpenGL context: {error}") from error
        self._program = self._context.program(
            vertex_shader=_VERTEX_SHADER,
            fragment_shader=_FRAGMENT_SHADER,
        )
        vertices = _build_character_mesh()
        self._vertex_buffer = self._context.buffer(vertices.astype("f4").tobytes())
        self._vertex_array = self._context.vertex_array(
            self._program,
            [
                (
                    self._vertex_buffer,
                    "3f 3f 2f 3f 1f 1f",
                    "in_position",
                    "in_normal",
                    "in_uv",
                    "in_color",
                    "in_textured",
                    "in_hinge",
                )
            ],
        )
        self._texture = self._context.texture((1024, 512), 3)
        self._texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._texture.repeat_x = False
        self._texture.repeat_y = False
        self._eye_texture_key: tuple[bool, bool] | None = None
        self._framebuffer: moderngl.Framebuffer | None = None
        self._color_target: moderngl.Texture | None = None
        self._depth_target: moderngl.Renderbuffer | None = None
        self._target_size = (0, 0)
        self._last_safe_frame: ndarray | None = None
        self._context.enable(moderngl.DEPTH_TEST)
        self._program["u_texture"].value = 0
        self._program["u_flap_angles"].value = (0.0, 0.0, 0.0)
        self._program["u_outer_flap_angles"].value = (0.0, 0.0)

    def render(self, frame: ndarray, state: FaceTrackingState) -> None:
        if not state.detected:
            self._render_tracking_loss(frame)
            return
        frame_height, frame_width = frame.shape[:2]
        target_width = max(1, math.ceil(frame_width / self._config.pixel_scale))
        target_height = max(1, math.ceil(frame_height / self._config.pixel_scale))
        self._ensure_target(target_width, target_height)
        self._update_texture(state)
        assert self._framebuffer is not None
        self._framebuffer.use()
        self._context.viewport = (0, 0, target_width, target_height)
        self._framebuffer.clear(0.0, 0.0, 0.0, 0.0, depth=1.0)

        projection, model = self._matrices(frame_width, frame_height, state)
        self._program["u_projection"].write(projection.astype("f4").T.tobytes())
        self._program["u_model"].write(model.astype("f4").T.tobytes())
        if self._flap_physics is not None:
            angles = self._flap_physics.step(state)
            self._program["u_flap_angles"].value = angles[:3]
            self._program["u_outer_flap_angles"].value = angles[3:]
        self._texture.use(location=0)
        self._vertex_array.render(mode=moderngl.TRIANGLES)

        pixels = self._framebuffer.read(components=4, alignment=1)
        rgba = np.frombuffer(pixels, dtype=np.uint8).reshape(
            target_height,
            target_width,
            4,
        )
        rgba = np.flipud(rgba)
        overlay = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        alpha = rgba[:, :, 3]
        overlay_full = cv2.resize(
            overlay,
            (frame_width, frame_height),
            interpolation=cv2.INTER_NEAREST,
        )
        alpha_full = cv2.resize(
            alpha,
            (frame_width, frame_height),
            interpolation=cv2.INTER_NEAREST,
        )
        cv2.copyTo(overlay_full, alpha_full, frame)
        self._last_safe_frame = frame.copy()

    def reset(self) -> None:
        self._last_safe_frame = None
        if self._flap_physics is not None:
            self._flap_physics.reset()

    def close(self) -> None:
        self._release_target()
        self._texture.release()
        self._vertex_array.release()
        self._vertex_buffer.release()
        self._program.release()
        self._context.release()

    def _render_tracking_loss(self, frame: ndarray) -> None:
        if self._last_safe_frame is None or self._last_safe_frame.shape != frame.shape:
            frame.fill(0)
            return
        frame[:] = self._last_safe_frame

    def _ensure_target(self, width: int, height: int) -> None:
        if self._target_size == (width, height):
            return
        self._release_target()
        self._color_target = self._context.texture((width, height), 4)
        self._color_target.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._depth_target = self._context.depth_renderbuffer((width, height))
        self._framebuffer = self._context.framebuffer(
            color_attachments=[self._color_target],
            depth_attachment=self._depth_target,
        )
        self._target_size = (width, height)

    def _release_target(self) -> None:
        if self._framebuffer is not None:
            self._framebuffer.release()
        if self._color_target is not None:
            self._color_target.release()
        if self._depth_target is not None:
            self._depth_target.release()
        self._framebuffer = None
        self._color_target = None
        self._depth_target = None
        self._target_size = (0, 0)

    def _update_texture(self, state: FaceTrackingState) -> None:
        key = (
            _eye_closed(state.left_eye_open, state.right_eye_open),
            _eye_closed(state.right_eye_open, state.left_eye_open),
        )
        if key == self._eye_texture_key:
            return
        texture_bgr = _create_cardboard_texture(*key)
        texture_rgb = cv2.cvtColor(np.flipud(texture_bgr), cv2.COLOR_BGR2RGB)
        self._texture.write(texture_rgb.tobytes())
        self._eye_texture_key = key

    def _matrices(
        self,
        frame_width: int,
        frame_height: int,
        state: FaceTrackingState,
    ) -> tuple[ndarray, ndarray]:
        distance = 5.0
        fov = math.radians(self._config.fov_degrees)
        focal_pixels = frame_height / (2.0 * math.tan(fov / 2.0))
        world_per_pixel = distance / focal_pixels
        target_width = state.face_width * frame_width * self._config.box_width_multiplier
        target_height = state.face_height * frame_height * self._config.box_height_multiplier
        cube_side = max(target_width, target_height)
        center_x = state.center_x * frame_width
        center_y = state.center_y * frame_height - cube_side * self._config.upward_bias
        world_x = (center_x - frame_width / 2.0) * world_per_pixel
        world_y = -(center_y - frame_height / 2.0) * world_per_pixel

        projection = _perspective(
            fov,
            frame_width / frame_height,
            0.1,
            100.0,
        )
        scale = _scale(
            cube_side * world_per_pixel,
            cube_side * world_per_pixel,
            cube_side * world_per_pixel,
        )
        pitch = math.radians(state.head_pose.pitch_degrees)
        yaw = math.radians(state.head_pose.yaw_degrees)
        roll = math.radians(state.head_pose.roll_degrees)
        rotation = _rotation_z(roll) @ _rotation_y(yaw) @ _rotation_x(pitch)
        translation = _translation(
            world_x,
            world_y,
            -(distance + self._config.perspective_depth_offset),
        )
        return projection, translation @ rotation @ scale


class _FlapPhysics:
    _MAX_SIDE_ANGLE = math.radians(26.0)
    _MAX_FRONT_ANGLE = math.radians(24.0)
    _MAX_OUTER_ANGLE = math.radians(42.0)

    def __init__(self) -> None:
        parameters = SpringParameters(frequency_hz=2.4, damping_ratio=0.34)
        self._left = DampedSpring(parameters=parameters)
        self._right = DampedSpring(
            parameters=SpringParameters(frequency_hz=2.15, damping_ratio=0.30)
        )
        self._front = DampedSpring(
            parameters=SpringParameters(frequency_hz=2.6, damping_ratio=0.36)
        )
        self._outer_left = DampedSpring(
            parameters=SpringParameters(frequency_hz=3.8, damping_ratio=0.28)
        )
        self._outer_right = DampedSpring(
            parameters=SpringParameters(frequency_hz=3.45, damping_ratio=0.25)
        )
        self._previous_state: FaceTrackingState | None = None
        self._rest_pitch_degrees = 0.0
        self._rest_yaw_degrees = 0.0
        self._rest_roll_degrees = 0.0

    def step(self, state: FaceTrackingState) -> tuple[float, float, float, float, float]:
        previous = self._previous_state
        self._previous_state = state
        if previous is None:
            self._rest_pitch_degrees = state.head_pose.pitch_degrees
            self._rest_yaw_degrees = state.head_pose.yaw_degrees
            self._rest_roll_degrees = state.head_pose.roll_degrees
            return self.angles

        delta_seconds = (state.timestamp_ms - previous.timestamp_ms) / 1000.0
        if delta_seconds <= 0.0:
            return self.angles
        if delta_seconds > 0.25:
            self.reset()
            self._previous_state = state
            self._rest_pitch_degrees = state.head_pose.pitch_degrees
            self._rest_yaw_degrees = state.head_pose.yaw_degrees
            self._rest_roll_degrees = state.head_pose.roll_degrees
            return self.angles

        horizontal_velocity = (state.center_x - previous.center_x) / delta_seconds
        vertical_velocity = (state.center_y - previous.center_y) / delta_seconds
        relative_roll = math.radians(
            state.head_pose.roll_degrees - self._rest_roll_degrees
        )
        relative_yaw = math.radians(
            state.head_pose.yaw_degrees - self._rest_yaw_degrees
        )
        relative_pitch = math.radians(
            state.head_pose.pitch_degrees - self._rest_pitch_degrees
        )

        side_sway = -0.75 * relative_roll - 0.12 * horizontal_velocity
        left_target = _clamp(
            side_sway - 0.55 * relative_yaw,
            -self._MAX_SIDE_ANGLE,
            self._MAX_SIDE_ANGLE,
        )
        right_target = _clamp(
            side_sway + 0.55 * relative_yaw,
            -self._MAX_SIDE_ANGLE,
            self._MAX_SIDE_ANGLE,
        )
        front_target = _clamp(
            -0.75 * relative_pitch + 0.10 * vertical_velocity,
            -self._MAX_FRONT_ANGLE,
            self._MAX_FRONT_ANGLE,
        )
        outer_impulse = 0.24 * horizontal_velocity
        outer_left_target = _clamp(
            -1.8 * relative_yaw - outer_impulse,
            -self._MAX_OUTER_ANGLE,
            self._MAX_OUTER_ANGLE,
        )
        outer_right_target = _clamp(
            1.8 * relative_yaw - outer_impulse,
            -self._MAX_OUTER_ANGLE,
            self._MAX_OUTER_ANGLE,
        )
        left = self._step_bounded(
            self._left,
            left_target * 0.92,
            delta_seconds,
            self._MAX_SIDE_ANGLE,
        )
        right = self._step_bounded(
            self._right,
            right_target,
            delta_seconds,
            self._MAX_SIDE_ANGLE,
        )
        front = self._step_bounded(
            self._front,
            front_target,
            delta_seconds,
            self._MAX_FRONT_ANGLE,
        )
        outer_left = self._step_bounded(
            self._outer_left,
            outer_left_target,
            delta_seconds,
            self._MAX_OUTER_ANGLE,
        )
        outer_right = self._step_bounded(
            self._outer_right,
            outer_right_target,
            delta_seconds,
            self._MAX_OUTER_ANGLE,
        )
        return left, right, front, outer_left, outer_right

    @property
    def angles(self) -> tuple[float, float, float, float, float]:
        return (
            self._left.value,
            self._right.value,
            self._front.value,
            self._outer_left.value,
            self._outer_right.value,
        )

    def reset(self) -> None:
        self._left.reset(0.0)
        self._right.reset(0.0)
        self._front.reset(0.0)
        self._outer_left.reset(0.0)
        self._outer_right.reset(0.0)
        self._previous_state = None
        self._rest_pitch_degrees = 0.0
        self._rest_yaw_degrees = 0.0
        self._rest_roll_degrees = 0.0

    @staticmethod
    def _step_bounded(
        spring: DampedSpring,
        target: float,
        delta_seconds: float,
        limit: float,
    ) -> float:
        value = spring.step(target, delta_seconds)
        bounded = _clamp(value, -limit, limit)
        if bounded != value:
            spring.reset(bounded)
        return bounded


class _MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[list[float]] = []

    def triangle(
        self,
        points: tuple[tuple[float, float, float], ...],
        normal: tuple[float, float, float],
        uvs: tuple[tuple[float, float], ...],
        color: tuple[float, float, float],
        textured: bool,
        hinge: float = 0.0,
    ) -> None:
        for point, uv in zip(points, uvs, strict=True):
            self.vertices.append(
                [
                    *point,
                    *normal,
                    *uv,
                    *color,
                    1.0 if textured else 0.0,
                    hinge,
                ]
            )

    def quad(
        self,
        points: tuple[tuple[float, float, float], ...],
        normal: tuple[float, float, float],
        uvs: tuple[tuple[float, float], ...],
        color: tuple[float, float, float],
        textured: bool,
        hinge: float = 0.0,
    ) -> None:
        self.triangle(
            (points[0], points[1], points[2]),
            normal,
            (uvs[0], uvs[1], uvs[2]),
            color,
            textured,
            hinge,
        )
        self.triangle(
            (points[0], points[2], points[3]),
            normal,
            (uvs[0], uvs[2], uvs[3]),
            color,
            textured,
            hinge,
        )


def _build_character_mesh() -> ndarray:
    builder = _MeshBuilder()
    cardboard = (0.72, 0.47, 0.23)
    dark_cardboard = (0.34, 0.20, 0.09)
    edge_cardboard = (0.27, 0.16, 0.075)
    head_shadow = (0.16, 0.12, 0.09)
    white = (0.78, 0.75, 0.66)
    cushion_beige = (0.62, 0.52, 0.38)
    left_side_uv = ((0.0, 0.0), (0.25, 0.0), (0.25, 0.5), (0.0, 0.5))
    right_side_uv = ((0.25, 0.0), (0.5, 0.0), (0.5, 0.5), (0.25, 0.5))
    top_uv = ((0.0, 0.5), (0.25, 0.5), (0.25, 1.0), (0.0, 1.0))
    generic_uv = ((0.25, 0.5), (0.5, 0.5), (0.5, 1.0), (0.25, 1.0))

    builder.quad(
        ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)),
        (0.0, 0.0, 1.0),
        ((0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)),
        cardboard,
        True,
    )
    builder.quad(
        ((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5)),
        (-1.0, 0.0, 0.0),
        left_side_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)),
        (1.0, 0.0, 0.0),
        right_side_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5)),
        (0.0, 1.0, 0.0),
        top_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((0.5, -0.12, -0.5), (-0.5, -0.12, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5)),
        (0.0, 0.0, -1.0),
        generic_uv,
        dark_cardboard,
        True,
    )
    builder.quad(
        ((-0.5, -0.5, -0.5), (-0.16, -0.5, -0.5), (-0.12, -0.12, -0.5), (-0.5, -0.12, -0.5)),
        (0.0, 0.0, -1.0),
        generic_uv,
        dark_cardboard,
        True,
    )
    builder.quad(
        ((0.12, -0.12, -0.5), (0.16, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.12, -0.5)),
        (0.0, 0.0, -1.0),
        generic_uv,
        dark_cardboard,
        True,
    )

    _add_subtle_box_edges(builder, edge_cardboard)
    _add_bottom_flaps(builder, cardboard, dark_cardboard, generic_uv)
    _add_front_underside_flap(builder, cardboard, dark_cardboard, generic_uv)
    _add_privacy_head_volume(builder, head_shadow)

    builder.quad(
        ((-0.5, -0.5, -0.32), (-0.5, -0.5, 0.32), (-0.62, -0.61, 0.37), (-0.62, -0.61, -0.37)),
        (-0.72, -0.69, 0.0),
        generic_uv,
        cardboard,
        True,
        4.0,
    )
    builder.quad(
        ((0.5, -0.5, 0.32), (0.5, -0.5, -0.32), (0.62, -0.61, -0.37), (0.62, -0.61, 0.37)),
        (0.72, -0.69, 0.0),
        generic_uv,
        cardboard,
        True,
        5.0,
    )

    _add_cylinder_ring(builder, -0.57, -0.02, 0.0, 0.18, 0.215, 0.29, cushion_beige)
    _add_cylinder_ring(builder, 0.57, -0.02, 0.0, 0.18, 0.215, 0.29, cushion_beige)
    _add_cylinder(builder, -0.62, -0.02, 0.0, 0.20, 0.22, white)
    _add_cylinder(builder, 0.62, -0.02, 0.0, 0.20, 0.22, white)
    for angle_degrees in range(15, 166, 15):
        angle = math.radians(angle_degrees)
        center = (0.62 * math.cos(angle), 0.30 + 0.55 * math.sin(angle), -0.14)
        _add_rotated_box(
            builder,
            center,
            (0.21, 0.12, 0.18),
            angle - math.pi / 2.0,
            white,
        )
        cushion_center = (
            0.57 * math.cos(angle),
            0.30 + 0.48 * math.sin(angle),
            -0.035,
        )
        _add_rotated_box(
            builder,
            cushion_center,
            (0.18, 0.075, 0.19),
            angle - math.pi / 2.0,
            cushion_beige,
        )

    return np.asarray(builder.vertices, dtype=np.float32)


def _add_subtle_box_edges(
    builder: _MeshBuilder,
    color: tuple[float, float, float],
) -> None:
    front_edges = (
        ((-0.5, 0.5), (0.5, 0.5)),
        ((-0.5, -0.5), (-0.5, 0.5)),
        ((0.5, -0.5), (0.5, 0.5)),
        ((-0.5, -0.5), (0.5, -0.5)),
    )
    rear_edges = (
        ((-0.5, 0.5), (0.5, 0.5)),
        ((-0.5, -0.5), (-0.5, 0.5)),
        ((0.5, -0.5), (0.5, 0.5)),
        ((-0.5, -0.5), (-0.16, -0.5)),
        ((-0.16, -0.5), (-0.12, -0.12)),
        ((0.12, -0.12), (0.16, -0.5)),
        ((0.16, -0.5), (0.5, -0.5)),
    )
    for start, end in front_edges:
        _add_edge_bar(builder, start, end, 0.506, 0.012, 0.008, color)
    for start, end in rear_edges:
        _add_edge_bar(builder, start, end, -0.506, 0.012, 0.008, color)
    for x in (-0.5, 0.5):
        for y in (-0.5, 0.5):
            _add_rotated_box(builder, (x, y, 0.0), (0.012, 0.012, 1.012), 0.0, color)


def _add_bottom_flaps(
    builder: _MeshBuilder,
    cardboard: tuple[float, float, float],
    edge_color: tuple[float, float, float],
    uvs: tuple[tuple[float, float], ...],
) -> None:
    neck_left = -0.13
    neck_right = 0.13
    neck_rear = -0.5
    neck_front = 0.5
    flaps = (
        (
            (-0.5, -0.5, -0.5),
            (neck_left, -0.54, neck_rear),
            (neck_left, -0.54, neck_front),
            (-0.5, -0.5, 0.5),
        ),
        (
            (neck_right, -0.54, neck_rear),
            (0.5, -0.5, -0.5),
            (0.5, -0.5, 0.5),
            (neck_right, -0.54, neck_front),
        ),
    )
    for hinge, flap in enumerate(flaps, start=1):
        builder.quad(flap, (0.0, -1.0, 0.0), uvs, cardboard, True, float(hinge))

    border_thickness = 0.018
    border_y = -0.558
    borders = (
        (
            (neck_left - border_thickness, border_y, neck_rear),
            (neck_left, border_y, neck_rear),
            (neck_left, border_y, neck_front),
            (neck_left - border_thickness, border_y, neck_front),
        ),
        (
            (neck_right, border_y, neck_rear),
            (neck_right + border_thickness, border_y, neck_rear),
            (neck_right + border_thickness, border_y, neck_front),
            (neck_right, border_y, neck_front),
        ),
    )
    for hinge, border in enumerate(borders, start=1):
        builder.quad(border, (0.0, -1.0, 0.0), uvs, edge_color, False, float(hinge))


def _add_front_underside_flap(
    builder: _MeshBuilder,
    cardboard: tuple[float, float, float],
    edge_color: tuple[float, float, float],
    uvs: tuple[tuple[float, float], ...],
) -> None:
    flap = (
        (-0.48, -0.49, 0.51),
        (0.48, -0.49, 0.51),
        (0.32, -0.72, 0.40),
        (-0.32, -0.72, 0.40),
    )
    builder.quad(flap, _face_normal(flap[0], flap[1], flap[2]), uvs, cardboard, True, 3.0)
    _add_edge_bar(
        builder,
        (-0.32, -0.72),
        (0.32, -0.72),
        0.42,
        0.026,
        0.035,
        edge_color,
        3.0,
    )


def _add_privacy_head_volume(
    builder: _MeshBuilder,
    color: tuple[float, float, float],
) -> None:
    center = np.asarray((0.0, -0.075, 0.0), dtype=np.float64)
    radii = np.asarray((0.41, 0.545, 0.30), dtype=np.float64)
    latitude_segments = 8
    longitude_segments = 12
    uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

    def point(latitude: float, longitude: float) -> tuple[float, float, float]:
        cosine = math.cos(latitude)
        unit = np.asarray(
            (
                cosine * math.cos(longitude),
                math.sin(latitude),
                cosine * math.sin(longitude),
            ),
            dtype=np.float64,
        )
        return tuple(center + radii * unit)

    for latitude_index in range(latitude_segments):
        latitude_0 = -math.pi / 2.0 + math.pi * latitude_index / latitude_segments
        latitude_1 = -math.pi / 2.0 + math.pi * (latitude_index + 1) / latitude_segments
        for longitude_index in range(longitude_segments):
            longitude_0 = 2.0 * math.pi * longitude_index / longitude_segments
            longitude_1 = 2.0 * math.pi * (longitude_index + 1) / longitude_segments
            points = (
                point(latitude_0, longitude_0),
                point(latitude_0, longitude_1),
                point(latitude_1, longitude_1),
                point(latitude_1, longitude_0),
            )
            normal = _face_normal(points[0], points[1], points[2])
            face_center = np.mean(np.asarray(points), axis=0)
            if np.dot(np.asarray(normal), face_center - center) < 0:
                normal = tuple(-component for component in normal)
            builder.quad(points, normal, uvs, color, False)


def _face_normal(
    point_0: tuple[float, float, float],
    point_1: tuple[float, float, float],
    point_2: tuple[float, float, float],
) -> tuple[float, float, float]:
    edge_0 = np.asarray(point_1) - np.asarray(point_0)
    edge_1 = np.asarray(point_2) - np.asarray(point_0)
    normal = np.cross(edge_0, edge_1)
    length = np.linalg.norm(normal)
    if length <= 1e-9:
        return (0.0, 0.0, 1.0)
    return tuple(normal / length)


def _add_cylinder(
    builder: _MeshBuilder,
    center_x: float,
    center_y: float,
    center_z: float,
    length: float,
    radius: float,
    color: tuple[float, float, float],
    segments: int = 10,
) -> None:
    x0 = center_x - length / 2.0
    x1 = center_x + length / 2.0
    for index in range(segments):
        angle0 = 2.0 * math.pi * index / segments
        angle1 = 2.0 * math.pi * (index + 1) / segments
        y0, z0 = center_y + radius * math.cos(angle0), center_z + radius * math.sin(angle0)
        y1, z1 = center_y + radius * math.cos(angle1), center_z + radius * math.sin(angle1)
        normal = (0.0, math.cos((angle0 + angle1) / 2.0), math.sin((angle0 + angle1) / 2.0))
        builder.quad(
            ((x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1)),
            normal,
            ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
            color,
            False,
        )
        builder.triangle(
            ((x0, center_y, center_z), (x0, y1, z1), (x0, y0, z0)),
            (-1.0, 0.0, 0.0),
            ((0.5, 0.5), (1.0, 1.0), (1.0, 0.0)),
            color,
            False,
        )
        builder.triangle(
            ((x1, center_y, center_z), (x1, y0, z0), (x1, y1, z1)),
            (1.0, 0.0, 0.0),
            ((0.5, 0.5), (1.0, 0.0), (1.0, 1.0)),
            color,
            False,
        )


def _add_cylinder_ring(
    builder: _MeshBuilder,
    center_x: float,
    center_y: float,
    center_z: float,
    length: float,
    inner_radius: float,
    outer_radius: float,
    color: tuple[float, float, float],
    segments: int = 10,
) -> None:
    x0 = center_x - length / 2.0
    x1 = center_x + length / 2.0
    uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for index in range(segments):
        angle0 = 2.0 * math.pi * index / segments
        angle1 = 2.0 * math.pi * (index + 1) / segments
        cos0, sin0 = math.cos(angle0), math.sin(angle0)
        cos1, sin1 = math.cos(angle1), math.sin(angle1)
        outer0 = (center_y + outer_radius * cos0, center_z + outer_radius * sin0)
        outer1 = (center_y + outer_radius * cos1, center_z + outer_radius * sin1)
        inner0 = (center_y + inner_radius * cos0, center_z + inner_radius * sin0)
        inner1 = (center_y + inner_radius * cos1, center_z + inner_radius * sin1)
        radial_normal = (0.0, math.cos((angle0 + angle1) / 2.0), math.sin((angle0 + angle1) / 2.0))

        builder.quad(
            (
                (x0, outer0[0], outer0[1]),
                (x1, outer0[0], outer0[1]),
                (x1, outer1[0], outer1[1]),
                (x0, outer1[0], outer1[1]),
            ),
            radial_normal,
            uvs,
            color,
            False,
        )
        builder.quad(
            (
                (x0, inner1[0], inner1[1]),
                (x1, inner1[0], inner1[1]),
                (x1, inner0[0], inner0[1]),
                (x0, inner0[0], inner0[1]),
            ),
            tuple(-component for component in radial_normal),
            uvs,
            color,
            False,
        )
        builder.quad(
            (
                (x0, outer1[0], outer1[1]),
                (x0, outer0[0], outer0[1]),
                (x0, inner0[0], inner0[1]),
                (x0, inner1[0], inner1[1]),
            ),
            (-1.0, 0.0, 0.0),
            uvs,
            color,
            False,
        )
        builder.quad(
            (
                (x1, outer0[0], outer0[1]),
                (x1, outer1[0], outer1[1]),
                (x1, inner1[0], inner1[1]),
                (x1, inner0[0], inner0[1]),
            ),
            (1.0, 0.0, 0.0),
            uvs,
            color,
            False,
        )


def _add_rotated_box(
    builder: _MeshBuilder,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    angle: float,
    color: tuple[float, float, float],
    hinge: float = 0.0,
) -> None:
    half_x, half_y, half_z = (value / 2.0 for value in size)
    local = (
        (-half_x, -half_y, -half_z),
        (half_x, -half_y, -half_z),
        (half_x, half_y, -half_z),
        (-half_x, half_y, -half_z),
        (-half_x, -half_y, half_z),
        (half_x, -half_y, half_z),
        (half_x, half_y, half_z),
        (-half_x, half_y, half_z),
    )
    cos_angle, sin_angle = math.cos(angle), math.sin(angle)

    def transform(point: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = point
        return (
            center[0] + x * cos_angle - y * sin_angle,
            center[1] + x * sin_angle + y * cos_angle,
            center[2] + z,
        )

    points = tuple(transform(point) for point in local)
    faces = (
        ((0, 1, 2, 3), (0.0, 0.0, -1.0)),
        ((4, 7, 6, 5), (0.0, 0.0, 1.0)),
        ((0, 4, 5, 1), (sin_angle, -cos_angle, 0.0)),
        ((3, 2, 6, 7), (-sin_angle, cos_angle, 0.0)),
        ((0, 3, 7, 4), (-cos_angle, -sin_angle, 0.0)),
        ((1, 5, 6, 2), (cos_angle, sin_angle, 0.0)),
    )
    uv = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for indices, normal in faces:
        builder.quad(tuple(points[index] for index in indices), normal, uv, color, False, hinge)


def _add_edge_bar(
    builder: _MeshBuilder,
    start: tuple[float, float],
    end: tuple[float, float],
    z: float,
    thickness: float,
    depth: float,
    color: tuple[float, float, float],
    hinge: float = 0.0,
) -> None:
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    length = math.hypot(delta_x, delta_y)
    _add_rotated_box(
        builder,
        ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0, z),
        (length, thickness, depth),
        math.atan2(delta_y, delta_x),
        color,
        hinge,
    )


def _create_cardboard_texture(left_closed: bool, right_closed: bool) -> ndarray:
    height, width = 512, 1024
    rng = np.random.default_rng(20260823)
    low_noise = rng.integers(-12, 13, size=(32, 64), dtype=np.int16)
    noise = np.repeat(np.repeat(low_noise, 16, axis=0), 16, axis=1)
    base = np.empty((height, width, 3), dtype=np.int16)
    base[:] = (76, 128, 174)
    base += noise[:, :, None]
    texture = np.clip(base, 0, 255).astype(np.uint8)
    for y in range(18, height, 37):
        cv2.line(texture, (0, y), (width, y), (70, 120, 162), 1, cv2.LINE_8)
    for _ in range(480):
        x = int(rng.integers(0, width))
        y = int(rng.integers(0, height))
        color = (88, 142, 184) if rng.random() > 0.5 else (66, 112, 153)
        cv2.rectangle(texture, (x, y), (x + 2, y + 1), color, -1)

    _draw_shipping_decals(texture)
    front_x = width // 2
    tape = (105, 112, 112)
    cv2.rectangle(texture, (front_x + 220, 0), (front_x + 286, 92), tape, -1)
    cv2.rectangle(texture, (front_x + 28, 28), (front_x + 110, 112), (52, 80, 102), 6)
    cv2.arrowedLine(
        texture,
        (front_x + 55, 92),
        (front_x + 55, 47),
        (30, 34, 35),
        6,
        cv2.LINE_8,
        tipLength=0.3,
    )
    cv2.arrowedLine(
        texture,
        (front_x + 84, 92),
        (front_x + 84, 47),
        (30, 34, 35),
        6,
        cv2.LINE_8,
        tipLength=0.3,
    )
    _draw_texture_eye(texture, "K", front_x + 178, 285, left_closed)
    _draw_texture_eye(texture, "C", front_x + 375, 285, right_closed)
    return texture


def _draw_shipping_decals(texture: ndarray) -> None:
    paper = (126, 154, 178)
    faded_paper = (112, 142, 166)
    ink = (28, 32, 35)
    red = (48, 54, 185)

    _draw_aged_sticker(texture, (34, 306, 150, 390), paper, ink, tear_pattern=1)
    _draw_pixel_text(
        texture,
        "HANDLE",
        (45, 339),
        cv2.FONT_HERSHEY_DUPLEX,
        0.48,
        ink,
        1,
        4,
    )
    _draw_pixel_text(
        texture,
        "CARE",
        (55, 374),
        cv2.FONT_HERSHEY_PLAIN,
        1.25,
        red,
        2,
        4,
    )
    _draw_aged_sticker(texture, (148, 394, 230, 477), faded_paper, ink, tear_pattern=2)
    _draw_barcode(texture, 157, 407, 64, 43, ink)
    _draw_pixel_text(
        texture,
        "0815-L",
        (162, 469),
        cv2.FONT_HERSHEY_PLAIN,
        0.75,
        ink,
        1,
        3,
    )

    _draw_aged_sticker(texture, (292, 298, 466, 390), faded_paper, ink)
    cv2.arrowedLine(texture, (330, 360), (330, 315), ink, 6, cv2.LINE_8, tipLength=0.28)
    cv2.arrowedLine(texture, (370, 360), (370, 315), ink, 6, cv2.LINE_8, tipLength=0.28)
    _draw_pixel_text(
        texture,
        "UP",
        (400, 350),
        cv2.FONT_HERSHEY_PLAIN,
        1.35,
        ink,
        2,
        4,
    )
    _draw_aged_sticker(texture, (320, 402, 476, 476), paper, ink)
    _draw_barcode(texture, 332, 415, 132, 43, ink)

    _draw_aged_sticker(texture, (28, 42, 226, 194), faded_paper, red, border_width=6)
    _draw_pixel_text(
        texture,
        "FRAGILE",
        (46, 118),
        cv2.FONT_HERSHEY_DUPLEX,
        1.05,
        red,
        3,
        5,
    )
    cv2.line(texture, (48, 139), (204, 139), red, 4, cv2.LINE_8)
    _draw_pixel_text(
        texture,
        "DO NOT DROP",
        (54, 169),
        cv2.FONT_HERSHEY_PLAIN,
        1.0,
        red,
        1,
        4,
    )


def _draw_aged_sticker(
    texture: ndarray,
    bounds: tuple[int, int, int, int],
    paper: tuple[int, int, int],
    border: tuple[int, int, int],
    *,
    border_width: int = 4,
    tear_pattern: int = 0,
) -> None:
    left, top, right, bottom = bounds
    width = right - left
    height = bottom - top
    if tear_pattern == 1:
        relative_points = (
            (3, 15),
            (18, 2),
            (43, 5),
            (58, 0),
            (width - 25, 4),
            (width - 4, 12),
            (width - 12, 24),
            (width, 38),
            (width - 8, height - 19),
            (width - 19, height),
            (72, height - 6),
            (58, height),
            (39, height - 8),
            (21, height - 2),
            (0, height - 20),
            (7, height - 33),
            (1, 34),
        )
        stains = ((18, 21, 19, 4), (69, 10, 7, 5), (31, 58, 14, 6), (88, 43, 16, 3))
    elif tear_pattern == 2:
        relative_points = (
            (0, 8),
            (15, 1),
            (32, 6),
            (47, 2),
            (width - 11, 0),
            (width, 17),
            (width - 7, 29),
            (width - 1, 42),
            (width - 5, height - 14),
            (width - 17, height - 6),
            (width - 31, height),
            (35, height - 7),
            (22, height - 1),
            (8, height - 11),
            (3, height - 28),
            (8, 43),
            (0, 28),
        )
        stains = ((11, 16, 9, 6), (52, 8, 13, 3), (17, 61, 18, 4), (60, 49, 8, 7))
    else:
        relative_points = (
            (10, 0),
            (width - 13, 3),
            (width, 14),
            (width - 4, height - 12),
            (width - 17, height),
            (13, height - 3),
            (0, height - 18),
            (4, 11),
        )
        stains = ((24, 19, 13, 5), (63, 9, 8, 4), (44, 51, 17, 6), (91, 34, 10, 4))
    points = np.asarray(
        tuple((left + x, top + y) for x, y in relative_points),
        dtype=np.int32,
    )
    cv2.fillPoly(texture, [points], paper, cv2.LINE_8)
    cv2.polylines(texture, [points], True, border, border_width, cv2.LINE_8)
    stain = tuple(max(0, component - 22) for component in paper)
    for x_offset, y_offset, stain_width, stain_height in stains:
        x = min(right - 6, left + x_offset)
        y = min(bottom - 6, top + y_offset)
        cv2.rectangle(
            texture,
            (x, y),
            (min(right - 5, x + stain_width), y + stain_height),
            stain,
            -1,
        )


def _draw_pixel_text(
    texture: ndarray,
    text: str,
    origin: tuple[int, int],
    font: int,
    scale: float,
    color: tuple[int, int, int],
    thickness: int,
    pixel_size: int,
) -> None:
    mask = np.zeros(texture.shape[:2], dtype=np.uint8)
    cv2.putText(mask, text, origin, font, scale, 255, thickness, cv2.LINE_8)
    low_size = (
        math.ceil(mask.shape[1] / pixel_size),
        math.ceil(mask.shape[0] / pixel_size),
    )
    low_mask = cv2.resize(mask, low_size, interpolation=cv2.INTER_AREA)
    low_mask = np.where(low_mask >= 48, 255, 0).astype(np.uint8)
    block_mask = np.repeat(
        np.repeat(low_mask, pixel_size, axis=0),
        pixel_size,
        axis=1,
    )[: mask.shape[0], : mask.shape[1]]
    texture[block_mask != 0] = color


def _draw_barcode(
    texture: ndarray,
    x: int,
    y: int,
    width: int,
    height: int,
    color: tuple[int, int, int],
) -> None:
    pattern = (3, 1, 2, 1, 4, 2, 1, 3, 2, 2, 4, 1, 1, 2, 3, 1, 4, 2, 2, 1)
    cursor = x
    index = 0
    while cursor < x + width:
        bar_width = pattern[index % len(pattern)]
        cv2.rectangle(
            texture,
            (cursor, y),
            (min(x + width - 1, cursor + bar_width - 1), y + height),
            color,
            -1,
        )
        cursor += bar_width + 2
        index += 1


def _draw_texture_eye(
    texture: ndarray,
    letter: str,
    center_x: int,
    center_y: int,
    closed: bool,
) -> None:
    color = (22, 25, 27)
    if closed:
        points = tuple(
            (
                center_x + round(62 * math.cos(math.radians(angle))),
                center_y + round(25 * math.sin(math.radians(angle))),
            )
            for angle in range(180, 361, 15)
        )
        _paint_brush_stroke(texture, points, (13, 15, 14, 16), color)
        return
    if letter == "K":
        strokes = (
            (
                (
                    (center_x - 45, center_y - 74),
                    (center_x - 48, center_y - 30),
                    (center_x - 46, center_y + 18),
                    (center_x - 44, center_y + 75),
                ),
                (19, 21, 18),
            ),
            (
                (
                    (center_x - 43, center_y - 2),
                    (center_x - 7, center_y - 35),
                    (center_x + 42, center_y - 70),
                ),
                (18, 16),
            ),
            (
                (
                    (center_x - 42, center_y),
                    (center_x - 2, center_y + 31),
                    (center_x + 47, center_y + 72),
                ),
                (18, 21),
            ),
        )
    elif letter == "C":
        c_points = []
        for index, angle in enumerate(np.linspace(315.0, 45.0, 19)):
            radians = math.radians(float(angle))
            c_points.append(
                (
                    center_x + round(62 * math.cos(radians)) + (index % 3 - 1),
                    center_y + round(75 * math.sin(radians)) + ((index + 1) % 3 - 1),
                )
            )
        strokes = ((tuple(c_points), (17, 19, 21, 20, 18)),)
    else:
        raise ValueError(f"unsupported painted letter: {letter}")

    for points, widths in strokes:
        _paint_brush_stroke(texture, points, widths, color)


def _paint_brush_stroke(
    texture: ndarray,
    points: tuple[tuple[int, int], ...],
    widths: tuple[int, ...],
    color: tuple[int, int, int],
) -> None:
    pixel_size = 7
    low_height = math.ceil(texture.shape[0] / pixel_size)
    low_width = math.ceil(texture.shape[1] / pixel_size)
    mask = np.zeros((low_height, low_width), dtype=np.uint8)
    low_points = tuple(
        (round(x / pixel_size), round(y / pixel_size))
        for x, y in points
    )
    segments = tuple(zip(low_points[:-1], low_points[1:], strict=True))
    for index, (start, end) in enumerate(segments):
        width = max(2, round(widths[index % len(widths)] / pixel_size))
        cv2.line(mask, start, end, 255, width, cv2.LINE_8)
    for endpoint, width in (
        (low_points[0], widths[0]),
        (low_points[-1], widths[-1]),
    ):
        cv2.circle(
            mask,
            endpoint,
            max(1, round(width / (pixel_size * 2))),
            255,
            -1,
            cv2.LINE_8,
        )
    block_mask = np.repeat(
        np.repeat(mask, pixel_size, axis=0),
        pixel_size,
        axis=1,
    )[: texture.shape[0], : texture.shape[1]]
    texture[block_mask != 0] = color


def _eye_closed(openness: float, other_openness: float) -> bool:
    if openness <= 0.35:
        return True
    return openness <= 0.70 and other_openness >= 0.65 and (
        other_openness - openness >= 0.15
    )


def _perspective(fov: float, aspect: float, near: float, far: float) -> ndarray:
    focal = 1.0 / math.tan(fov / 2.0)
    return np.array(
        [
            [focal / aspect, 0.0, 0.0, 0.0],
            [0.0, focal, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), 2.0 * far * near / (near - far)],
            [0.0, 0.0, -1.0, 0.0],
        ],
        dtype=np.float32,
    )


def _translation(x: float, y: float, z: float) -> ndarray:
    matrix = np.eye(4, dtype=np.float32)
    matrix[:3, 3] = (x, y, z)
    return matrix


def _scale(x: float, y: float, z: float) -> ndarray:
    return np.diag((x, y, z, 1.0)).astype(np.float32)


def _rotation_x(angle: float) -> ndarray:
    sine, cosine = math.sin(angle), math.cos(angle)
    return np.array(
        (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, cosine, -sine, 0.0),
            (0.0, sine, cosine, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ),
        dtype=np.float32,
    )


def _rotation_y(angle: float) -> ndarray:
    sine, cosine = math.sin(angle), math.cos(angle)
    return np.array(
        (
            (cosine, 0.0, sine, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (-sine, 0.0, cosine, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ),
        dtype=np.float32,
    )


def _rotation_z(angle: float) -> ndarray:
    sine, cosine = math.sin(angle), math.cos(angle)
    return np.array(
        (
            (cosine, -sine, 0.0, 0.0),
            (sine, cosine, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ),
        dtype=np.float32,
    )
