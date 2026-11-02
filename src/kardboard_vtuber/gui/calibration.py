"""Timed, signal-only eye calibration; no face images are saved."""

from __future__ import annotations

import time

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from kardboard_vtuber.tracking.eyes import EyeSensitivity, calibrate_eyes
from kardboard_vtuber.tracking.models import FaceTrackingState


class EyeCalibrationDialog(QDialog):
    calibrated = Signal(object)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibrate both anatomical eyes")
        self.setMinimumWidth(440)
        self.open_samples: list[tuple[float, float]] = []
        self.closed_samples: list[tuple[float, float]] = []
        self.phase = "open"
        self.deadline = 0.0
        self.last_timestamp = -1
        self.sampling = False
        layout = QVBoxLayout(self)
        self.instructions = QLabel(
            "1. Face the camera with both eyes relaxed and OPEN.\n"
            "Capture open samples, then follow the closed-eye step.\n"
            "Only numeric eye scores are used; no face pictures are recorded.",
        )
        self.instructions.setWordWrap(True)
        layout.addWidget(self.instructions)
        self.result = QLabel()
        self.result.setWordWrap(True)
        layout.addWidget(self.result)
        self.capture = QPushButton("Capture OPEN eyes")
        self.capture.clicked.connect(self.begin)
        layout.addWidget(self.capture)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)
        self.timer = QTimer(self)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.tick)

    def begin(self) -> None:
        self.capture.setEnabled(False)
        self.sampling = False
        self.deadline = time.monotonic() + (3 if self.phase == "closed" else 1)
        self.timer.start()
        self.tick()

    def observe(self, state: FaceTrackingState) -> None:
        if (
            not self.timer.isActive() or not self.sampling or not state.detected
            or state.timestamp_ms == self.last_timestamp
        ):
            return
        self.last_timestamp = state.timestamp_ms
        target = self.open_samples if self.phase == "open" else self.closed_samples
        target.append((state.left_eye_open, state.right_eye_open))

    def tick(self) -> None:
        remaining = self.deadline - time.monotonic()
        if remaining > 0:
            self.result.setText(
                f"{'Hold BOTH eyes ' + self.phase.upper() if self.sampling else 'Get ready'}"
                f" / {remaining:.1f}s"
            )
            return
        if not self.sampling:
            self.sampling = True
            self.deadline = time.monotonic() + 2.0
            return
        self.timer.stop()
        if self.phase == "open":
            if len(self.open_samples) < 12:
                self.open_samples.clear()
                self.result.setText("Too few face observations. Improve framing and try again.")
                self.capture.setEnabled(True)
                return
            self.phase = "closed"
            self.instructions.setText(
                "2. Press the button, then close BOTH eyes during the three-second countdown.\n"
                "Keep them fully closed until the two-second capture is finished.",
            )
            self.result.setText(f"Captured {len(self.open_samples)} open-eye observations.")
            self.capture.setText("Capture BOTH CLOSED eyes (3-second countdown)")
            self.capture.setEnabled(True)
            return
        try:
            sensitivity = calibrate_eyes(self.open_samples, self.closed_samples)
        except ValueError as error:
            self.result.setText(str(error))
            self.closed_samples.clear()
            self.capture.setEnabled(True)
            return
        self.apply(sensitivity)

    def apply(self, sensitivity: EyeSensitivity) -> None:
        self.calibrated.emit(sensitivity)
        self.accept()

    def done(self, result: int) -> None:
        self.timer.stop()
        super().done(result)
