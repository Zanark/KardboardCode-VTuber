"""Publish composed BGR frames through the installed OBS virtual-camera component."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from numpy import ndarray


@dataclass(frozen=True, slots=True)
class VirtualCameraConfig:
    width: int = 1280
    height: int = 720
    fps: float = 30.0

    def __post_init__(self) -> None:
        for name in ("width", "height"):
            value = getattr(self, name)
            if value < 2 or value % 2:
                raise ValueError(f"virtual-camera {name} must be a positive even number")
        if not math.isfinite(self.fps) or not 1.0 <= self.fps <= 60.0:
            raise ValueError("virtual-camera FPS must be between 1 and 60")


class VirtualCameraOutput:
    """Keep a fixed-size output, letterboxing without stretching or cropping."""

    def __init__(self, config: VirtualCameraConfig) -> None:
        try:
            import pyvirtualcam
        except ImportError as error:
            raise RuntimeError(
                'Virtual camera dependency missing. Run: '
                'python -m pip install -e ".[tracking,virtual-camera]"'
            ) from error

        self._config = config
        self._frame = np.zeros((config.height, config.width, 3), dtype=np.uint8)
        self._closed = False
        try:
            self._camera = pyvirtualcam.Camera(
                width=config.width,
                height=config.height,
                fps=config.fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
                backend="obs",
            )
        except (KeyError, OSError, RuntimeError, ValueError) as error:
            raise RuntimeError(
                "Could not open OBS Virtual Camera. On Windows, install OBS Studio "
                "with its virtual-camera component. Stop OBS's virtual-camera output "
                "and any other sender before running this tool; OBS itself need not run. "
                f"Backend error: {error}"
            ) from error
        try:
            self.repeat()
        except RuntimeError:
            self.close()
            raise

    @property
    def device(self) -> str:
        return self._camera.device

    def send(self, frame: ndarray) -> None:
        if (
            frame.dtype != np.uint8
            or frame.ndim != 3
            or frame.shape[2] != 3
            or min(frame.shape[:2]) == 0
        ):
            raise ValueError("virtual-camera input must be a nonempty uint8 BGR frame")
        height, width = frame.shape[:2]
        scale = min(self._config.width / width, self._config.height / height)
        size = (
            max(1, min(self._config.width, round(width * scale))),
            max(1, min(self._config.height, round(height * scale))),
        )
        resized = (
            frame
            if size == (width, height)
            else cv2.resize(
                frame,
                size,
                interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR,
            )
        )
        left = (self._config.width - size[0]) // 2
        top = (self._config.height - size[1]) // 2
        self._frame.fill(0)
        self._frame[top : top + size[1], left : left + size[0]] = resized
        self.repeat()

    def repeat(self) -> None:
        """Republish only the last composed frame, or black before acquisition."""
        if self._closed:
            raise RuntimeError("Virtual camera is closed")
        try:
            self._camera.send(self._frame)
        except (OSError, RuntimeError, ValueError) as error:
            raise RuntimeError(f"Virtual-camera frame delivery failed: {error}") from error

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._camera.close()
