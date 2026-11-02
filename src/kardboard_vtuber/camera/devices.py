"""Windows camera metadata discovery without opening capture streams."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass

from kardboard_vtuber.camera.models import CameraBackend


@dataclass(frozen=True, slots=True)
class LocalCameraDevice:
    index: int
    backend: str
    name: str

    def __post_init__(self) -> None:
        if type(self.index) is not int or self.index < 0:
            raise ValueError("Camera index must be a nonnegative integer")
        if not isinstance(self.backend, str) or self.backend not in {
            CameraBackend.DSHOW.value,
            CameraBackend.MSMF.value,
        }:
            raise ValueError("Camera discovery returned an unsupported backend")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Camera discovery returned an empty device name")

    @property
    def label(self) -> str:
        api = "DirectShow" if self.backend == "dshow" else "Media Foundation"
        return f"{self.name} / {api} / index {self.index}"


def discover_local_cameras() -> tuple[LocalCameraDevice, ...]:
    if sys.platform != "win32":
        raise RuntimeError(
            "Named camera discovery currently supports Windows. "
            "Use a manual device index in the custom-source field on other platforms.",
        )
    try:
        from cv2_enumerate_cameras import enumerate_cameras
    except ImportError as error:
        raise RuntimeError(
            'Camera discovery dependency missing. Run: python -m pip install -e ".[gui]"',
        ) from error
    devices = []
    for backend in (CameraBackend.MSMF, CameraBackend.DSHOW):
        for camera in enumerate_cameras(backend.opencv_id):
            devices.append(
                LocalCameraDevice(
                    camera.index,
                    backend.value,
                    camera.name.strip() or "Name unavailable",
                )
            )
    return tuple(devices)


def decode_camera_inventory(payload: str) -> tuple[LocalCameraDevice, ...]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("Camera discovery did not return a device list")
    devices = []
    for row in data:
        if not isinstance(row, dict) or set(row) != {"index", "backend", "name"}:
            raise ValueError("Camera discovery returned an invalid device entry")
        devices.append(LocalCameraDevice(**row))
    return tuple(devices)


def main() -> int:
    try:
        devices = discover_local_cameras()
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps([asdict(device) for device in devices], ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
