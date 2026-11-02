"""Capture real studio widgets using only the explicitly synthetic demo."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from kardboard_vtuber.gui.window import StudioWindow


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
    timer = QTimer()
    timer.setInterval(400)

    def capture() -> None:
        if window.worker is None or time.monotonic() - started > 20:
            print("Synthetic preview did not become ready.", flush=True)
            state["error"] = True
            timer.stop()
            window.close()
            return
        if window.preview.image.isNull():
            return
        number = state["shot"]
        if number == 0:
            path = args.output_dir / "kardboardcode-studio-dark.png"
            if not window.grab().save(str(path)):
                raise RuntimeError(f"Could not save screenshot: {path}")
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
            timer.stop()
            heartbeat.stop()
            gaps = [(right - left) * 1000 for left, right in zip(beats, beats[1:], strict=False)]
            print(
                json.dumps(
                    {
                        "synthetic_only": True,
                        "screenshots": 4,
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
