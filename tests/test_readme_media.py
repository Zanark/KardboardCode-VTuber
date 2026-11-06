from __future__ import annotations

from types import SimpleNamespace

import pytest
from PIL import Image

from scripts.capture_readme_media import ensure_demo_surface, save_animation


def test_gif_preserves_changed_frames_holds_and_infinite_loop(tmp_path):
    frames = [Image.new("RGB", (32, 18), color) for color in ("red", "red", "blue", "green")]
    output = tmp_path / "example.gif"
    receipt = save_animation(frames, [200, 300, 1000, 200], output)
    assert receipt["duration_ms"] == 1700
    assert receipt["frames"] >= 3
    with Image.open(output) as gif:
        assert gif.info["loop"] == 0
        gif.seek(gif.n_frames - 1)
        assert gif.convert("RGB").getpixel((0, 0)) == (0, 128, 0)


def test_static_or_mismatched_animation_is_rejected_without_output(tmp_path):
    output = tmp_path / "invalid.gif"
    frames = [Image.new("RGB", (32, 18), "red")] * 2
    with pytest.raises(ValueError, match="changed frames"):
        save_animation(frames, [200, 200], output)
    with pytest.raises(ValueError, match="dimensions"):
        save_animation([frames[0], Image.new("RGB", (16, 9), "blue")], [200, 200], output)
    assert not output.exists()


def test_gif_timing_is_not_silently_truncated(tmp_path):
    frames = [Image.new("RGB", (32, 18), color) for color in ("red", "blue")]
    with pytest.raises(ValueError, match="multiples of ten"):
        save_animation(frames, [201, 200], tmp_path / "invalid.gif")


def test_capture_rejects_non_demo_or_unexpected_surfaces_before_grabbing_pixels():
    window = SimpleNamespace(
        worker=SimpleNamespace(demo=True),
        job=None,
        error_label=SimpleNamespace(isVisible=lambda: False),
        page_selector=SimpleNamespace(currentText=lambda: "Avatar & eyes"),
    )
    ensure_demo_surface(window, "Avatar & eyes")
    window.worker.demo = False
    with pytest.raises(RuntimeError, match="non-demo"):
        ensure_demo_surface(window, "Avatar & eyes")
    window.worker.demo = True
    with pytest.raises(RuntimeError, match="unexpected"):
        ensure_demo_surface(window, "Output & effects")
