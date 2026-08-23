"""Download and verify the official MediaPipe Pose Landmarker Lite model."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
MODEL_SHA256 = "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a"
DEFAULT_DESTINATION = Path("models/pose_landmarker_lite.task")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    destination: Path = args.destination
    if destination.exists() and not args.force:
        _verify(destination)
        print(f"Model already present and verified: {destination}")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.download")
    try:
        urllib.request.urlretrieve(MODEL_URL, temporary)
        _verify(temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)

    print(f"Downloaded and verified: {destination}")
    return 0


def _verify(path: Path) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != MODEL_SHA256:
        raise RuntimeError(
            f"model checksum mismatch for {path}: expected {MODEL_SHA256}, got {digest}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
