"""Derive PNG/Windows icon assets from the unchanged, user-supplied logo."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import cv2
import numpy as np

ASSETS = Path("src") / "kardboard_vtuber" / "gui" / "assets"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def icon_frame(image: np.ndarray, size: int) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] != 4 or image.dtype != np.uint8:
        raise ValueError("Branding input must be an 8-bit RGBA PNG")
    ys, xs = np.nonzero(image[:, :, 3])
    if not len(xs):
        raise ValueError("The logo is fully transparent")
    cropped = image[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    padding = max(1, round(size * 0.06))
    available = size - padding * 2
    scale = available / max(cropped.shape[:2])
    width = max(1, round(cropped.shape[1] * scale))
    height = max(1, round(cropped.shape[0] * scale))
    alpha = cropped[:, :, 3:4].astype(np.float32) / 255
    premultiplied = np.concatenate((cropped[:, :, :3] * alpha, alpha), axis=2)
    resized = cv2.resize(
        premultiplied, (width, height),
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR,
    )
    restored = np.zeros((height, width, 4), dtype=np.uint8)
    restored[:, :, :3] = np.clip(np.rint(
        resized[:, :, :3] / np.maximum(resized[:, :, 3:4], 1e-8),
    ), 0, 255).astype(np.uint8)
    restored[:, :, 3] = np.clip(np.rint(resized[:, :, 3] * 255), 0, 255).astype(np.uint8)
    canvas = np.zeros((size, size, 4), dtype=np.uint8)
    left, top = (size - width) // 2, (size - height) // 2
    canvas[top:top + height, left:left + width] = restored
    return canvas


def png_bytes(image: np.ndarray) -> bytes:
    success, data = cv2.imencode(".png", image)
    if not success:
        raise RuntimeError("Could not encode the branding PNG")
    return data.tobytes()


def build(root: Path) -> None:
    folder = root / ASSETS
    source = folder / "kardboardcode-logo.png"
    original = source.read_bytes()
    image = cv2.imdecode(np.frombuffer(original, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Could not decode the supplied logo PNG")
    frames = [(size, png_bytes(icon_frame(image, size))) for size in SIZES]
    offset = 6 + 16 * len(frames)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(frames)))
    for size, data in frames:
        dimension = 0 if size == 256 else size
        directory.extend(struct.pack(
            "<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset,
        ))
        offset += len(data)
    (folder / "kardboardcode-icon.ico").write_bytes(
        bytes(directory) + b"".join(data for _, data in frames),
    )
    (folder / "kardboardcode-icon.png").write_bytes(frames[-1][1])
    if source.read_bytes() != original:
        raise RuntimeError("Canonical logo changed while deriving icons")
    print(f"Built PNG and {len(frames)}-size ICO from: {source}")


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        build(Path(__file__).resolve().parents[1])
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Branding build failed: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
