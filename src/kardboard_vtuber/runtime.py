"""Optional, toolkit-neutral hooks for a cooperative desktop session."""

from __future__ import annotations

import math
import re
import threading
from collections import deque
from dataclasses import dataclass, field

import cv2
from numpy import ndarray

from kardboard_vtuber.camera.models import CameraSource
from kardboard_vtuber.tracking.events import ActionThresholds
from kardboard_vtuber.tracking.eyes import EyeSensitivity
from kardboard_vtuber.tracking.models import FaceTrackingState


def redact(message: str, *, source: str | None = None) -> str:
    """Keep camera endpoints and URL secrets out of GUI logs and command copies."""
    if source and source.strip() and not source.strip().isdecimal():
        message = message.replace(source, "[camera source hidden]")
        message = message.replace(
            CameraSource.parse(source).redacted(),
            "[camera source hidden]",
        )
    return re.sub(
        r"\b[a-z][a-z0-9+.-]*://\S+",
        "[camera URL hidden]",
        message,
        flags=re.IGNORECASE,
    )


@dataclass(frozen=True, slots=True)
class LiveTuning:
    eyes: EyeSensitivity = field(default_factory=EyeSensitivity)
    brightness: int = 12
    action_hold_ms: int = 100
    eye_hold_ms: int = 40

    def __post_init__(self) -> None:
        if not isinstance(self.brightness, int) or not 0 <= self.brightness <= 100:
            raise ValueError("brightness must be an integer between 0 and 100")
        if self.action_hold_ms < 0 or self.eye_hold_ms < 0:
            raise ValueError("action hold times cannot be negative")

    def action_thresholds(self) -> ActionThresholds:
        return ActionThresholds(
            eye_closed=min(self.eyes.left_closed, self.eyes.right_closed),
            left_eye_closed=self.eyes.left_closed,
            right_eye_closed=self.eyes.right_closed,
            eye_open=self.eyes.opened,
            wink_closed=self.eyes.wink,
            wink_min_difference=self.eyes.difference,
            hold_ms=self.action_hold_ms,
            eye_hold_ms=self.eye_hold_ms,
        )


@dataclass(frozen=True, slots=True)
class RuntimeTelemetry:
    face: FaceTrackingState = field(default_factory=FaceTrackingState.no_face)
    raw_face: FaceTrackingState = field(default_factory=FaceTrackingState.no_face)
    effective_detected: bool = False
    camera_fps: float = 0.0
    tracking_fps: float = 0.0
    frame_age_ms: float = 0.0
    frame_size: tuple[int, int] = (0, 0)
    capture_state: str = "stopped"
    action: str = ""
    output_device: str = ""
    demo: bool = False
    masking_enabled: bool = True
    raw_preview: bool = False
    render_face: FaceTrackingState | None = None
    calibration_status: str = ""


@dataclass(frozen=True, slots=True)
class PreviewPacket:
    frame: ndarray | None
    skeleton: ndarray | None
    telemetry: RuntimeTelemetry
    clean_frame: ndarray | None = None
    face_mesh: ndarray | None = None
    raw_face: ndarray | None = None


class RuntimeBridge:
    """One latest display packet; bounded logs; no dependency on the widget toolkit."""

    def __init__(
        self,
        tuning: LiveTuning | None = None,
        *,
        source: str | None = None,
    ) -> None:
        self.stop_event = threading.Event()
        self._lock = threading.Lock()
        self._tuning = tuning or LiveTuning()
        self._source = source
        self._preview: PreviewPacket | None = None
        self._logs: deque[str] = deque(maxlen=500)
        self._lost_logs = 0

    def set_tuning(self, tuning: LiveTuning) -> None:
        with self._lock:
            self._tuning = tuning

    def tuning(self) -> LiveTuning:
        with self._lock:
            return self._tuning

    def log(self, message: str) -> None:
        safe = redact(message, source=self._source)
        with self._lock:
            if len(self._logs) == self._logs.maxlen:
                self._lost_logs += 1
            self._logs.append(safe)

    def publish(
        self,
        frame: ndarray | None,
        telemetry: RuntimeTelemetry,
        skeleton: ndarray | None = None,
        *,
        clean_frame: ndarray | None = None,
        face_mesh: ndarray | None = None,
        raw_face: ndarray | None = None,
    ) -> None:
        packet = PreviewPacket(
            _display_copy(frame), _display_copy(skeleton), telemetry,
            clean_frame.copy() if clean_frame is not None else None,
            _display_copy(face_mesh), _display_copy(raw_face),
        )
        with self._lock:
            self._preview = packet

    def take(self) -> tuple[PreviewPacket | None, tuple[str, ...]]:
        with self._lock:
            packet, self._preview = self._preview, None
            logs = tuple(self._logs)
            self._logs.clear()
            lost, self._lost_logs = self._lost_logs, 0
        if lost:
            logs = (
                f"[GUI] {lost} older log lines dropped to keep the interface responsive.",
                *logs,
            )
        return packet, logs


def _display_copy(frame: ndarray | None) -> ndarray | None:
    if frame is None:
        return None
    height, width = frame.shape[:2]
    scale = min(1.0, 1280 / width, 800 / height)
    if not math.isclose(scale, 1.0):
        return cv2.resize(
            frame,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return frame.copy()
