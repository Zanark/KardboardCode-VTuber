"""Generate face-free synthetic render galleries for project documentation."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from kardboard_vtuber.renderer.textured_3d import (
    Textured3DCardboardRenderer,
    Textured3DRendererConfig,
    _build_character_mesh,
)
from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    PoseLandmark,
    render_pose_skeleton_debug,
)
from kardboard_vtuber.tracking.mediapipe_tracker import (
    _FACE_OVAL,
    _INNER_LIPS,
    _LEFT_BROW,
    _LEFT_EYE,
    _NOSE_BASE,
    _NOSE_BRIDGE,
    _OUTER_LIPS,
    _RIGHT_BROW,
    _RIGHT_EYE,
    draw_tracking_debug,
)
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose, NormalizedLandmark

OUTPUT_DIRECTORY = Path(__file__).resolve().parents[1] / "docs" / "images"
BACKGROUND = (23, 17, 13)
PRIMARY_TEXT = (235, 237, 230)
SECONDARY_TEXT = (160, 148, 139)


def _state(
    *,
    timestamp_ms: int = 1,
    yaw: float = 0.0,
    pitch: float = -10.0,
    roll: float = 0.0,
    left_eye: float = 1.0,
    right_eye: float = 1.0,
    mouth: float = 0.0,
    face_width: float = 0.18,
    face_height: float = 0.15,
) -> FaceTrackingState:
    return FaceTrackingState(
        timestamp_ms=timestamp_ms,
        detected=True,
        landmarks=(),
        center_x=0.5,
        center_y=0.52,
        face_width=face_width,
        face_height=face_height,
        left_eye_open=left_eye,
        right_eye_open=right_eye,
        mouth_open=mouth,
        head_pose=HeadPose(
            translation_x=0.0,
            translation_y=0.0,
            translation_z=0.0,
            pitch_degrees=pitch,
            yaw_degrees=yaw,
            roll_degrees=roll,
        ),
    )


def _render_panel(
    width: int,
    height: int,
    tracking_state: FaceTrackingState,
    *,
    config: Textured3DRendererConfig | None = None,
) -> np.ndarray:
    renderer = Textured3DCardboardRenderer(config)
    frame = np.full((height, width, 3), BACKGROUND, dtype=np.uint8)
    renderer.render(frame, tracking_state)
    renderer.close()
    return frame


def _label(panel: np.ndarray, title: str, subtitle: str | None = None) -> np.ndarray:
    cv2.putText(
        panel,
        title,
        (20, 34),
        cv2.FONT_HERSHEY_DUPLEX,
        0.68,
        PRIMARY_TEXT,
        2,
        cv2.LINE_AA,
    )
    if subtitle:
        cv2.putText(
            panel,
            subtitle,
            (20, 58),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.43,
            SECONDARY_TEXT,
            1,
            cv2.LINE_AA,
        )
    return panel


def _write(name: str, image: np.ndarray) -> None:
    path = OUTPUT_DIRECTORY / name
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"could not write documentation image: {path}")
    print(f"{path.name}: {image.shape[1]}x{image.shape[0]}")


def _generate_angle_gallery() -> None:
    views = (
        ("UP-RIGHT", 32.0, -22.0, -3.0),
        ("UP-LEFT", -32.0, -22.0, 3.0),
        ("TOP-DOWN", 0.0, 52.0, 0.0),
        ("LOW ANGLE", 0.0, -52.0, 0.0),
        ("LEFT PROFILE", 76.0, -8.0, 0.0),
        ("RIGHT PROFILE", -76.0, -8.0, 0.0),
        ("REAR LEFT", 136.0, -8.0, 0.0),
        ("REAR RIGHT", -136.0, -8.0, 0.0),
        ("DUTCH TILT", 22.0, -12.0, 24.0),
    )
    panels = [
        _label(
            _render_panel(480, 400, _state(yaw=yaw, pitch=pitch, roll=roll)),
            title,
            f"yaw {yaw:+.0f}  pitch {pitch:+.0f}  roll {roll:+.0f}",
        )
        for title, yaw, pitch, roll in views
    ]
    image = np.vstack(
        (
            np.hstack(panels[0:3]),
            np.hstack(panels[3:6]),
            np.hstack(panels[6:9]),
        )
    )
    _write("kardboardcode-angle-gallery.png", image)


def _generate_cinematic_poses() -> None:
    poses = (
        ("CURIOUS", 18.0, 14.0, -7.0),
        ("HERO LOOK", 30.0, -20.0, -3.0),
        ("SIDE-EYE", -38.0, -8.0, 4.0),
        ("LOOKING UP", 0.0, -38.0, 0.0),
        ("LEAN LEFT", 12.0, -10.0, 25.0),
        ("LEAN RIGHT", -12.0, -10.0, -25.0),
    )
    panels = [
        _label(
            _render_panel(480, 420, _state(yaw=yaw, pitch=pitch, roll=roll)),
            title,
        )
        for title, yaw, pitch, roll in poses
    ]
    image = np.vstack((np.hstack(panels[:3]), np.hstack(panels[3:])))
    _write("kardboardcode-cinematic-poses.png", image)


def _generate_performance_states() -> None:
    performances = (
        ("OPEN / FRONT", 0.0, -10.0, 0.0, 1.0, 1.0),
        ("BLINK / FRONT", 0.0, -10.0, 0.0, 0.2, 0.2),
        ("LEFT WINK / TURN", 28.0, -12.0, -4.0, 0.2, 1.0),
        ("RIGHT WINK / TURN", -28.0, -12.0, 4.0, 1.0, 0.2),
        ("BLINK / LOOK UP", 0.0, -34.0, 0.0, 0.2, 0.2),
        ("OPEN / LOOK DOWN", 0.0, 36.0, 0.0, 1.0, 1.0),
        ("LEFT PROFILE", 66.0, -8.0, 0.0, 1.0, 1.0),
        ("RIGHT PROFILE", -66.0, -8.0, 0.0, 1.0, 1.0),
    )
    panels = [
        _label(
            _render_panel(
                420,
                360,
                _state(
                    yaw=yaw,
                    pitch=pitch,
                    roll=roll,
                    left_eye=left_eye,
                    right_eye=right_eye,
                ),
            ),
            title,
        )
        for title, yaw, pitch, roll, left_eye, right_eye in performances
    ]
    image = np.vstack((np.hstack(panels[:4]), np.hstack(panels[4:])))
    _write("kardboardcode-performance-states.png", image)


def _generate_flap_motion_sequence() -> None:
    renderer = Textured3DCardboardRenderer(
        Textured3DRendererConfig(physics_enabled=True)
    )
    frame = np.full((380, 360, 3), BACKGROUND, dtype=np.uint8)
    renderer.render(frame, _state(timestamp_ms=1))
    panels: list[np.ndarray] = []
    timestamp_ms = 1
    for title, yaw in (
        ("FAR LEFT", -24.0),
        ("LEFT", -12.0),
        ("CENTER", 0.0),
        ("RIGHT", 12.0),
        ("FAR RIGHT", 24.0),
    ):
        for _ in range(10):
            timestamp_ms += 33
            frame = np.full((380, 360, 3), BACKGROUND, dtype=np.uint8)
            renderer.render(frame, _state(timestamp_ms=timestamp_ms, yaw=yaw))
        assert renderer._flap_physics is not None
        left_angle, right_angle = np.degrees(renderer._flap_physics.angles[3:])
        panels.append(
            _label(
                frame.copy(),
                title,
                f"outer tabs {left_angle:+.0f} / {right_angle:+.0f} deg",
            )
        )
    renderer.close()
    _write("kardboardcode-flap-motion-sequence.png", np.hstack(panels))


def _generate_surface_tour() -> None:
    views = (
        ("AGED LEFT LABELS", 58.0, -8.0),
        ("RIGHT SHIPPING MARKS", -58.0, -8.0),
        ("FRAGILE TOP", 0.0, 58.0),
        ("NECK-SAFE UNDERSIDE", 0.0, -60.0),
        ("REAR NECK CHANNEL", 180.0, -18.0),
        ("HEADPHONE PROFILE", 82.0, 2.0),
    )
    panels = [
        _label(
            _render_panel(
                480,
                420,
                _state(
                    yaw=yaw,
                    pitch=pitch,
                    face_width=0.20,
                    face_height=0.17,
                ),
            ),
            title,
        )
        for title, yaw, pitch in views
    ]
    image = np.vstack((np.hstack(panels[:3]), np.hstack(panels[3:])))
    _write("kardboardcode-surface-tour.png", image)


def _assign_ellipse(
    points: list[NormalizedLandmark],
    indices: tuple[int, ...],
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    *,
    start_angle: float = 0.0,
) -> None:
    for position, index in enumerate(indices):
        angle = start_angle + 2.0 * math.pi * position / len(indices)
        points[index] = NormalizedLandmark(
            center_x + radius_x * math.cos(angle),
            center_y + radius_y * math.sin(angle),
            0.0,
        )


def _synthetic_debug_state() -> FaceTrackingState:
    points = [
        NormalizedLandmark(
            0.5 + 0.10 * math.cos(index * 0.31),
            0.49 + 0.14 * math.sin(index * 0.47),
            0.0,
        )
        for index in range(478)
    ]
    _assign_ellipse(points, _FACE_OVAL, 0.5, 0.49, 0.14, 0.20, start_angle=-math.pi / 2)
    _assign_ellipse(points, _LEFT_EYE, 0.55, 0.46, 0.035, 0.017)
    _assign_ellipse(points, _RIGHT_EYE, 0.45, 0.46, 0.035, 0.017)
    _assign_ellipse(points, _LEFT_BROW, 0.55, 0.425, 0.043, 0.012, start_angle=math.pi)
    _assign_ellipse(points, _RIGHT_BROW, 0.45, 0.425, 0.043, 0.012, start_angle=math.pi)
    _assign_ellipse(points, _OUTER_LIPS, 0.5, 0.57, 0.060, 0.028)
    _assign_ellipse(points, _INNER_LIPS, 0.5, 0.57, 0.038, 0.014)
    for position, index in enumerate(_NOSE_BRIDGE):
        fraction = position / max(len(_NOSE_BRIDGE) - 1, 1)
        points[index] = NormalizedLandmark(0.5, 0.45 + fraction * 0.085, 0.0)
    _assign_ellipse(points, _NOSE_BASE, 0.5, 0.535, 0.036, 0.014)
    return FaceTrackingState(
        timestamp_ms=1,
        detected=True,
        landmarks=tuple(points),
        center_x=0.5,
        center_y=0.49,
        face_width=0.28,
        face_height=0.40,
        left_eye_open=0.82,
        right_eye_open=0.76,
        mouth_open=0.31,
        head_pose=HeadPose(
            translation_x=0.0,
            translation_y=0.0,
            translation_z=0.0,
            pitch_degrees=-12.0,
            yaw_degrees=24.0,
            roll_degrees=-5.0,
        ),
    )


def _generate_tracking_debug_window() -> None:
    tracking_state = _synthetic_debug_state()
    frame = np.full((720, 1200, 3), BACKGROUND, dtype=np.uint8)
    renderer = Textured3DCardboardRenderer()
    renderer.render(
        frame,
        replace(
            tracking_state,
            face_width=0.14,
            face_height=0.12,
            center_x=0.38,
            center_y=0.62,
        ),
    )
    renderer.close()
    draw_tracking_debug(
        frame,
        tracking_state,
        action="left_wink",
        draw_frame_geometry=False,
    )
    cv2.putText(
        frame,
        "1200x720  30.0 FPS  4.2 ms frame age",
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (80, 255, 80),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "SYNTHETIC DEBUG INPUT - NO CAMERA PIXELS",
        (16, 690),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        SECONDARY_TEXT,
        1,
        cv2.LINE_AA,
    )
    _write("kardboardcode-tracking-debug-window.png", frame)


def _synthetic_body_state() -> FullBodyPoseState:
    coordinates = (
        (0.50, 0.08), (0.48, 0.07), (0.47, 0.07), (0.45, 0.08),
        (0.52, 0.07), (0.53, 0.07), (0.55, 0.08), (0.42, 0.10),
        (0.58, 0.10), (0.48, 0.12), (0.52, 0.12), (0.40, 0.25),
        (0.60, 0.25), (0.32, 0.40), (0.68, 0.40), (0.26, 0.55),
        (0.74, 0.55), (0.23, 0.58), (0.77, 0.58), (0.24, 0.56),
        (0.76, 0.56), (0.27, 0.53), (0.73, 0.53), (0.44, 0.55),
        (0.56, 0.55), (0.42, 0.72), (0.58, 0.72), (0.40, 0.90),
        (0.60, 0.90), (0.38, 0.94), (0.62, 0.94), (0.42, 0.96),
        (0.58, 0.96),
    )
    return FullBodyPoseState(
        timestamp_ms=1,
        landmarks=tuple(
            PoseLandmark(x=x, y=y, z=0.0, visibility=1.0, presence=1.0)
            for x, y in coordinates
        ),
    )


def _generate_body_debug_window() -> None:
    debug = render_pose_skeleton_debug(
        _synthetic_body_state(),
        width=540,
        height=720,
    )
    cv2.putText(
        debug,
        "SYNTHETIC LANDMARKS - NO CAMERA PIXELS",
        (12, 700),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        SECONDARY_TEXT,
        1,
        cv2.LINE_AA,
    )
    _write("kardboardcode-body-skeleton-debug-window.png", debug)


def _rotation_matrix(yaw: float, pitch: float, roll: float) -> np.ndarray:
    x = math.radians(pitch)
    y = math.radians(yaw)
    z = math.radians(roll)
    rotation_x = np.array(
        ((1.0, 0.0, 0.0), (0.0, math.cos(x), -math.sin(x)), (0.0, math.sin(x), math.cos(x)))
    )
    rotation_y = np.array(
        ((math.cos(y), 0.0, math.sin(y)), (0.0, 1.0, 0.0), (-math.sin(y), 0.0, math.cos(y)))
    )
    rotation_z = np.array(
        ((math.cos(z), -math.sin(z), 0.0), (math.sin(z), math.cos(z), 0.0), (0.0, 0.0, 1.0))
    )
    return rotation_z @ rotation_y @ rotation_x


def _mesh_debug_panel(
    title: str,
    *,
    yaw: float,
    pitch: float,
    roll: float = 0.0,
    mode: str,
) -> np.ndarray:
    panel = np.full((500, 560, 3), BACKGROUND, dtype=np.uint8)
    vertices = _build_character_mesh()
    positions = vertices[:, :3] @ _rotation_matrix(yaw, pitch, roll).T
    projected = np.column_stack((positions[:, 0], -positions[:, 1]))
    projected -= projected.mean(axis=0)
    scale = min(430 / max(np.ptp(projected[:, 0]), 1e-6), 380 / max(np.ptp(projected[:, 1]), 1e-6))
    projected = projected * scale + np.array((280.0, 275.0))
    triangles = []
    for start in range(0, len(vertices), 3):
        triangle = projected[start : start + 3]
        if len(triangle) != 3:
            continue
        depth = float(positions[start : start + 3, 2].mean())
        hinge = round(float(vertices[start : start + 3, 12].mean()))
        color = vertices[start : start + 3, 8:11].mean(axis=0)
        triangles.append((depth, triangle, hinge, color))
    hinge_colors = {
        0: (105, 105, 105),
        1: (255, 150, 60),
        2: (255, 230, 70),
        3: (70, 220, 255),
        4: (210, 90, 255),
        5: (90, 255, 120),
    }
    privacy_color = np.array((0.16, 0.12, 0.09))
    for _, triangle, hinge, color in sorted(triangles, key=lambda item: item[0]):
        if mode == "hinges":
            line_color = hinge_colors.get(hinge, hinge_colors[0])
        elif mode == "privacy":
            is_privacy = np.linalg.norm(color - privacy_color) < 0.03
            line_color = (80, 80, 255) if is_privacy else (60, 60, 60)
        else:
            line_color = (190, 175, 135)
        points = np.rint(triangle).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(panel, [points], True, line_color, 1, cv2.LINE_AA)
    _label(panel, title, f"yaw {yaw:+.0f}  pitch {pitch:+.0f}  roll {roll:+.0f}")
    return panel


def _generate_render_mesh_debug() -> None:
    panels = (
        _mesh_debug_panel("ALL TRIANGLES", yaw=28.0, pitch=-16.0, mode="wireframe"),
        _mesh_debug_panel("HINGE IDS 1-5", yaw=12.0, pitch=-34.0, mode="hinges"),
        _mesh_debug_panel("PRIVACY CORE", yaw=38.0, pitch=-8.0, mode="privacy"),
        _mesh_debug_panel("UNDERSIDE MESH", yaw=-18.0, pitch=-58.0, mode="wireframe"),
    )
    image = np.vstack((np.hstack(panels[:2]), np.hstack(panels[2:])))
    cv2.putText(
        image,
        "HINGES: 1 BLUE  2 CYAN  3 YELLOW  4 MAGENTA  5 GREEN  |  PRIVACY CORE: RED",
        (20, image.shape[0] - 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        PRIMARY_TEXT,
        1,
        cv2.LINE_AA,
    )
    _write("kardboardcode-render-mesh-debug.png", image)


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    _generate_angle_gallery()
    _generate_cinematic_poses()
    _generate_performance_states()
    _generate_flap_motion_sequence()
    _generate_surface_tour()
    _generate_tracking_debug_window()
    _generate_body_debug_window()
    _generate_render_mesh_debug()


if __name__ == "__main__":
    main()
