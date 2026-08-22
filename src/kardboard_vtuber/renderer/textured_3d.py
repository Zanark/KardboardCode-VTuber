"""GPU-rendered textured low-poly KardboardCode head."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import moderngl
import numpy as np
from numpy import ndarray

from kardboard_vtuber.tracking.models import FaceTrackingState

_VERTEX_SHADER = """
#version 330

uniform mat4 u_projection;
uniform mat4 u_model;

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;
in vec3 in_color;
in float in_textured;

out vec3 v_normal;
out vec2 v_uv;
out vec3 v_color;
out float v_textured;

void main() {
    gl_Position = u_projection * u_model * vec4(in_position, 1.0);
    v_normal = normalize(mat3(u_model) * in_normal);
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
    box_depth_multiplier: float = 1.55
    upward_bias: float = 0.12
    fov_degrees: float = 42.0
    mirrored: bool = False

    def __post_init__(self) -> None:
        if self.pixel_scale < 1:
            raise ValueError("pixel_scale must be at least 1")
        if min(
            self.box_width_multiplier,
            self.box_height_multiplier,
            self.box_depth_multiplier,
        ) <= 0:
            raise ValueError("box dimensions must be positive")
        if not 10.0 <= self.fov_degrees <= 100.0:
            raise ValueError("fov_degrees must be between 10 and 100")


class Textured3DCardboardRenderer:
    """Renders a textured 3D cardboard head into an offscreen OpenGL framebuffer."""

    def __init__(self, config: Textured3DRendererConfig | None = None) -> None:
        self._config = config or Textured3DRendererConfig()
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
                    "3f 3f 2f 3f 1f",
                    "in_position",
                    "in_normal",
                    "in_uv",
                    "in_color",
                    "in_textured",
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
        target_depth = state.face_width * frame_width * self._config.box_depth_multiplier
        center_x = state.center_x * frame_width
        center_y = state.center_y * frame_height - target_height * self._config.upward_bias
        world_x = (center_x - frame_width / 2.0) * world_per_pixel
        world_y = -(center_y - frame_height / 2.0) * world_per_pixel

        projection = _perspective(
            fov,
            frame_width / frame_height,
            0.1,
            100.0,
        )
        scale = _scale(
            target_width * world_per_pixel,
            target_height * world_per_pixel,
            target_depth * world_per_pixel,
        )
        pitch = math.radians(state.head_pose.pitch_degrees)
        yaw = math.radians(state.head_pose.yaw_degrees)
        roll = math.radians(state.head_pose.roll_degrees)
        rotation = _rotation_z(roll) @ _rotation_y(yaw) @ _rotation_x(pitch)
        translation = _translation(world_x, world_y, -distance)
        return projection, translation @ rotation @ scale


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
    ) -> None:
        for point, uv in zip(points, uvs, strict=True):
            self.vertices.append(
                [
                    *point,
                    *normal,
                    *uv,
                    *color,
                    1.0 if textured else 0.0,
                ]
            )

    def quad(
        self,
        points: tuple[tuple[float, float, float], ...],
        normal: tuple[float, float, float],
        uvs: tuple[tuple[float, float], ...],
        color: tuple[float, float, float],
        textured: bool,
    ) -> None:
        self.triangle(
            (points[0], points[1], points[2]),
            normal,
            (uvs[0], uvs[1], uvs[2]),
            color,
            textured,
        )
        self.triangle(
            (points[0], points[2], points[3]),
            normal,
            (uvs[0], uvs[2], uvs[3]),
            color,
            textured,
        )


