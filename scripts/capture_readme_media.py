"""Capture owned native Studio widgets with synthetic data; never capture a desktop/camera."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
FRAME_MS = 200
FRAMES_PER_THEME = 30


def ensure_demo_surface(window, expected_page: str) -> None:
    if (
        window.worker is None
        or not window.worker.demo
        or window.job is not None
        or window.error_label.isVisible()
        or window.page_selector.currentText() != expected_page
    ):
        raise RuntimeError("Capture interrupted; refusing a non-demo or unexpected surface.")


def save_animation(frames: list[Image.Image], durations: list[int], output: Path) -> dict:
    if not frames or len(frames) != len(durations):
        raise ValueError("Animation needs one duration per frame.")
    if any(duration < 20 or duration % 10 for duration in durations):
        raise ValueError("GIF durations must be positive multiples of ten milliseconds.")
    if any(frame.size != frames[0].size for frame in frames):
        raise ValueError("Animation frame dimensions must match.")
    if len({hashlib.sha256(frame.tobytes()).digest() for frame in frames}) < 2:
        raise ValueError("A walkthrough must contain genuine changed frames.")
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
    with Image.open(output) as animation:
        actual_duration = sum(frame.info["duration"] for frame in ImageSequence.Iterator(animation))
        if actual_duration != sum(durations) or animation.info.get("loop") != 0:
            raise RuntimeError("Encoded GIF timing/loop differs from the intended walkthrough.")
        if animation.n_frames < 2 or animation.size != frames[0].size:
            raise RuntimeError("Encoded GIF lost its animation or dimensions.")
        receipt = {
            "file": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else output.name,
            "width": animation.width,
            "height": animation.height,
            "frames": animation.n_frames,
            "duration_ms": actual_duration,
        }
    data = output.read_bytes()
    if len(data) > 10 * 1024 * 1024:
        raise RuntimeError("README GIF exceeds the ten-megabyte media budget.")
    return {**receipt, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def capture(output: Path, evidence: Path) -> None:
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtGui import QRegion

    from kardboard_vtuber.gui.window import StudioWindow

    if __package__:
        from .capture_gui_visual_reference import ReferenceCapture
    else:
        from capture_gui_visual_reference import ReferenceCapture

    output.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    frames_by_theme: dict[str, list[Image.Image]] = {}
    program_frames: dict[str, int] = {}
    shots = []
    preserved = {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in (
            "kardboardcode-live-demo.gif",
            "kardboardcode-real-life-demo.gif",
            "kardboardcode-green-screen-demo.gif",
        )
    }
    with patch.object(StudioWindow, "refresh_native_cameras"):
        reference = ReferenceCapture(evidence)
        window, app = reference.window, reference.app
        try:
            window.page_selector.setCurrentText("Avatar & eyes")
            for name, value in (
                ("physics", True),
                ("tracking_debug", True),
                ("debug_face_preview", True),
                ("left_blink_threshold", 0.30),
                ("right_blink_threshold", 0.38),
            ):
                window.controls[name].set_value(value)
            window._refresh_settings()
            window.show_output.setChecked(False)
            window.start_demo()
            deadline = time.monotonic() + 25
            while window.preview.image.isNull() and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            if window.preview.image.isNull() or window.worker is None:
                raise RuntimeError("The real synthetic Studio demo did not start.")
            if not window.worker.demo or window.job is not None:
                raise RuntimeError("Only a synthetic demo without helper/capture jobs is allowed.")
            for theme in ("dark", "light"):
                reference.set_theme(theme)
                frames = []
                palette = None
                program_hashes = set()
                window.tools_action.setChecked(False)
                window.page_selector.setCurrentText("Avatar & eyes")
                for index in range(FRAMES_PER_THEME):
                    tick = time.monotonic()
                    if index == 10:
                        window.page_selector.setCurrentText("Output & effects")
                    elif index == 20:
                        window.page_selector.setCurrentText("Avatar & eyes")
                        window.tools_action.setChecked(True)
                        window.console_tabs.setCurrentIndex(0)
                    while time.monotonic() < tick + FRAME_MS / 1000:
                        app.processEvents()
                        time.sleep(0.005)
                    if window.worker is None or window.error_label.isVisible():
                        raise RuntimeError("Synthetic demo failed during media capture.")
                    window._poll_runtime()
                    window.timer.stop()
                    program_hashes.add(
                        hashlib.sha256(bytes(window.preview.image.constBits())).hexdigest()
                    )
                    window.raw_face.set_frame(reference.raw)
                    window.face_mesh.set_frame(reference.face)
                    window.diagnostics_notice.setText("Synthetic example diagnostics / NOT A FACE")
                    reference.settle()
                    ensure_demo_surface(
                        window, "Output & effects" if 10 <= index < 20 else "Avatar & eyes"
                    )
                    for canvas in (window.preview, window.raw_face, window.face_mesh):
                        if (
                            not canvas.isVisible()
                            or not QRegion(canvas.rect())
                            .subtracted(canvas.visibleRegion())
                            .isEmpty()
                        ):
                            raise RuntimeError(
                                "Native preview/diagnostic was clipped in the capture."
                            )
                    pixmap = window.grab()
                    if index == 4:
                        path = output / f"kardboardcode-studio-{theme}.png"
                        if not pixmap.save(str(path)):
                            raise RuntimeError("Could not save the native theme screenshot.")
                        shots.append(
                            {
                                "file": str(path.relative_to(ROOT))
                                if path.is_relative_to(ROOT)
                                else path.name,
                                "width": pixmap.width(),
                                "height": pixmap.height(),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            }
                        )
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    if not pixmap.save(buffer, "PNG"):
                        raise RuntimeError("Could not read the owned widget pixels.")
                    with Image.open(io.BytesIO(bytes(buffer.data()))) as image:
                        size = (1200, round(image.height * 1200 / image.width))
                        rgb = image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
                    if palette is None:
                        palette = rgb.quantize(colors=256, dither=Image.Dither.NONE)
                    frames.append(rgb.quantize(palette=palette, dither=Image.Dither.NONE))
                    if index in (0, 10, 20, FRAMES_PER_THEME - 1):
                        key = evidence / f"{theme}-keyframe-{index:02}.png"
                        if not pixmap.save(str(key)):
                            raise RuntimeError("Could not save the bounded review keyframe.")
                    window.timer.start()
                if len(program_hashes) < 10:
                    raise RuntimeError("The walkthrough did not contain enough actual demo motion.")
                program_frames[theme] = len(program_hashes)
                frames_by_theme[theme] = frames
        finally:
            window.stop()
            deadline = time.monotonic() + 10
            while window.worker is not None and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            if window.worker is not None:
                raise RuntimeError("Owned synthetic worker did not stop cooperatively.")
            window.output_window.close()
            window.close()
            reference.settle()
    durations = [1000, *([FRAME_MS] * (FRAMES_PER_THEME - 2)), 1000]
    animations = [
        save_animation(
            frames_by_theme[theme],
            durations,
            output / f"kardboardcode-studio-walkthrough-{theme}.gif",
        )
        for theme in ("dark", "light")
    ]
    animations.append(
        save_animation(
            frames_by_theme["dark"] + frames_by_theme["light"],
            durations + durations,
            output / "kardboardcode-studio-walkthrough.gif",
        )
    )
    for name, checksum in preserved.items():
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != checksum:
            raise RuntimeError("Previously approved media was changed.")
    sources = (
        Path(__file__),
        ROOT / "scripts" / "capture_gui_visual_reference.py",
        ROOT / "src" / "kardboard_vtuber" / "gui" / "window.py",
        ROOT / "src" / "kardboard_vtuber" / "gui" / "worker.py",
    )
    receipt = {
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "synthetic_only": True,
        "owned_widgets_only": True,
        "camera_or_desktop_capture": False,
        "native_device_discovery": False,
        "story": ["Live anatomical eye controls", "Output controls", "Optional Logs drawer"],
        "distinct_actual_demo_frames": program_frames,
        "animations": animations,
        "screenshots": shots,
        "preserved_media": preserved,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sources
        },
    }
    (evidence / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "images")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "build" / "readme-media")
    args = parser.parse_args()
    capture(args.output_dir.resolve(), args.evidence_dir.resolve())


if __name__ == "__main__":
    main()
