"""Capture real studio widgets using only the explicitly synthetic demo."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from kardboard_vtuber.camera.devices import LocalCameraDevice
from kardboard_vtuber.gui.window import StudioWindow
from kardboard_vtuber.tracking.mediapipe_tracker import render_face_mesh_panel
from kardboard_vtuber.tracking.models import FaceTrackingState


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/images"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setStyle("Fusion")
    window = StudioWindow()
    window.page_selector.setCurrentText("Avatar & eyes")
    window.controls["left_blink_threshold"].set_value(0.30)
    window.controls["right_blink_threshold"].set_value(0.38)
    window._refresh_settings()
    window.show()
    window.start_demo()
    started = time.monotonic()
    beats: list[float] = []
    heartbeat = QTimer()
    heartbeat.setInterval(10)
    heartbeat.timeout.connect(lambda: beats.append(time.monotonic()))
    heartbeat.start()
    state = {"shot": 0, "error": False}
    demo_image = QImage()
    timer = QTimer()
    timer.setInterval(400)

    def capture() -> None:
        nonlocal demo_image
        if (state["shot"] < 4 and window.worker is None) or time.monotonic() - started > 30:
            print("Synthetic preview did not become ready.", flush=True)
            state["error"] = True
            timer.stop()
            window.close()
            return
        if state["shot"] < 4 and window.preview.image.isNull():
            return
        number = state["shot"]
        if number == 0:
            demo_image = window.preview.image.copy()
            path = args.output_dir / "kardboardcode-studio-dark.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            clean_path = args.output_dir / "kardboardcode-studio-clean-output.png"
            if not window.output_window.grab().save(str(clean_path)):
                raise RuntimeError(f"Could not save screenshot: {clean_path}")
            window.toggle_theme()
        elif number == 1:
            path = args.output_dir / "kardboardcode-studio-light.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            window.toggle_theme()
            window.resize(1120, 780)
        elif number == 2:
            path = args.output_dir / "kardboardcode-studio-compact.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            window.show_tutorial(3)
        elif number == 3:
            path = args.output_dir / "kardboardcode-studio-tutorial.png"
            assert window._tutorial is not None
            if not window._tutorial.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            window._tutorial.close()
            window.stop_button.click()
            window.resize(1500, 980)
            window.page_selector.setCurrentText("Camera")
        elif number == 4:
            if window.worker is not None:
                return
            window._native_devices = (
                LocalCameraDevice(index=0, backend="msmf", name="Illustrative laptop camera"),
                LocalCameraDevice(index=0, backend="dshow", name="Illustrative USB camera"),
            )
            window._populate_native_cameras()
            window.native_camera.setCurrentIndex(1)
            window.native_hint.setText(
                "Illustrative device names for documentation. No physical camera was opened.",
            )
        elif number == 5:
            path = args.output_dir / "kardboardcode-studio-native-camera.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            window.work_mode.setCurrentIndex(1)
            window.video_input.setText(r"C:\example\original-video.mp4")
            window.video_output.setText(r"C:\example\original-video-kardboard.mkv")
        elif number == 6:
            path = args.output_dir / "kardboardcode-studio-video.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            window.work_mode.setCurrentIndex(0)
            window.resize(1800, 1000)
            window.page_selector.setCurrentText("Tracking labs")
            window.controls["full_body"].set_value(True)
            window.controls["tracking_debug"].set_value(True)
            window.controls["debug_face_preview"].set_value(True)
            window._refresh_settings()
            window.preview.image = demo_image.copy()
            window.preview.update()
            raw = np.full((260, 230, 3), (55, 85, 65), np.uint8)
            for x in range(0, 230, 30):
                for y in range(0, 260, 30):
                    if (x + y) // 30 % 2:
                        raw[y:y + 30, x:x + 30] = (85, 115, 95)
            cv2.putText(raw, "SYNTHETIC", (30, 120), cv2.FONT_HERSHEY_SIMPLEX,
                        .65, (210, 235, 220), 2)
            cv2.putText(raw, "NOT A FACE", (28, 155), cv2.FONT_HERSHEY_SIMPLEX,
                        .60, (210, 235, 220), 1)
            window.raw_face.set_frame(raw)
            window.face_mesh.set_frame(
                render_face_mesh_panel(FaceTrackingState.no_face(), (1280, 720)),
            )
            window.raw_panel.show()
            window.diagnostic_panel.show()
            window.status.setText("SYNTHETIC DIAGNOSTIC LAYOUT / NO CAMERA INPUT")
        elif number == 7:
            path = args.output_dir / "kardboardcode-studio-diagnostics.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
            timer.stop()
            heartbeat.stop()
            gaps = [(right - left) * 1000 for left, right in zip(beats, beats[1:], strict=False)]
            print(
                json.dumps(
                    {
                        "synthetic_only": True,
                        "screenshots": 8,
                        "heartbeat_samples": len(beats),
                        "maximum_heartbeat_gap_ms": round(max(gaps), 2) if gaps else None,
                    }
                ),
                flush=True,
            )
            window.close()
        state["shot"] += 1

    timer.timeout.connect(capture)
    timer.start()
    code = app.exec()
    return 1 if state["error"] else code


if __name__ == "__main__":
    raise SystemExit(main())