def _build_character_mesh() -> ndarray:
    builder = _MeshBuilder()
    cardboard = (0.72, 0.47, 0.23)
    dark_cardboard = (0.34, 0.20, 0.09)
    edge_cardboard = (0.50, 0.31, 0.13)
    white = (0.78, 0.75, 0.66)
    cushion = (0.13, 0.12, 0.10)
    generic_uv = ((0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0))

    builder.quad(
        ((-0.5, -0.38, 0.5), (0.5, -0.38, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)),
        (0.0, 0.0, 1.0),
        ((0.5, 0.12), (1.0, 0.12), (1.0, 1.0), (0.5, 1.0)),
        cardboard,
        True,
    )
    builder.quad(
        ((-0.5, -0.5, 0.5), (-0.18, -0.5, 0.5), (0.0, -0.38, 0.5), (-0.5, -0.38, 0.5)),
        (0.0, 0.0, 1.0),
        ((0.5, 0.0), (0.66, 0.0), (0.75, 0.12), (0.5, 0.12)),
        cardboard,
        True,
    )
    builder.quad(
        ((0.0, -0.38, 0.5), (0.18, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.38, 0.5)),
        (0.0, 0.0, 1.0),
        ((0.75, 0.12), (0.84, 0.0), (1.0, 0.0), (1.0, 0.12)),
        cardboard,
        True,
    )
    builder.quad(
        ((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5)),
        (-1.0, 0.0, 0.0),
        generic_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)),
        (1.0, 0.0, 0.0),
        generic_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5)),
        (0.0, 1.0, 0.0),
        generic_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((0.5, -0.38, -0.5), (-0.5, -0.38, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5)),
        (0.0, 0.0, -1.0),
        generic_uv,
        dark_cardboard,
        True,
    )
    builder.quad(
        ((0.5, -0.5, -0.5), (0.18, -0.5, -0.5), (0.0, -0.38, -0.5), (0.5, -0.38, -0.5)),
        (0.0, 0.0, -1.0),
        generic_uv,
        dark_cardboard,
        True,
    )
    builder.quad(
        ((0.0, -0.38, -0.5), (-0.18, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.38, -0.5)),
        (0.0, 0.0, -1.0),
        generic_uv,
        dark_cardboard,
        True,
    )

    builder.quad(
        ((-0.5, -0.5, 0.5), (-0.18, -0.5, 0.5), (-0.14, -0.65, 0.64), (-0.51, -0.64, 0.63)),
        (0.0, -0.70, 0.72),
        generic_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((0.18, -0.5, 0.5), (0.5, -0.5, 0.5), (0.51, -0.64, 0.63), (0.14, -0.65, 0.64)),
        (0.0, -0.70, 0.72),
        generic_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((-0.5, -0.5, -0.32), (-0.5, -0.5, 0.32), (-0.62, -0.61, 0.37), (-0.62, -0.61, -0.37)),
        (-0.72, -0.69, 0.0),
        generic_uv,
        cardboard,
        True,
    )
    builder.quad(
        ((0.5, -0.5, 0.32), (0.5, -0.5, -0.32), (0.62, -0.61, -0.37), (0.62, -0.61, 0.37)),
        (0.72, -0.69, 0.0),
        generic_uv,
        cardboard,
        True,
    )

    front_edges = (
        ((-0.5, 0.5), (0.5, 0.5)),
        ((-0.5, -0.5), (-0.5, 0.5)),
        ((0.5, -0.5), (0.5, 0.5)),
        ((-0.5, -0.5), (-0.18, -0.5)),
        ((-0.18, -0.5), (0.0, -0.38)),
        ((0.0, -0.38), (0.18, -0.5)),
        ((0.18, -0.5), (0.5, -0.5)),
    )
    for start, end in front_edges:
        _add_edge_bar(builder, start, end, 0.515, 0.028, 0.045, dark_cardboard)
        _add_edge_bar(builder, start, end, 0.541, 0.010, 0.012, edge_cardboard)
    flap_edges = (
        ((-0.51, -0.64), (-0.14, -0.65)),
        ((0.14, -0.65), (0.51, -0.64)),
    )
    for start, end in flap_edges:
        _add_edge_bar(builder, start, end, 0.71, 0.024, 0.035, dark_cardboard)

    _add_cylinder(builder, -0.57, -0.02, 0.0, 0.15, 0.22, white)
    _add_cylinder(builder, 0.57, -0.02, 0.0, 0.15, 0.22, white)
    _add_cylinder(builder, -0.49, -0.02, 0.0, 0.028, 0.17, cushion)
    _add_cylinder(builder, 0.49, -0.02, 0.0, 0.028, 0.17, cushion)
    for angle_degrees in range(15, 166, 15):
        angle = math.radians(angle_degrees)
        center = (0.58 * math.cos(angle), 0.30 + 0.50 * math.sin(angle), -0.12)
        _add_rotated_box(
            builder,
            center,
            (0.18, 0.09, 0.14),
            angle - math.pi / 2.0,
            white,
        )

    return np.asarray(builder.vertices, dtype=np.float32)


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


def _add_rotated_box(
    builder: _MeshBuilder,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    angle: float,
    color: tuple[float, float, float],
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
        builder.quad(tuple(points[index] for index in indices), normal, uv, color, False)


def _add_edge_bar(
    builder: _MeshBuilder,
    start: tuple[float, float],
    end: tuple[float, float],
    z: float,
    thickness: float,
    depth: float,
    color: tuple[float, float, float],
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

    front_x = width // 2
    tape = (105, 112, 112)
    cv2.rectangle(texture, (front_x + 220, 0), (front_x + 286, 92), tape, -1)
    cv2.rectangle(texture, (front_x + 218, 395), (front_x + 288, 511), tape, -1)
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
    cv2.rectangle(texture, (front_x + 36, 421), (front_x + 112, 493), (50, 62, 180), 5)
    cv2.line(
        texture,
        (front_x + 53, 441),
        (front_x + 95, 475),
        (50, 62, 180),
        5,
        cv2.LINE_8,
    )
    cv2.line(
        texture,
        (front_x + 95, 441),
        (front_x + 53, 475),
        (50, 62, 180),
        5,
        cv2.LINE_8,
    )
    _draw_texture_eye(texture, "K", front_x + 178, 285, left_closed)
    _draw_texture_eye(texture, "C", front_x + 375, 285, right_closed)
    return texture


def _draw_texture_eye(
    texture: ndarray,
    letter: str,
    center_x: int,
    center_y: int,
    closed: bool,
) -> None:
    color = (22, 25, 27)
    if closed:
        cv2.ellipse(
            texture,
            (center_x, center_y),
            (62, 25),
            0,
            180,
            360,
            color,
            14,
            cv2.LINE_8,
        )
        return
    font_scale = 4.6
    thickness = 14
    (text_width, text_height), _ = cv2.getTextSize(
        letter,
        cv2.FONT_HERSHEY_DUPLEX,
        font_scale,
        thickness,
    )
    cv2.putText(
        texture,
        letter,
        (center_x - text_width // 2, center_y + text_height // 2),
        cv2.FONT_HERSHEY_DUPLEX,
        font_scale,
        color,
        thickness,
        cv2.LINE_8,
    )


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
