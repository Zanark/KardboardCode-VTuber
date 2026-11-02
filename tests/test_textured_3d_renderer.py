from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from kardboard_vtuber.renderer.textured_3d import (
    Textured3DCardboardRenderer,
    Textured3DRendererConfig,
    _build_character_mesh,
    _create_cardboard_texture,
    _draw_aged_sticker,
    _eye_closed,
    _FlapPhysics,
)
from tests.test_ps1_cardboard_renderer import state


def test_character_mesh_contains_box_underside_flap_and_headphone_geometry() -> None:
    vertices = _build_character_mesh()

    assert vertices.ndim == 2
    assert vertices.shape[1] == 13
    assert vertices.shape[0] > 500
    assert np.min(vertices[:, 0]) < -0.64
    assert np.max(vertices[:, 0]) > 0.64
    assert np.max(vertices[:, 1]) > 0.75
    assert np.max(vertices[:, 2]) >= 0.5
    head_volume_vertices = vertices[
        (np.isclose(vertices[:, 8], 0.16))
        & (np.isclose(vertices[:, 9], 0.12))
        & (np.isclose(vertices[:, 10], 0.09))
    ]
    assert head_volume_vertices.shape[0] > 500
    assert np.min(head_volume_vertices[:, 1]) <= -0.62
    assert np.max(head_volume_vertices[:, 1]) >= 0.46
    assert np.min(head_volume_vertices[:, 2]) <= -0.29
    assert np.max(head_volume_vertices[:, 2]) >= 0.29


def test_front_face_is_one_complete_cardboard_square() -> None:
    vertices = _build_character_mesh()
    front_vertices = vertices[
        np.isclose(vertices[:, 2], 0.5)
        & np.isclose(vertices[:, 5], 1.0)
        & np.isclose(vertices[:, 8], 0.72)
        & np.isclose(vertices[:, 9], 0.47)
        & np.isclose(vertices[:, 10], 0.23)
        & np.isclose(vertices[:, 11], 1.0)
    ]
    area = 0.0
    for start in range(0, front_vertices.shape[0], 3):
        triangle = front_vertices[start : start + 3, :2]
        if triangle.shape[0] != 3:
            continue
        edge_0 = triangle[1] - triangle[0]
        edge_1 = triangle[2] - triangle[0]
        area += abs(float(edge_0[0] * edge_1[1] - edge_0[1] * edge_1[0])) / 2.0

    assert area == pytest.approx(1.0)


def test_textured_renderer_respects_less_sensitive_eye_thresholds() -> None:
    default_config = Textured3DRendererConfig()
    strict_config = Textured3DRendererConfig(
        eye_closed_threshold=0.20,
        eye_open_threshold=0.72,
        wink_closed_threshold=0.50,
        wink_min_difference=0.25,
    )

    assert _eye_closed(0.30, 0.30, default_config)
    assert not _eye_closed(0.30, 0.30, strict_config)
    assert _eye_closed(0.55, 0.80, default_config)
    assert not _eye_closed(0.55, 0.80, strict_config)


def test_headphone_band_is_enlarged_and_has_dark_beige_cushion() -> None:
    vertices = _build_character_mesh()
    outer_band = vertices[
        np.isclose(vertices[:, 8], 0.78)
        & np.isclose(vertices[:, 9], 0.75)
        & np.isclose(vertices[:, 10], 0.66)
    ]
    cushion = vertices[
        np.isclose(vertices[:, 8], 0.62)
        & np.isclose(vertices[:, 9], 0.52)
        & np.isclose(vertices[:, 10], 0.38)
        & (vertices[:, 1] > 0.25)
    ]

    assert outer_band.shape[0] >= 396
    assert cushion.shape[0] >= 396
    assert np.max(outer_band[:, 1]) >= 0.90
    assert np.max(cushion[:, 1]) >= 0.80


def test_ear_cushions_are_larger_than_cream_earpieces() -> None:
    vertices = _build_character_mesh()
    earpieces = vertices[
        np.isclose(vertices[:, 8], 0.78)
        & np.isclose(vertices[:, 9], 0.75)
        & np.isclose(vertices[:, 10], 0.66)
        & (vertices[:, 1] < 0.25)
    ]
    cushions = vertices[
        np.isclose(vertices[:, 8], 0.62)
        & np.isclose(vertices[:, 9], 0.52)
        & np.isclose(vertices[:, 10], 0.38)
        & (vertices[:, 1] < 0.25)
    ]

    assert earpieces.shape[0] >= 120
    assert cushions.shape[0] >= 440
    assert np.ptp(cushions[:, 1]) > np.ptp(earpieces[:, 1])
    assert np.ptp(cushions[:, 2]) > np.ptp(earpieces[:, 2])


