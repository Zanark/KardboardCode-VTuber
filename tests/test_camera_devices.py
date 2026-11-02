from __future__ import annotations

import sys
from types import SimpleNamespace

import cv2
import pytest

from kardboard_vtuber.camera.devices import (
    LocalCameraDevice,
    decode_camera_inventory,
    discover_local_cameras,
)


def test_native_discovery_reads_metadata_without_opening_capture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def enumerate_devices(backend: int):
        calls.append(backend)
        return [SimpleNamespace(index=2, name="Laptop RGB Camera")]

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(
        sys.modules,
        "cv2_enumerate_cameras",
        SimpleNamespace(enumerate_cameras=enumerate_devices),
    )
    monkeypatch.setattr(
        cv2,
        "VideoCapture",
        lambda *args: pytest.fail("Discovery must not open a camera"),
    )
    devices = discover_local_cameras()
    assert calls == [cv2.CAP_MSMF, cv2.CAP_DSHOW]
    assert [(device.index, device.backend) for device in devices] == [(2, "msmf"), (2, "dshow")]
    assert devices[0].name == "Laptop RGB Camera"


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        '[{"index":true,"backend":"dshow","name":"Camera"}]',
        '[{"index":0,"backend":[],"name":"Camera"}]',
        '[{"index":0,"backend":"auto","name":"Camera"}]',
        '[{"index":0,"backend":"dshow","name":""}]',
    ],
)
def test_malformed_native_inventory_is_rejected(payload: str) -> None:
    with pytest.raises(ValueError):
        decode_camera_inventory(payload)


def test_inventory_preserves_backend_specific_indices() -> None:
    data = '[{"index":1,"backend":"msmf","name":"Laptop Camera"}]'
    assert decode_camera_inventory(data) == (LocalCameraDevice(1, "msmf", "Laptop Camera"),)
    assert "Media Foundation" in decode_camera_inventory(data)[0].label
