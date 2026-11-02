from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QSlider,
    QSpinBox,
    QStyle,
    QStyleOptionSlider,
    QStyleOptionSpinBox,
)

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


@pytest.mark.parametrize("dark", [True, False])
@pytest.mark.parametrize("decimal", [True, False])
def test_numeric_step_buttons_render_plus_minus_and_step_values(
    dark: bool, decimal: bool,
) -> None:
    app = QApplication.instance() or QApplication([])
    spin = QDoubleSpinBox() if decimal else QSpinBox()
    spin.setRange(0, 10)
    if isinstance(spin, QDoubleSpinBox):
        spin.setDecimals(2)
        spin.setSingleStep(0.01)
    spin.setValue(5)
    spin.resize(78, 38)
    spin.setStyleSheet(stylesheet(dark))
    spin.show()
    app.processEvents()

    def button_rects() -> list[QRect]:
        option = QStyleOptionSpinBox()
        spin.initStyleOption(option)
        return [
            spin.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, option, control, spin)
            for control in (QStyle.SubControl.SC_SpinBoxUp, QStyle.SubControl.SC_SpinBoxDown)
        ]

    def glyph_bounds(rect: QRect, color: str) -> tuple[float, float]:
        image = spin.grab().toImage()
        ratio = image.devicePixelRatio()
        expected = QColor(color)
        points = []
        for x in range(round((rect.x() + 3) * ratio), round((rect.right() - 2) * ratio)):
            for y in range(round((rect.y() + 2) * ratio), round((rect.bottom() - 1) * ratio)):
                actual = image.pixelColor(x, y)
                if max(
                    abs(actual.red() - expected.red()),
                    abs(actual.green() - expected.green()),
                    abs(actual.blue() - expected.blue()),
                ) <= 24:
                    points.append((x, y))
        assert points, "An empty step button is not a usable numeric affordance."
        return (
            (max(x for x, _ in points) - min(x for x, _ in points) + 1) / ratio,
            (max(y for _, y in points) - min(y for _, y in points) + 1) / ratio,
        )

    try:
        up, down = button_rects()
        plus_width, plus_height = glyph_bounds(up, "#19332b")
        minus_width, minus_height = glyph_bounds(down, "#19332b")
        assert plus_width >= 4 and plus_height >= 4
        assert minus_width >= 4 and minus_height <= 3
        before = spin.value()
        QTest.mouseClick(spin, Qt.MouseButton.LeftButton, pos=up.center())
        assert spin.value() > before
        QTest.mouseClick(spin, Qt.MouseButton.LeftButton, pos=down.center())
        assert spin.value() == before
        muted = "#819385" if dark else "#786e5c"
        spin.setValue(0)
        app.processEvents()
        glyph_bounds(down, muted)
        QTest.mouseClick(spin, Qt.MouseButton.LeftButton, pos=down.center())
        assert spin.value() == 0
        spin.setValue(10)
        app.processEvents()
        glyph_bounds(up, muted)
        QTest.mouseClick(spin, Qt.MouseButton.LeftButton, pos=up.center())
        assert spin.value() == 10
        spin.setEnabled(False)
        app.processEvents()
        glyph_bounds(up, muted)
        glyph_bounds(down, muted)
    finally:
        spin.close()
