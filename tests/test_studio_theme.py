from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QSlider, QStyle, QStyleOptionSlider

from kardboard_vtuber.gui.theme import stylesheet


@pytest.mark.parametrize("dark,expected", [(True, "#d5a568"), (False, "#276447")])
def test_slider_track_and_handle_have_visible_palette_and_disabled_states(
    dark: bool, expected: str,
) -> None:
    app = QApplication.instance() or QApplication([])
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(60)
    slider.resize(320, 40)
    slider.setStyleSheet(stylesheet(dark))
    slider.show()
    app.processEvents()
    try:
        option = QStyleOptionSlider()
        slider.initStyleOption(option)
        groove = slider.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderGroove, slider,
        )
        handle = slider.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderHandle, slider,
        )
        track_point = QPoint(groove.x() + groove.width() // 4, groove.center().y())
        image = slider.grab().toImage()
        assert image.pixelColor(track_point).name() == expected
        assert image.pixelColor(handle.center()).name() == expected
        slider.setEnabled(False)
        app.processEvents()
        disabled = slider.grab().toImage()
        assert disabled.pixelColor(track_point).name() != expected
        assert disabled.pixelColor(handle.center()).name() != expected
    finally:
        slider.close()