def test_cream_earpieces_protrude_beyond_cushion_rings() -> None:
    vertices = _build_character_mesh()
    earpieces = vertices[
        np.isclose(vertices[:, 8], 0.78)
        & np.isclose(vertices[:, 9], 0.75)
        & np.isclose(vertices[:, 10], 0.66)
        & (vertices[:, 1] < 0.25)
    ]
    cushions = vertices[
        np.isclose(vertices[:, 8], 0.62)
        & np.isclose(vertices[:, 9], 0.52)
        & np.isclose(vertices[:, 10], 0.38)
        & (vertices[:, 1] < 0.25)
    ]

    assert np.min(earpieces[:, 0]) <= np.min(cushions[:, 0]) - 0.05
    assert np.max(earpieces[:, 0]) >= np.max(cushions[:, 0]) + 0.05


def test_character_mesh_has_subtle_dark_box_edges() -> None:
    vertices = _build_character_mesh()
    edge_vertices = vertices[
        np.isclose(vertices[:, 8], 0.27)
        & np.isclose(vertices[:, 9], 0.16)
        & np.isclose(vertices[:, 10], 0.075)
    ]

    assert edge_vertices.shape[0] >= 500
    assert np.ptp(edge_vertices[:, 0]) >= 1.0
    assert np.ptp(edge_vertices[:, 1]) >= 1.0
    assert np.ptp(edge_vertices[:, 2]) >= 1.0


def test_character_mesh_has_folded_bottom_flaps_around_neck_opening() -> None:
    vertices = _build_character_mesh()
    bottom_vertices = vertices[
        np.isclose(vertices[:, 4], -1.0)
        & (vertices[:, 1] <= -0.5)
    ]

    assert bottom_vertices.shape[0] >= 24
    assert np.any(np.isclose(bottom_vertices[:, 0], -0.13))
    assert np.any(np.isclose(bottom_vertices[:, 0], 0.13))
    assert np.any(np.isclose(bottom_vertices[:, 2], -0.5))
    assert np.any(np.isclose(bottom_vertices[:, 2], 0.5))


def test_character_mesh_has_downward_front_underside_flap() -> None:
    vertices = _build_character_mesh()
    flap_vertices = vertices[
        (vertices[:, 0] >= -0.48)
        & (vertices[:, 0] <= 0.48)
        & (vertices[:, 1] >= -0.73)
        & (vertices[:, 1] <= -0.48)
        & (vertices[:, 2] >= 0.39)
        & (vertices[:, 2] <= 0.52)
        & np.isclose(vertices[:, 11], 1.0)
    ]

    assert flap_vertices.shape[0] >= 6
    assert np.any(np.isclose(flap_vertices[:, 1], -0.49))
    assert np.any(np.isclose(flap_vertices[:, 1], -0.72))


def test_every_underside_flap_has_a_distinct_physics_hinge() -> None:
    vertices = _build_character_mesh()

    assert set(np.unique(vertices[:, 12])) == {0.0, 1.0, 2.0, 3.0, 4.0, 5.0}
    for hinge in (1.0, 2.0, 3.0):
        assert np.count_nonzero(np.isclose(vertices[:, 12], hinge)) >= 12
    for hinge in (4.0, 5.0):
        assert np.count_nonzero(np.isclose(vertices[:, 12], hinge)) == 6


def test_flap_physics_reacts_to_motion_and_stays_bounded() -> None:
    physics = _FlapPhysics()
    initial = state(1)

    assert physics.step(initial) == (0.0, 0.0, 0.0, 0.0, 0.0)
    moved = replace(
        state(34, pitch=5.0, roll=18.0),
        center_x=0.58,
        center_y=0.52,
    )
    angles = physics.step(moved)
    for frame_index in range(2, 18):
        angles = physics.step(
            replace(
                moved,
                timestamp_ms=34 + frame_index * 33,
            )
        )

    assert all(angle != 0.0 for angle in angles)
    assert abs(angles[0]) >= np.radians(8.0)
    assert abs(angles[1]) >= np.radians(8.0)
    assert abs(angles[2]) >= np.radians(7.0)
    assert abs(angles[0]) <= np.radians(26.0)
    assert abs(angles[1]) <= np.radians(26.0)
    assert abs(angles[2]) <= np.radians(24.0)
    assert abs(angles[3]) <= np.radians(42.0)
    assert abs(angles[4]) <= np.radians(42.0)


