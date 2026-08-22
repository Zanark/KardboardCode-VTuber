"""Data structures and invariants for camera capture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

import cv2
from numpy import ndarray

CameraInput: TypeAlias = int | str


class CameraBackend(StrEnum):
    """OpenCV video backend selected for a camera source."""

    AUTO = "auto"
    DSHOW = "dshow"
    MSMF = "msmf"
    FFMPEG = "ffmpeg"

    @property
    def opencv_id(self) -> int:
        return {
            CameraBackend.AUTO: cv2.CAP_ANY,
            CameraBackend.DSHOW: cv2.CAP_DSHOW,
            CameraBackend.MSMF: cv2.CAP_MSMF,
            CameraBackend.FFMPEG: cv2.CAP_FFMPEG,
        }[self]


class CameraRotation(StrEnum):
    """Clockwise rotation applied after capture."""

    NONE = "none"
    LEFT = "left"
    RIGHT = "right"
    HALF = "180"

    @property
    def opencv_code(self) -> int | None:
        return {
            CameraRotation.NONE: None,
            CameraRotation.LEFT: cv2.ROTATE_90_COUNTERCLOCKWISE,
            CameraRotation.RIGHT: cv2.ROTATE_90_CLOCKWISE,
            CameraRotation.HALF: cv2.ROTATE_180,
        }[self]


class CaptureState(StrEnum):
    """Lifecycle state of the background capture worker."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CameraSource:
    """A local device index or a network stream URL."""

    value: CameraInput

    @classmethod
    def parse(cls, raw: str) -> CameraSource:
        normalized = raw.strip()
        if not normalized:
            raise ValueError("camera source cannot be empty")
        if normalized.isdecimal():
            return cls(int(normalized))
        return cls(normalized)

    @property
    def is_network_stream(self) -> bool:
        return isinstance(self.value, str) and "://" in self.value

    def redacted(self) -> str:
        if not isinstance(self.value, str):
            return str(self.value)
        if "@" not in self.value:
            return self.value
        scheme, remainder = self.value.split("://", 1)
        return f"{scheme}://***@{remainder.rsplit('@', 1)[-1]}"


@dataclass(frozen=True, slots=True)
class CameraConfig:
    """Requested capture behavior.

    Width, height and FPS are requests. Camera drivers and network streams may
    negotiate different values; callers must inspect ``CaptureSnapshot``.
    """

    source: CameraSource
    backend: CameraBackend = CameraBackend.AUTO
    requested_width: int | None = None
    requested_height: int | None = None
    requested_fps: float | None = None
    rotation: CameraRotation = CameraRotation.NONE
    mirror: bool = False
    buffer_size: int = 1
    max_consecutive_failures: int = 30
    reconnect_delay_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.requested_width is not None and self.requested_width <= 0:
            raise ValueError("requested_width must be positive")
        if self.requested_height is not None and self.requested_height <= 0:
            raise ValueError("requested_height must be positive")
        if self.requested_fps is not None and self.requested_fps <= 0:
            raise ValueError("requested_fps must be positive")
        if self.buffer_size < 1:
            raise ValueError("buffer_size must be at least 1")
        if self.max_consecutive_failures < 1:
            raise ValueError("max_consecutive_failures must be at least 1")
        if self.reconnect_delay_seconds < 0:
            raise ValueError("reconnect_delay_seconds cannot be negative")


@dataclass(frozen=True, slots=True)
class FramePacket:
    """One captured BGR frame and its monotonic capture metadata."""

    sequence: int
    captured_at_ns: int
    frame: ndarray

    @property
    def width(self) -> int:
        return int(self.frame.shape[1])

    @property
    def height(self) -> int:
        return int(self.frame.shape[0])


@dataclass(frozen=True, slots=True)
class CaptureSnapshot:
    """Immutable diagnostic snapshot of the capture worker."""

    state: CaptureState
    source: str
    backend: CameraBackend
    negotiated_width: int
    negotiated_height: int
    negotiated_fps: float
    received_frames: int
    overwritten_frames: int
    read_failures: int
    reconnects: int
    measured_fps: float
    last_error: str | None
