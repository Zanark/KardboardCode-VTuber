from __future__ import annotations

import numpy as np
import pytest

from kardboard_vtuber.renderer.textured_3d import (
    Textured3DCardboardRenderer,
    Textured3DRendererConfig,
    _build_character_mesh,
    _create_cardboard_texture,
)
from tests.test_ps1_cardboard_renderer import state


def test_character_mesh_contains_box_flaps_and_headphone_geometry() -> None:
    vertices = _build_character_mesh()

    assert vertices.ndim == 2
    assert vertices.shape[1] == 12
    assert vertices.shape[0] > 500
    assert np.min(vertices[:, 0]) < -0.64
    assert np.max(vertices[:, 0]) > 0.64
    assert np.max(vertices[:, 1]) > 0.75
    assert np.max(vertices[:, 2]) > 0.65


def test_cardboard_texture_changes_letters_into_wink_arcs() -> None:
    open_texture = _create_cardboard_texture(False, False)
    left_wink_texture = _create_cardboard_texture(True, False)

    assert open_texture.shape == (512, 1024, 3)
    assert not np.array_equal(open_texture, left_wink_texture)
    assert np.array_equal(open_texture[:, 800:], left_wink_texture[:, 800:])


def test_textured_3d_config_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        Textured3DRendererConfig(box_depth_multiplier=0.0)


def test_gpu_renderer_is_fail_closed_and_composites_model() -> None:
    try:
        renderer = Textured3DCardboardRenderer()
    except RuntimeError as error:
        pytest.skip(str(error))
    frame = np.full((360, 640, 3), 91, dtype=np.uint8)

    renderer.render(frame, state(1, detected=False))
    assert np.count_nonzero(frame) == 0

    frame.fill(91)
    renderer.render(frame, state(34, yaw=20.0, pitch=10.0))
    safe_frame = frame.copy()
    assert np.count_nonzero(frame != 91) > 20_000

    frame.fill(220)
    renderer.render(frame, state(67, detected=False))
    assert np.array_equal(frame, safe_frame)
    renderer.close()