def test_yaw_turn_moves_side_flaps_in_opposite_directions() -> None:
    physics = _FlapPhysics()
    physics.step(state(1))
    turned = state(34, yaw=25.0)

    angles = (0.0, 0.0, 0.0, 0.0, 0.0)
    for frame_index in range(1, 16):
        angles = physics.step(replace(turned, timestamp_ms=1 + frame_index * 33))

    assert angles[0] < np.radians(-5.0)
    assert angles[1] > np.radians(5.0)
    assert angles[3] < np.radians(-25.0)
    assert angles[4] > np.radians(25.0)


def test_outer_side_flaps_are_highly_sensitive_to_small_yaw_turns() -> None:
    physics = _FlapPhysics()
    physics.step(state(1))
    turned = state(34, yaw=8.0)

    angles = physics.angles
    for frame_index in range(1, 12):
        angles = physics.step(replace(turned, timestamp_ms=1 + frame_index * 33))

    assert angles[3] < np.radians(-10.0)
    assert angles[4] > np.radians(10.0)


def test_cardboard_texture_changes_letters_into_wink_arcs() -> None:
    open_texture = _create_cardboard_texture(False, False)
    left_wink_texture = _create_cardboard_texture(True, False)

    assert open_texture.shape == (512, 1024, 3)
    assert not np.array_equal(open_texture, left_wink_texture)
    assert np.array_equal(open_texture[:, 800:], left_wink_texture[:, 800:])


def test_texture_has_distinct_side_barcodes_and_top_fragile_sticker() -> None:
    texture = _create_cardboard_texture(False, False)
    left_barcode = texture[407:451, 157:222]
    right_barcode = texture[415:459, 332:465]
    top_sticker = texture[42:195, 28:227]

    dark = np.asarray((28, 32, 35))
    red = np.asarray((48, 54, 185))
    assert np.count_nonzero(np.all(left_barcode == dark, axis=2)) > 900
    assert np.count_nonzero(np.all(right_barcode == dark, axis=2)) > 1_800
    assert np.count_nonzero(np.all(top_sticker == red, axis=2)) > 3_000


def test_front_texture_has_no_red_boxed_cross_stamp() -> None:
    texture = _create_cardboard_texture(False, False)
    former_stamp = texture[421:494, 548:625]

    assert not np.any(np.all(former_stamp == (50, 62, 180), axis=2))


def test_front_texture_has_no_lower_center_tape_strip() -> None:
    texture = _create_cardboard_texture(False, False)
    former_tape = texture[395:512, 730:801]

    assert not np.any(np.all(former_tape == (105, 112, 112), axis=2))


def test_shipping_stickers_are_aged_torn_and_pixel_lettered() -> None:
    texture = _create_cardboard_texture(False, False)
    clean_white = np.all(texture == (190, 202, 205), axis=2)
    fragile_text = np.all(texture[85:125, 45:210] == (48, 54, 185), axis=2)

    assert not np.any(clean_white)
    assert not np.array_equal(texture[42, 28], (112, 142, 166))
    assert not np.array_equal(texture[194, 226], (112, 142, 166))
    for y in range(0, fragile_text.shape[0], 5):
        for x in range(0, fragile_text.shape[1], 5):
            block = fragile_text[y : y + 5, x : x + 5]
            assert np.all(block) or not np.any(block)


def test_left_side_sticker_tears_are_asymmetric_and_non_repeating() -> None:
    first = np.zeros((110, 140, 3), dtype=np.uint8)
    second = np.zeros_like(first)
    bounds = (10, 10, 126, 94)

    _draw_aged_sticker(first, bounds, (126, 154, 178), (28, 32, 35), tear_pattern=1)
    _draw_aged_sticker(second, bounds, (126, 154, 178), (28, 32, 35), tear_pattern=2)
    first_mask = np.any(first[10:95, 10:127] != 0, axis=2)
    second_mask = np.any(second[10:95, 10:127] != 0, axis=2)

    assert not np.array_equal(first_mask, np.fliplr(first_mask))
    assert not np.array_equal(second_mask, np.fliplr(second_mask))
    assert not np.array_equal(first_mask, second_mask)


