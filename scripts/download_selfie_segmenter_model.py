"""Download and verify the official MediaPipe Selfie Segmenter model."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
    "selfie_segmenter/float16/latest/selfie_segmenter.tflite"
)
MODEL_SHA256 = "191ac9529ae506ee0beefa6b2c945a172dab9d07d1e802a290a4e4038226658b"
DEFAULT_DESTINATION = Path("models/selfie_segmenter.tflite")


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
