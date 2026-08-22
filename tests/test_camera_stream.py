from __future__ import annotations

import threading
import time

import cv2
import numpy as np

from kardboard_vtuber.camera.models import CameraConfig, CameraRotation, CameraSource
from kardboard_vtuber.camera.stream import LatestFrameCamera


class FakeCapture:
    def __init__(self) -> None:
        self.opened = True
        self.released = False
        self.index = 0
        self.lock = threading.Lock()
        self.properties: dict[int, float] = {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 360,
            cv2.CAP_PROP_FPS: 30,
        }

    def isOpened(self) -> bool:
        return self.opened

    def read(self) -> tuple[bool, np.ndarray]:
        with self.lock:
            self.index += 1
            value = self.index % 255
        time.sleep(0.002)
        return True, np.full((4, 6, 3), value, dtype=np.uint8)

    def release(self) -> None:
        self.released = True
        self.opened = False

    def set(self, prop_id: int, value: float) -> bool:
        self.properties[prop_id] = value
        return True

    def get(self, prop_id: int) -> float:
        return self.properties.get(prop_id, 0.0)


def test_latest_frame_camera_returns_newer_sequences() -> None:
    fake = FakeCapture()
    camera = LatestFrameCamera(
        CameraConfig(CameraSource(0)),
        capture_factory=lambda _source, _backend: fake,
    )

    camera.start()
    first = camera.read(timeout=1)
    assert first is not None
    second = camera.read(after_sequence=first.sequence, timeout=1)
    camera.stop()

    assert second is not None
    assert second.sequence > first.sequence
    assert second.width == 6
    assert second.height == 4
    assert fake.released


def test_latest_frame_camera_overwrites_unread_frames() -> None:
    fake = FakeCapture()
    camera = LatestFrameCamera(
        CameraConfig(CameraSource(0)),
        capture_factory=lambda _source, _backend: fake,
    )

    camera.start()
    time.sleep(0.03)
    snapshot = camera.snapshot()
    camera.stop()

    assert snapshot.received_frames > 1
    assert snapshot.overwritten_frames > 0


def test_latest_frame_camera_rotates_left() -> None:
    fake = FakeCapture()
    camera = LatestFrameCamera(
        CameraConfig(CameraSource(0), rotation=CameraRotation.LEFT),
        capture_factory=lambda _source, _backend: fake,
    )

    camera.start()
    packet = camera.read(timeout=1)
    camera.stop()

    assert packet is not None
    assert packet.width == 4
    assert packet.height == 6