def test_left_right_and_top_faces_use_distinct_atlas_regions() -> None:
    vertices = _build_character_mesh()
    left_face = vertices[
        np.isclose(vertices[:, 0], -0.5)
        & np.isclose(vertices[:, 3], -1.0)
        & np.isclose(vertices[:, 11], 1.0)
    ]
    right_face = vertices[
        np.isclose(vertices[:, 0], 0.5)
        & np.isclose(vertices[:, 3], 1.0)
        & np.isclose(vertices[:, 11], 1.0)
    ]
    top_face = vertices[
        np.isclose(vertices[:, 1], 0.5)
        & np.isclose(vertices[:, 4], 1.0)
        & np.isclose(vertices[:, 11], 1.0)
    ]

    assert left_face.shape[0] == 6
    assert right_face.shape[0] == 6
    assert top_face.shape[0] == 6
    assert np.max(left_face[:, 6]) <= 0.25
    assert np.min(right_face[:, 6]) >= 0.25
    assert np.max(right_face[:, 6]) <= 0.5
    assert np.min(top_face[:, 7]) >= 0.5


def test_painted_letters_have_irregular_brush_strokes() -> None:
    texture = _create_cardboard_texture(False, False)
    ink = np.all(texture < (55, 55, 55), axis=2)
    front_ink = ink[190:370, 620:950]

    assert np.count_nonzero(front_ink) > 5_000
    row_widths = np.count_nonzero(front_ink, axis=1)
    nonempty_widths = row_widths[row_widths > 0]
    assert np.ptp(nonempty_widths) > 40


def test_painted_letters_use_hard_ps1_pixel_colors() -> None:
    texture = _create_cardboard_texture(False, False)
    letter_crop = texture[190:380, 600:1010]
    dark_pixels = letter_crop[np.all(letter_crop < (60, 60, 60), axis=2)]
    dark_colors = np.unique(dark_pixels, axis=0)

    assert dark_colors.shape[0] == 1
    assert any(np.array_equal(color, (22, 25, 27)) for color in dark_colors)

    ink = np.all(texture == (22, 25, 27), axis=2)
    for y in range(0, ink.shape[0], 7):
        for x in range(0, ink.shape[1], 7):
            block = ink[y : y + 7, x : x + 7]
            assert np.all(block) or not np.any(block)


def test_textured_3d_config_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        Textured3DRendererConfig(box_height_multiplier=0.0)


def test_model_uses_larger_front_dimension_for_uniform_cube_scale() -> None:
    renderer = object.__new__(Textured3DCardboardRenderer)
    renderer._config = Textured3DRendererConfig(upward_bias=0.0)
    tracked = state(1)

    _, model = renderer._matrices(640, 360, tracked)

    axis_lengths = np.linalg.norm(model[:3, :3], axis=0)
    expected_side = max(
        tracked.face_width * 640 * renderer._config.box_width_multiplier,
        tracked.face_height * 360 * renderer._config.box_height_multiplier,
    )
    fov = np.radians(renderer._config.fov_degrees)
    world_per_pixel = 5.0 / (360 / (2.0 * np.tan(fov / 2.0)))
    assert axis_lengths == pytest.approx(np.full(3, expected_side * world_per_pixel))


def test_default_model_is_moved_backward_by_configured_perspective_offset() -> None:
    renderer = object.__new__(Textured3DCardboardRenderer)
    renderer._config = Textured3DRendererConfig(upward_bias=0.0)

    _, model = renderer._matrices(640, 360, state(1))

    assert model[2, 3] == pytest.approx(-5.16)


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


def test_upward_pitch_head_volume_covers_head_but_leaves_neck_visible() -> None:
    try:
        renderer = Textured3DCardboardRenderer()
    except RuntimeError as error:
        pytest.skip(str(error))
    frame = np.full((720, 405, 3), 91, dtype=np.uint8)

    renderer.render(frame, state(1, pitch=-50.0))

    assert not np.all(frame[380, 202] == 91)
    assert not np.all(frame[460, 202] == 91)
    assert np.all(frame[540, 202] == 91)
    renderer.close()
