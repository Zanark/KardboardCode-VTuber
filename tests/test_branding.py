from __future__ import annotations

import struct
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts.build_branding import ASSETS, build, icon_frame, png_bytes


def test_icon_resampling_preserves_color_across_transparent_pixels() -> None:
    image = np.zeros((80, 120, 4), dtype=np.uint8)
    image[:, :, :3] = (0, 255, 255)
    image[10:70, 20:100:2] = (40, 90, 180, 255)
    original = image.copy()
    result = icon_frame(image, 16)
    visible = result[:, :, 3] > 0
    assert visible.any()
    assert np.all(result[:, :, :3][visible] == (40, 90, 180))
    assert not result[[0, -1], :, 3].any()
    assert result[:, [0, -1], 3].any()
    assert np.array_equal(image, original)


@pytest.mark.parametrize(
    "image",
    [np.zeros((2, 2, 4), dtype=np.uint8), np.zeros((2, 2, 3), dtype=np.uint8)],
)
def test_unusable_logo_is_rejected(image: np.ndarray) -> None:
    with pytest.raises(ValueError, match="transparent|RGBA"):
        icon_frame(image, 32)


def test_build_preserves_master_and_emits_repeatable_decodable_ico(tmp_path: Path) -> None:
    folder = tmp_path / ASSETS
    folder.mkdir(parents=True)
    image = np.zeros((24, 40, 4), dtype=np.uint8)
    image[4:20, 6:34] = (30, 80, 150, 200)
    source = folder / "kardboardcode-logo.png"
    original = png_bytes(image)
    source.write_bytes(original)
    build(tmp_path)
    ico = (folder / "kardboardcode-icon.ico").read_bytes()
    png = (folder / "kardboardcode-icon.png").read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", ico)
    assert (reserved, kind) == (0, 1)
    dimensions = []
    for index in range(count):
        width, height, _, _, planes, bits, length, offset = struct.unpack_from(
            "<BBBBHHII", ico, 6 + 16 * index,
        )
        dimension = width or 256
        decoded = cv2.imdecode(
            np.frombuffer(ico[offset:offset + length], dtype=np.uint8), cv2.IMREAD_UNCHANGED,
        )
        assert (planes, bits, height or 256) == (1, 32, dimension)
        assert decoded.shape == (dimension, dimension, 4)
        assert decoded[:, :, 3].any()
        dimensions.append(dimension)
    assert min(dimensions) <= 16 and max(dimensions) >= 256
    build(tmp_path)
    assert source.read_bytes() == original
    assert (folder / "kardboardcode-icon.ico").read_bytes() == ico
    assert (folder / "kardboardcode-icon.png").read_bytes() == png


def test_readme_art_rebuild_keeps_master_and_is_repeatable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PIL import Image

    from scripts import build_readme_art

    source = tmp_path / ASSETS / "kardboardcode-logo.png"
    source.parent.mkdir(parents=True)
    Image.new("RGBA", (40, 30), (180, 130, 70, 200)).save(source)
    original = source.read_bytes()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n')
    destination = tmp_path / "artwork"
    monkeypatch.setattr(build_readme_art, "ROOT", tmp_path)
    monkeypatch.setattr(build_readme_art, "OUTPUT", destination)
    build_readme_art.build()
    before = {path.name: path.read_bytes() for path in destination.iterdir()}
    build_readme_art.build()
    assert {path.name: path.read_bytes() for path in destination.iterdir()} == before
    assert source.read_bytes() == original
    with Image.open(destination / "hero.png") as hero:
        assert hero.size[0] > hero.size[1] > 0


def test_readme_banner_rejects_text_that_would_be_clipped() -> None:
    from PIL import Image

    from scripts.build_readme_art import text

    with pytest.raises(ValueError, match="overflow"):
        text(Image.new("RGB", (150, 100)), (50, 20), "TOO WIDE FOR THIS LABEL", 50)


def test_readme_section_art_is_real_vector_with_no_canvas_background(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import xml.etree.ElementTree as ET

    from scripts import build_readme_art

    monkeypatch.setattr(build_readme_art, "OUTPUT", tmp_path)
    build_readme_art.section("01", "CONTROL ROOM", "LIVE / VIDEO", "section.svg")
    svg = ET.fromstring((tmp_path / "section.svg").read_text(encoding="utf-8"))
    assert svg.findall(".//{http://www.w3.org/2000/svg}path")
    assert not svg.findall(".//{http://www.w3.org/2000/svg}image")
    assert not any(
        rect.get("width") == svg.get("width")
        for rect in svg.findall(".//{http://www.w3.org/2000/svg}rect")
    )
