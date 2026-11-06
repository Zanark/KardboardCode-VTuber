"""Native controls and ownership-safe BGR display widgets."""

from __future__ import annotations

import argparse
import textwrap

from numpy import ndarray
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from kardboard_vtuber.gui.settings import LIVE_FIELDS, PATH_FIELDS, Field, SettingValue


class DisclosureSection(QWidget):
    def __init__(self, title: str, *, expanded: bool = False) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.toggle = QToolButton()
        self.toggle.setObjectName("sectionToggle")
        self.toggle.setText(title)
        self.toggle.setAccessibleName(title)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setCheckable(True)
        self.toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.toggle)
        self.body = QWidget()
        self.content = QVBoxLayout(self.body)
        self.content.setContentsMargins(2, 4, 2, 8)
        self.content.setSpacing(8)
        layout.addWidget(self.body)
        self.toggle.toggled.connect(self._show_content)
        self.set_expanded(expanded)

    def set_expanded(self, expanded: bool) -> None:
        self.toggle.setChecked(expanded)
        self._show_content(expanded)

    def _show_content(self, expanded: bool) -> None:
        self.body.setVisible(expanded)
        self.toggle.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow,
        )


class ErrorBanner(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("error")
        self.setAccessibleName("Session error details")
        self.setReadOnly(True)
        self.setMinimumHeight(48)
        self.setMaximumHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

    def setText(self, message: str) -> None:
        self.setPlainText(message)

    def text(self) -> str:
        return self.toPlainText()


class ValueSlider(QWidget):
    changed = Signal()

    def __init__(self, maximum: int = 1) -> None:
        super().__init__()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, maximum * 100)
        self.number = QDoubleSpinBox()
        self.number.setRange(0, maximum)
        self.number.setDecimals(2 if maximum == 1 else 0)
        self.number.setSingleStep(0.01 if maximum == 1 else 1)
        self.number.setFixedWidth(78)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.slider, 1)
        row.addWidget(self.number)
        self.slider.valueChanged.connect(lambda value: self.number.setValue(value / 100))
        self.number.valueChanged.connect(self._number_changed)

    def _number_changed(self, value: float) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(round(value * 100))
        self.slider.blockSignals(False)
        self.changed.emit()

    def value(self) -> float:
        return self.number.value()

    def setValue(self, value: float) -> None:
        self.number.setValue(value)
        self.slider.setValue(round(value * 100))


