"""Download and verify the Depth Anything V2 Small FP16 ONNX model."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

MODEL_URL = (
    "https://huggingface.co/onnx-community/depth-anything-v2-small/"
    "resolve/main/onnx/model_fp16.onnx"
)
MODEL_SHA256 = "2df6223f206b5164e21f664ace61dabeb9bb6a49b8b5a3e00510b4807d0f5b04"
DEFAULT_DESTINATION = Path("models/depth_anything_v2_small_fp16.onnx")


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
