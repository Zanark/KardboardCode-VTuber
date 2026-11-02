"""Declarative control inventory and source-free, validated preset persistence."""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from kardboard_vtuber.app_paths import RESOURCE_ROOT, command_prefix, data_root, recordings_root
from kardboard_vtuber.cli import build_parser, validate_options

SettingValue: TypeAlias = bool | int | float | str | None
ROOT = RESOURCE_ROOT
LIVE_FIELDS = frozenset(
    {
        "brightness",
        "blink_threshold",
        "left_blink_threshold",
        "right_blink_threshold",
        "eye_open_threshold",
        "wink_threshold",
        "wink_min_difference",
        "action_hold_ms",
        "eye_action_hold_ms",
    }
)
PRIVATE_FIELDS = frozenset({"source", "debug_face_preview"})
PATH_FIELDS = frozenset(
    {
        "face_model",
        "hand_model",
        "segmentation_model",
        "pose_model",
    }
)


@dataclass(frozen=True, slots=True)
class Field:
    name: str
    label: str
    kind: str = "auto"
    hint: str = ""


PAGES: dict[str, tuple[Field, ...]] = {
    "Camera": (
        Field("source", "Camera / stream / recording", "source"),
        Field("backend", "Capture backend"),
        Field("width", "Requested width (auto when off)"),
        Field("height", "Requested height (auto when off)"),
        Field("fps", "Requested FPS (auto when off)"),
        Field("rotate", "Frame rotation"),
        Field("mirror", "Mirror the incoming image"),
        Field("input_already_mirrored", "Recording is already mirrored"),
        Field(
            "brightness",
            "Internal tracking brightness",
            "slider100",
            "Processing only. Does not brighten the visible camera or virtual output.",
        ),
        Field(
            "tracking_width",
            "Face tracking input width",
            hint="1280 can retain more distant detail; it is not a guaranteed distance fix.",
        ),
        Field("duration", "Stop after seconds (unlimited when off)"),
        Field("preview_height", "Local preview maximum height"),
        Field(
            "headless",
            "Suppress preview; keep processing / output",
            hint="The studio remains open. Video delivery continues without drawing a preview.",
        ),
    ),
    "Avatar & eyes": (
        Field("render_cardboard", "Render the privacy-first cardboard head"),
        Field("track_face", "Enable face tracking"),
        Field("cardboard_renderer", "Avatar renderer"),
        Field("physics", "Spring-driven flap physics (textured 3D only)"),
        Field(
            "box_depth_offset",
            "Perspective depth offset",
            "depth",
            "At least -1. Positive moves the box backward; enter a number directly.",
        ),
        Field("no_motion_filter", "Disable One Euro motion smoothing"),
        Field(
            "blink_threshold",
            "Shared blink threshold",
            "slider",
            "Baseline for either eye when its independent override is off.",
        ),
        Field(
            "left_blink_threshold",
            "Your LEFT eye / K blink threshold",
            "slider",
            "Independent anatomical eye. Lower values make closure less sensitive.",
        ),
        Field(
            "right_blink_threshold",
            "Your RIGHT eye / C blink threshold",
            "slider",
            "Independent anatomical eye. This is not mirrored screen-side naming.",
        ),
        Field("wink_threshold", "Wink closure threshold", "slider"),
        Field("eye_open_threshold", "Opposite eye must be open", "slider"),
        Field("wink_min_difference", "Minimum wink asymmetry", "slider"),
        Field("eye_action_hold_ms", "Eye debounce (milliseconds)"),
        Field("action_hold_ms", "Face / mouth debounce (milliseconds)"),
    ),
    "Output & effects": (
        Field(
            "virtual_camera",
            "Send clean video to OBS Virtual Camera",
            hint="Automatically enables cardboard rendering and face tracking.",
        ),
        Field("virtual_camera_width", "Virtual output width (even)"),
        Field("virtual_camera_height", "Virtual output height (even)"),
        Field("virtual_camera_fps", "Advertised output FPS"),
        Field("green_screen", "Replace the background with chroma green"),
        Field("segmentation_width", "Segmentation input width"),
        Field(
            "hand_occlusion",
            "Restore anatomical hands / forearms",
            hint="RGB approximation, not arbitrary object depth. Finger gaps retain cardboard.",
        ),
        Field("hand_tracking_width", "Hand tracking input width"),
    ),
    "Tracking labs": (
        Field("full_body", "Separate line-skeleton diagnostic"),
        Field("body_head_fallback", "Experimental calibrated shoulder fallback"),
        Field(
            "hood_marker_tracking",
            "Experimental green / blue hood markers",
            hint="Green: your left. Blue: your right. No markers is NOT proof of a rear view.",
        ),
        Field("pose_tracking_width", "Pose tracking input width"),
        Field("tracking_debug", "Local face mesh / pose / FPS diagnostics"),
        Field(
            "debug_face_preview",
            "RAW FACE preview (local only, explicit consent)",
            hint="Privacy-breaking. Never sent to virtual output and never saved in a preset.",
        ),
    ),
    "Models": (
        Field("face_model", "Face Landmarker model"),
        Field("hand_model", "Hand Landmarker model"),
        Field("segmentation_model", "Selfie Segmenter model"),
        Field("pose_model", "Pose Landmarker model"),
    ),
}