class OptionControl(QWidget):
    changed = Signal()

    def __init__(self, field: Field, action: argparse.Action, value: SettingValue) -> None:
        super().__init__()
        self.field = field
        self.action = action
        self.optional: QCheckBox | None = None
        self.setObjectName("field_" + field.name)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 5)
        layout.setSpacing(5)
        label = field.label
        self.state_badge = QLabel("LIVE" if field.name in LIVE_FIELDS else "")
        self.state_badge.setObjectName("lockBadge")
        self.editor: QCheckBox | QLineEdit | QComboBox | QSpinBox | QDoubleSpinBox | ValueSlider
        if isinstance(action, argparse._StoreTrueAction):
            self.editor = QCheckBox(textwrap.fill(label, width=32))
            title = QHBoxLayout()
            title.addWidget(self.editor, 1)
            title.addWidget(self.state_badge)
            layout.addLayout(title)
            self.editor.toggled.connect(lambda _: self.changed.emit())
        else:
            title = QHBoxLayout()
            name = QLabel(label)
            name.setWordWrap(True)
            title.addWidget(name, 1)
            if action.default is None:
                self.optional = QCheckBox("Override" if field.kind == "slider" else "Set")
                title.addWidget(self.optional)
                self.optional.toggled.connect(self._optional_changed)
            title.addWidget(self.state_badge)
            layout.addLayout(title)
            if field.kind in {"slider", "slider100"}:
                self.editor = ValueSlider(100 if field.kind == "slider100" else 1)
                self.editor.changed.connect(self.changed.emit)
            elif action.choices:
                self.editor = QComboBox()
                self.editor.addItems([str(item) for item in action.choices])
                self.editor.currentTextChanged.connect(lambda _: self.changed.emit())
            elif action.type is int or field.kind == "integer":
                self.editor = QSpinBox()
                self.editor.setRange(0, 1_000_000)
                self.editor.valueChanged.connect(lambda _: self.changed.emit())
            elif action.type is float:
                self.editor = QDoubleSpinBox()
                self.editor.setRange(0, 1_000_000)
                self.editor.setDecimals(2)
                self.editor.valueChanged.connect(lambda _: self.changed.emit())
            else:
                self.editor = QLineEdit()
                self.editor.textChanged.connect(lambda _: self.changed.emit())
            row = QHBoxLayout()
            row.addWidget(self.editor, 1)
            if field.kind == "source":
                assert isinstance(self.editor, QLineEdit)
                self.editor.setEchoMode(QLineEdit.EchoMode.Password)
                reveal = QPushButton("Show")
                reveal.setCheckable(True)
                reveal.toggled.connect(self._reveal_source)
                row.addWidget(reveal)
            if field.kind == "source" or field.name in PATH_FIELDS:
                browse = QPushButton("Browse")
                browse.clicked.connect(self._browse)
                row.addWidget(browse)
            layout.addLayout(row)
        self.editor.setObjectName(field.name)
        self.editor.setAccessibleName(field.label)
        help_text = field.hint or action.help or ""
        self.setToolTip(help_text)
        self.editor.setToolTip(help_text)
        self.editor.setAccessibleDescription(help_text)
        if field.name == "debug_face_preview" and field.hint:
            hint = QLabel(field.hint)
            hint.setObjectName("hint")
            hint.setWordWrap(True)
            layout.addWidget(hint)
        self.set_value(value)

    def set_locked(self, locked: bool) -> None:
        self.state_badge.setText("LOCKED" if locked else (
            "LIVE" if self.field.name in LIVE_FIELDS else ""
        ))
        self.state_badge.setToolTip("Stop the session to edit this setting." if locked else "")
        self.setProperty("locked", locked)
        self.setEnabled(not locked)

    def _optional_changed(self, enabled: bool) -> None:
        self.editor.setEnabled(enabled)
        self.changed.emit()

    def _reveal_source(self, enabled: bool) -> None:
        assert isinstance(self.editor, QLineEdit)
        self.editor.setEchoMode(
            QLineEdit.EchoMode.Normal if enabled else QLineEdit.EchoMode.Password,
        )

    def _browse(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Select recording or model file")
        if filename:
            assert isinstance(self.editor, QLineEdit)
            self.editor.setText(filename)

    def value(self) -> SettingValue:
        if self.optional is not None and not self.optional.isChecked():
            return None
        if isinstance(self.editor, QCheckBox):
            return self.editor.isChecked()
        if isinstance(self.editor, QComboBox):
            return self.editor.currentText()
        if isinstance(self.editor, QLineEdit):
            text = self.editor.text().strip()
            if self.field.kind == "depth":
                try:
                    return float(text)
                except ValueError as error:
                    raise ValueError("Perspective depth offset must be a number") from error
            return text
        value = self.editor.value()
        return int(value) if self.field.name == "brightness" else value

    def set_value(self, value: SettingValue) -> None:
        self.blockSignals(True)
        try:
            if self.optional is not None:
                self.optional.setChecked(value is not None)
            optional_defaults = {
                "width": 1280,
                "height": 720,
                "fps": 30.0,
                "duration": 60.0,
                "preview_height": 720,
            }
            shown = value
            if shown is None:
                shown = (
                    0.35
                    if self.field.kind == "slider"
                    else optional_defaults.get(
                        self.field.name,
                    )
                )
            if isinstance(self.editor, QCheckBox):
                self.editor.setChecked(bool(shown))
            elif isinstance(self.editor, QComboBox):
                self.editor.setCurrentText(str(shown))
            elif isinstance(self.editor, QLineEdit):
                self.editor.setText("" if shown is None else str(shown))
            elif isinstance(shown, (int, float)):
                if isinstance(self.editor, QSpinBox):
                    self.editor.setValue(int(shown))
                else:
                    self.editor.setValue(float(shown))
            if self.optional is not None:
                self.editor.setEnabled(value is not None)
        finally:
            self.blockSignals(False)


class VideoCanvas(QWidget):
    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self.image = QImage()
        self.placeholder = placeholder
        self.setMinimumSize(320, 220)
        self.setAccessibleName("Camera preview")

    def set_frame(self, frame: ndarray | None) -> None:
        if frame is None:
            self.image = QImage()
        else:
            height, width = frame.shape[:2]
            self.image = QImage(
                frame.data,
                width,
                height,
                frame.strides[0],
                QImage.Format.Format_BGR888,
            ).copy()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), "#101917")
        if self.image.isNull():
            painter.setPen("#9bb7ad")
            painter.drawText(
                self.rect().adjusted(30, 20, -30, -20),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self.placeholder,
            )
            return
        size = self.image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(
            (self.width() - size.width()) / 2,
            (self.height() - size.height()) / 2,
            size.width(),
            size.height(),
        )
        painter.drawImage(target, self.image)
