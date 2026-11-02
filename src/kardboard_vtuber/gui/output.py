"""A controls-free program window for OBS Window Capture."""

from __future__ import annotations

from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget

from kardboard_vtuber.gui.widgets import VideoCanvas


class CleanOutputWindow(QMainWindow):
    def __init__(self, parent: QWidget, icon: QIcon) -> None:
        super().__init__(parent)
        self.setWindowTitle("KardboardCode - Clean Output")
        self.setWindowIcon(icon)
        self.resize(960, 540)
        self.canvas = VideoCanvas("")
        self.canvas.setAccessibleName("Clean output for OBS Window Capture")
        self.setCentralWidget(self.canvas)
        self.allow_close = False

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.allow_close:
            event.accept()
        else:
            self.hide()
            event.ignore()
