from __future__ import annotations

import copy

import pytest

pytest.importorskip("PySide6")

from scripts.capture_gui_visual_reference import validate_coverage


def receipt() -> dict:
    return {
        "runtimeControls": ["source", "virtual_camera_width", "virtual_camera_height"],
        "expected": {"pages": ["Camera"], "sections": ["Camera / Input source"]},
        "screenshots": [
            {
                "id": "camera-" + theme,
                "theme": theme,
                "coverage": {"pages": ["Camera"], "sections": ["Camera / Input source"]},
                "visibleControls": ["source"],
                "representedControls": ["virtual_camera_width", "virtual_camera_height"],
            }
            for theme in ("dark", "light")
        ],
    }


def test_reference_requires_every_declared_surface_in_each_theme() -> None:
    manifest = receipt()
    validate_coverage(manifest)
    incomplete = copy.deepcopy(manifest)
    incomplete["screenshots"][1]["coverage"]["sections"] = []
    with pytest.raises(ValueError, match="light: missing sections"):
        validate_coverage(incomplete)


def test_reference_rejects_controls_covered_only_in_the_other_theme() -> None:
    manifest = receipt()
    manifest["screenshots"][0]["visibleControls"] = []
    with pytest.raises(ValueError, match="dark: controls never fully shown"):
        validate_coverage(manifest)


def test_reference_rejects_duplicate_screenshot_identifiers() -> None:
    manifest = receipt()
    manifest["screenshots"][1]["id"] = manifest["screenshots"][0]["id"]
    with pytest.raises(ValueError, match="Duplicate screenshot"):
        validate_coverage(manifest)