MODEL_SCRIPTS = {
    "face_model": "download_face_landmarker_model.py",
    "hand_model": "download_hand_landmarker_model.py",
    "segmentation_model": "download_selfie_segmenter_model.py",
    "pose_model": "download_pose_landmarker_model.py",
}


def parser_actions() -> dict[str, argparse.Action]:
    return {action.dest: action for action in build_parser()._actions if action.dest != "help"}


def defaults() -> dict[str, SettingValue]:
    values = {
        name: str(value) if isinstance(value, Path) else value
        for name, value in vars(build_parser().parse_args([])).items()
    }
    values.update(
        {
            "source": os.environ.get("KARDBOARD_CAMERA_URL") or "0",
            "render_cardboard": True,
            "physics": True,
            "mirror": True,
            "tracking_width": 1280,
        }
    )
    return values


def namespace(values: dict[str, SettingValue]) -> argparse.Namespace:
    actions = parser_actions()
    if set(values) != set(actions):
        raise ValueError("Studio settings do not match the current CLI option inventory")
    converted: dict[str, object] = {}
    for name, action in actions.items():
        value = values[name]
        if value is None:
            if action.default is not None:
                raise ValueError(f"{name} cannot be empty")
            converted[name] = None
            continue
        if isinstance(action, argparse._StoreTrueAction):
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be a boolean")
            converted[name] = value
            continue
        if isinstance(value, bool):
            raise ValueError(f"{name} has the wrong value type")
        try:
            if action.type is int:
                if not isinstance(value, int):
                    raise ValueError("expected an integer")
                converted[name] = value
            elif action.type is Path:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("expected a model path")
                if "://" in value:
                    raise ValueError("expected a local model file, not a URL")
                path = Path(value).expanduser()
                converted[name] = path if path.is_absolute() else data_root() / path
            elif action.type is not None:
                if not isinstance(value, (int, float)):
                    raise ValueError("expected a number")
                if not math.isfinite(value):
                    raise ValueError("expected a finite number")
                converted[name] = action.type(str(value))
            else:
                if not isinstance(value, str):
                    raise ValueError("expected text")
                converted[name] = value
        except (ValueError, argparse.ArgumentTypeError) as error:
            raise ValueError(f"{name}: {error}") from error
        if action.choices is not None and converted[name] not in action.choices:
            raise ValueError(f"{name} is not a supported choice")
    args = argparse.Namespace(**converted)
    validate_options(args, inspect_source=False)
    return args


def arguments(values: dict[str, SettingValue]) -> list[str]:
    args = namespace(values)
    result: list[str] = []
    for name, value in vars(args).items():
        if value is None or value is False:
            continue
        if name == "source":
            result.append("--source=" + str(value))
            continue
        result.append("--" + name.replace("_", "-"))
        if value is not True:
            result.append(str(value))
    return result


def command_preview(values: dict[str, SettingValue]) -> str:
    source = values["source"]
    local = isinstance(source, str) and source.isdecimal()
    safe = dict(values, source=source if local else "$env:KARDBOARD_CAMERA_URL")
    argv = arguments(safe)
    lines = (
        []
        if local
        else [
            '$env:KARDBOARD_CAMERA_URL = Read-Host "Camera source (kept out of presets)"',
        ]
    )
    lines.append(command_prefix("kardboard_vtuber") + " `")
    for index, value in enumerate(argv):
        if value.startswith("--"):
            part = value
            if index + 1 < len(argv) and not argv[index + 1].startswith("--"):
                item = argv[index + 1]
                quoted = item if item.startswith("$env:") else "'" + item.replace("'", "''") + "'"
                part += " " + quoted
            lines.append("  " + part + " `")
    lines[-1] = lines[-1].removesuffix(" `")
    return "\n".join(lines)


