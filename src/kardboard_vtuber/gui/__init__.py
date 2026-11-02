"""Optional native desktop entry point; importing the CLI does not import Qt."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KardboardCode native desktop studio")
    parser.add_argument("--demo", action="store_true", help="Start a camera-free synthetic demo.")
    parser.add_argument("--preset", type=Path, help="Load a source-free studio preset.")
    args = parser.parse_args(argv)
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        from kardboard_vtuber.gui.window import StudioWindow
    except ImportError as error:
        print(
            f'Desktop dependency missing. Run: python -m pip install -e ".[tracking,gui]"\n{error}',
            file=sys.stderr,
        )
        return 2
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("KardboardCode Studio")
    app.setOrganizationName("KardboardCode")
    app.setStyle("Fusion")
    window = StudioWindow()
    app.setWindowIcon(window.windowIcon())
    if sys.platform == "win32":
        import ctypes

        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "KardboardCode.Studio",
        )
        if result:
            window._append_log(f"[WARNING] Windows taskbar identity returned {result}.")
    if args.preset is not None:
        window.load_preset(args.preset)
    window.show()
    previous_sigint = signal.signal(signal.SIGINT, lambda _signum, _frame: window.close())
    if args.demo:
        window.page_selector.setCurrentText("Avatar & eyes")
        QTimer.singleShot(0, window.start_demo)
    try:
        return app.exec()
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
