"""KardboardCode VTuber application."""

from kardboard_vtuber.camera.models import (
    CameraBackend,
    CameraConfig,
    CameraSource,
    CaptureSnapshot,
    CaptureState,
    FramePacket,
)
from kardboard_vtuber.camera.stream import LatestFrameCamera

__all__ = [
    "CameraBackend",
    "CameraConfig",
    "CameraSource",
    "CaptureSnapshot",
    "CaptureState",
    "FramePacket",
    "LatestFrameCamera",
]

__version__ = "1.2.0"