def save_preset(path: Path, values: dict[str, SettingValue]) -> None:
    namespace(values)
    safe = {name: value for name, value in values.items() if name not in PRIVATE_FIELDS}
    payload = json.dumps({"schemaVersion": 1, "options": safe}, indent=2, allow_nan=False)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(payload + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load_preset(path: Path, current: dict[str, SettingValue]) -> dict[str, SettingValue]:
    if path.stat().st_size > 64_000:
        raise ValueError("Preset is too large (maximum 64 KB)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schemaVersion", "options"}:
        raise ValueError("Not a studio preset")
    if (
        type(data["schemaVersion"]) is not int
        or data["schemaVersion"] != 1
        or not isinstance(data["options"], dict)
    ):
        raise ValueError("Unsupported preset schema")
    allowed = set(defaults()) - PRIVATE_FIELDS
    if set(data["options"]) - allowed:
        raise ValueError(
            "Preset contains unknown or private fields; source/raw consent are not imported",
        )
    values = dict(current)
    values.update(data["options"])
    values["debug_face_preview"] = False
    namespace(values)
    return values


def required_models(values: dict[str, SettingValue]) -> tuple[str, ...]:
    args = namespace(values)
    names: list[str] = []
    if any(
        (
            args.track_face,
            args.render_cardboard,
            args.physics,
            args.full_body,
            args.body_head_fallback,
            args.hood_marker_tracking,
            args.tracking_debug,
            args.debug_face_preview,
        )
    ):
        names.append("face_model")
    if args.hand_occlusion:
        names.append("hand_model")
    if args.green_screen:
        names.append("segmentation_model")
    if args.full_body or args.body_head_fallback or args.hood_marker_tracking:
        names.append("pose_model")
    return tuple(name for name in names if not getattr(args, name).is_file())


@dataclass(frozen=True, slots=True)
class RecordingOptions:
    full_body: bool = False
    free_recording: bool = False
    duration: float = 90.0
    pose_tracking_width: int = 320
    pose_tracking_fps: float = 10.0
    output_dir: str = str(recordings_root())
    name: str = "KardboardCode-studio-session"
    countdown: float = 3.0
    preview_height: int = 720

    def arguments(self, values: dict[str, SettingValue], stop_file: Path) -> list[str]:
        args = namespace(values)
        if not math.isfinite(self.duration) or self.duration <= 0:
            raise ValueError("Recording duration must be positive and finite")
        if not math.isfinite(self.pose_tracking_fps) or self.pose_tracking_fps <= 0:
            raise ValueError("Pose recording FPS must be positive and finite")
        if not math.isfinite(self.countdown) or self.countdown < 0:
            raise ValueError("Countdown must be finite and nonnegative")
        if self.pose_tracking_width <= 0 or self.preview_height < 240:
            raise ValueError("Pose width must be positive; preview height must be at least 240")
        if not self.name or any(char in self.name for char in '\\/:*?"<>|'):
            raise ValueError("Recording name must be a filename stem, without directory separators")
        if not self.output_dir.strip():
            raise ValueError("Choose a private recording output folder")
        options = {
            "source": args.source,
            "backend": args.backend,
            "rotate": args.rotate,
            "mirror": args.mirror,
            "brightness": args.brightness,
            "tracking_width": args.tracking_width,
            "face_model": args.face_model,
            "pose_model": args.pose_model,
            "full_body": self.full_body,
            "free_recording": self.free_recording,
            "duration": self.duration,
            "pose_tracking_width": self.pose_tracking_width,
            "pose_tracking_fps": self.pose_tracking_fps,
            "output_dir": self.output_dir,
            "name": self.name,
            "countdown": self.countdown,
            "preview_height": self.preview_height,
            "stop_file": stop_file,
        }
        result: list[str] = []
        for key, value in options.items():
            if value is False:
                continue
            if key == "source":
                result.append("--source=" + str(value))
                continue
            result.append("--" + key.replace("_", "-"))
            if value is not True:
                result.append(str(value))
        return result
