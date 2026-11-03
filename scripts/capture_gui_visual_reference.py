"""Capture every named Studio surface with privacy-safe native example data."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from PySide6.QtCore import QPoint, QUrl
from PySide6.QtGui import QImage, QRegion
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QMenu,
    QMessageBox,
    QScrollArea,
    QWidget,
)

from kardboard_vtuber import __version__
from kardboard_vtuber.camera.devices import LocalCameraDevice
from kardboard_vtuber.gui import settings
from kardboard_vtuber.gui.calibration import EyeCalibrationDialog
from kardboard_vtuber.gui.tutorial import LESSONS
from kardboard_vtuber.gui.widgets import DisclosureSection, VideoCanvas
from kardboard_vtuber.gui.window import StudioWindow
from kardboard_vtuber.runtime import RuntimeTelemetry
from kardboard_vtuber.tracking.eyes import calibrate_eyes
from kardboard_vtuber.tracking.full_body import render_pose_skeleton_debug
from kardboard_vtuber.tracking.mediapipe_tracker import render_face_mesh_panel

if __package__:
    from .generate_documentation_gallery import _synthetic_body_state, _synthetic_debug_state
else:
    from generate_documentation_gallery import _synthetic_body_state, _synthetic_debug_state

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = r"C:\KardboardCode-example"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def source_reference(symbol: object) -> dict[str, str | int]:
    filename = inspect.getsourcefile(symbol)
    if filename is None:
        raise ValueError(f"No source file for {symbol}")
    _, line = inspect.getsourcelines(symbol)
    return {
        "file": str(Path(filename).resolve().relative_to(ROOT)),
        "line": line,
        "symbol": getattr(symbol, "__qualname__", str(symbol)),
    }


def validate_coverage(manifest: dict) -> None:
    images = manifest["screenshots"]
    identifiers = [image["id"] for image in images]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate screenshot identifiers")
    for theme in ("dark", "light"):
        themed = [image for image in images if image["theme"] == theme]
        for category, expected in manifest["expected"].items():
            found = {value for image in themed for value in image["coverage"].get(category, [])}
            missing = set(expected) - found
            if missing:
                raise ValueError(f"{theme}: missing {category}: {sorted(missing)}")
        visible = {name for image in themed for name in image["visibleControls"]}
        represented = {name for image in themed for name in image["representedControls"]}
        missing = set(manifest["runtimeControls"]) - visible - represented
        if missing:
            raise ValueError(f"{theme}: controls never fully shown: {sorted(missing)}")


class ReferenceCapture:
    def __init__(self, output: Path) -> None:
        self.output = output.resolve()
        self.captures = self.output / "captures"
        self.fixtures = self.output / "fixtures"
        self.captures.mkdir(parents=True, exist_ok=True)
        self.fixtures.mkdir(parents=True, exist_ok=True)
        for filename in ("example-input.mp4", "example-preset.json", "example-model.task"):
            (self.fixtures / filename).write_text("Synthetic file-picker specimen.\n")
        self.app = QApplication.instance() or QApplication([])
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setStyle("Fusion")
        # Never inherit a real endpoint into the custom-source memory or screenshots.
        with patch.dict(os.environ, {"KARDBOARD_CAMERA_URL": ""}):
            self.window = StudioWindow()
            self.defaults = settings.defaults()
        self.defaults["source"] = "0"
        for field, filename in (
            ("face_model", "face_landmarker.task"),
            ("hand_model", "hand_landmarker.task"),
            ("pose_model", "pose_landmarker_lite.task"),
            ("segmentation_model", "selfie_segmenter.tflite"),
        ):
            self.defaults[field] = EXAMPLE + "\\models\\" + filename
        self.window._apply_values(self.defaults)
        self.window._custom_source = "https://example.invalid/video"
        self.window._custom_backend = "ffmpeg"
        self.window.record_folder.setText(EXAMPLE + "\\recordings")
        self.window.record_name.setText("KardboardCode-example")
        self.window.video_input.setText(EXAMPLE + "\\example-input.mp4")
        self.window.video_output.setText(EXAMPLE + "\\example-output.mkv")
        self.window._native_devices = (
            LocalCameraDevice(0, "msmf", "Illustrative laptop camera"),
            LocalCameraDevice(1, "dshow", "Illustrative USB camera"),
        )
        self.window._populate_native_cameras()
        self.window.resize(1440, 810)
        self.window.show()
        self.settle()
        self.program = QImage()
        self.raw = np.full((260, 230, 3), (55, 85, 65), np.uint8)
        for x in range(0, 230, 30):
            for y in range(0, 260, 30):
                if (x + y) // 30 % 2:
                    self.raw[y : y + 30, x : x + 30] = (85, 115, 95)
        cv2.putText(
            self.raw, "SYNTHETIC", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (210, 235, 220), 2
        )
        cv2.putText(
            self.raw, "NOT A FACE", (28, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (210, 235, 220), 1
        )
        self.face = render_face_mesh_panel(_synthetic_debug_state(), (1280, 720))
        self.body = render_pose_skeleton_debug(_synthetic_body_state())
        self.images: list[dict] = []
        self.theme = "dark"
        self.expected = {
            "pages": list(self.window.page_names),
            "sections": [f"{page} / {name}" for page, name in self.window.sections],
            "tools": [
                self.window.console_tabs.tabText(i) for i in range(self.window.console_tabs.count())
            ],
            "diagnostics": [
                "Raw face",
                *[
                    self.window.diagnostic_tabs.tabText(i)
                    for i in range(self.window.diagnostic_tabs.count())
                ],
            ],
            "menus": ["File", "View", "Help", "Presets"],
            "tutorials": [lesson[0] for lesson in LESSONS],
            "selectors": [],
            "dialogs": [
                "Source picker",
                *[f"{name} picker" for name in settings.PATH_FIELDS],
                "Video input picker",
                "Video output picker",
                "Preset save picker",
                "Preset load picker",
                "Recording folder picker",
                "Raw camera consent",
                "Private recording consent",
                "Calibration ready",
                "Open countdown",
                "Open sampling",
                "Open samples collected",
                "Closed countdown",
                "Closed sampling",
                "Insufficient observations",
                "Overlapping samples",
            ],
            "states": [
                "Idle",
                "Synthetic demo",
                "Clean output",
                "Clean output reopened",
                "Optional overrides",
                "Preview suppressed",
                "Video ready",
                "Illustrative Video progress",
                "Illustrative error",
                "Illustrative helper job",
                "Synthetic calibration applied",
            ],
        }

    def settle(self) -> None:
        for _ in range(3):
            self.app.processEvents()

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        if self.window._dark != (theme == "dark"):
            self.window.toggle_theme()
        self.settle()

    def visible_controls(self) -> list[str]:
        result = []
        for name, control in self.window.controls.items():
            editor = control.editor
            if (
                editor.isVisible()
                and QRegion(editor.rect())
                .subtracted(
                    editor.visibleRegion(),
                )
                .isEmpty()
            ):
                result.append(name)
        return result

    def capture(
        self,
        widget: QWidget,
        key: str,
        title: str,
        group: str,
        source: object,
        *,
        coverage: dict[str, list[str]] | None = None,
        note: str = "",
    ) -> None:
        self.settle()
        identifier = f"{slug(key)}-{self.theme}"
        filename = identifier + ".png"
        pixmap = widget.grab()
        if pixmap.isNull() or not pixmap.save(str(self.captures / filename)):
            raise RuntimeError(f"Cannot capture {identifier}")
        raw = (self.captures / filename).read_bytes()
        represented = (
            ["virtual_camera_width", "virtual_camera_height"]
            if widget is self.window and self.window.output_resolution.isVisible()
            else []
        )
        self.images.append(
            {
                "id": identifier,
                "title": title,
                "group": group,
                "theme": self.theme,
                "mode": "Video" if self.window._mode else "Live",
                "file": "captures\\" + filename,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "width": pixmap.width(),
                "height": pixmap.height(),
                "visibleControls": self.visible_controls() if widget is self.window else [],
                "representedControls": represented,
                "coverage": coverage or {},
                "sources": [source_reference(source)],
                "note": note
                or "Actual native widgets with synthetic/example data; no camera input.",
            }
        )
        print(identifier, flush=True)

    def reset(self, mode: int = 0) -> None:
        self.window._processing_video = False
        self.window._set_busy(False)
        self.window._apply_values(self.defaults)
        self.window.work_mode.setCurrentIndex(mode)
        self.window._clear_signals()
        self.window.tools_action.setChecked(False)
        self.window.model_force.setChecked(False)
        self.window.error_label.hide()
        self.window.job_progress.hide()
        self.window.status.setText("SYNTHETIC GUI REFERENCE / NO CAMERA INPUT / EXAMPLE DATA")
        self.window.session_summary.setText("Illustrative layout / not publishing")
        if mode == 0:
            self.window.preview.image = self.program.copy()
            self.window.preview.update()
        for section in self.window.sections.values():
            section.set_expanded(False)
        self.settle()

    def scroll_capture(
        self,
        key: str,
        title: str,
        group: str,
        source: object,
        coverage: dict,
    ) -> None:
        scroll = self.window.pages.currentWidget()
        if not isinstance(scroll, QScrollArea):
            raise TypeError("Settings pages must remain scrollable")
        self.settle()
        bar = scroll.verticalScrollBar()
        maximum = bar.maximum()
        step = max(80, scroll.viewport().height() - 90)
        positions = sorted({0, maximum, *range(0, maximum + 1, step)})
        for index, position in enumerate(positions, 1):
            bar.setValue(position)
            suffix = f" / part {index} of {len(positions)}" if len(positions) > 1 else ""
            self.capture(
                self.window,
                f"{key}-part-{index}",
                title + suffix,
                group,
                source,
                coverage=coverage,
            )

    def demo(self) -> None:
        self.window.start_demo()
        deadline = time.monotonic() + 25
        while self.window.preview.image.isNull() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.preview.image.isNull():
            raise RuntimeError("The synthetic demo did not become ready")
        self.program = self.window.preview.image.copy()
        for theme in ("dark", "light"):
            self.set_theme(theme)
            self.capture(
                self.window,
                "demo",
                "Synthetic demo and locked settings",
                "Work modes",
                StudioWindow.start_demo,
                coverage={"states": ["Synthetic demo"]},
            )
            self.capture(
                self.window.output_window,
                "clean-output",
                "Clean output window",
                "Output",
                VideoCanvas.set_frame,
                coverage={"states": ["Clean output"]},
            )
            same = self.window.output_window
            same.close()
            self.window.clean_output_button.click()
            if self.window.output_window is not same or not same.isVisible():
                raise RuntimeError("Clean output did not reopen")
            self.capture(
                same,
                "clean-output-reopened",
                "Clean output reopened without restart",
                "Output",
                StudioWindow._toggle_clean_output,
                coverage={"states": ["Clean output reopened"]},
            )
        self.window.stop()
        deadline = time.monotonic() + 10
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            raise RuntimeError("Synthetic demo did not stop")
        self.window.timer.stop()
        self.window.output_window.hide()

    def settings_views(self) -> None:
        for page in self.window.page_names:
            self.reset(1 if page == "Video file" else 0)
            self.window.page_selector.setCurrentText(page)
            for (section_page, _), section in self.window.sections.items():
                if section_page == page:
                    section.set_expanded(True)
            self.scroll_capture(
                "page-" + page,
                page + " / complete page",
                "Settings pages",
                StudioWindow._build_ui,
                {"pages": [page]},
            )
        for (page, name), section in self.window.sections.items():
            self.reset()
            self.window.page_selector.setCurrentText(page)
            section.set_expanded(True)
            self.scroll_capture(
                "section-" + page + "-" + name,
                page + " / " + name,
                "Expanded sections",
                DisclosureSection.set_expanded,
                {"sections": [f"{page} / {name}"]},
            )
        self.reset()
        self.window.page_selector.setCurrentText("Camera")
        self.window.sections["Camera", "Input source"].set_expanded(True)
        self.window.input_type.setCurrentIndex(1)
        self.scroll_capture(
            "custom-source",
            "Camera / custom stream or recording",
            "Settings pages",
            StudioWindow._show_source_mode,
            {},
        )
        self.reset()
        self.window.page_selector.setCurrentText("Camera")
        self.window.sections["Camera", "Capture & tracking"].set_expanded(True)
        for name, value in (
            ("width", 1280),
            ("height", 720),
            ("fps", 30.0),
            ("duration", 60.0),
            ("preview_height", 600),
        ):
            self.window.controls[name].set_value(value)
        self.window._refresh_settings()
        self.scroll_capture(
            "capture-overrides",
            "Camera / optional capture limits enabled",
            "Settings pages",
            StudioWindow._refresh_settings,
            {"states": ["Optional overrides"]},
        )
        for page in ("Camera", "Avatar & eyes", "Output & effects", "Tracking labs", "Models"):
            self.reset(1)
            self.window.page_selector.setCurrentText(page)
            for (section_page, _), section in self.window.sections.items():
                if section_page == page:
                    section.set_expanded(True)
            self.scroll_capture(
                "video-scope-" + page,
                page + " / Video-mode availability",
                "Video scope",
                StudioWindow._set_busy,
                {},
            )
        self.reset()
        self.window.page_selector.setCurrentText("Models")
        self.window.sections["Models", "Model files"].set_expanded(True)
        self.window.model_force.setChecked(True)
        self.scroll_capture(
            "force-models",
            "Models / explicit force-download option",
            "Settings pages",
            StudioWindow.download_model,
            {},
        )

    def tools_and_diagnostics(self) -> None:
        self.reset()
        self.window.page_selector.setCurrentText("Tracking labs")
        self.window.sections["Tracking labs", "Local diagnostics"].set_expanded(True)
        for name in ("debug_face_preview", "tracking_debug", "full_body"):
            self.window.controls[name].set_value(True)
        self.window._refresh_settings()
        self.window.raw_face.set_frame(self.raw)
        self.window.face_mesh.set_frame(self.face)
        self.window.skeleton.set_frame(self.body)
        state = _synthetic_debug_state()
        self.window._display_telemetry(
            RuntimeTelemetry(
                face=state,
                raw_face=state,
                render_face=state,
                effective_detected=True,
                demo=True,
                frame_size=(1280, 720),
            ),
            False,
        )
        for index in range(self.window.diagnostic_tabs.count()):
            self.window.diagnostic_tabs.setCurrentIndex(index)
            title = self.window.diagnostic_tabs.tabText(index)
            self.capture(
                self.window,
                "diagnostic-" + title,
                "Raw face above " + title,
                "Diagnostics",
                StudioWindow._build_diagnostics,
                coverage={"diagnostics": ["Raw face", title]},
                note="Synthetic face/body landmarks and NOT A FACE pattern; no physical tracking.",
            )
        self.window.tools_action.setChecked(True)
        for index in range(self.window.console_tabs.count()):
            self.window.console_tabs.setCurrentIndex(index)
            title = self.window.console_tabs.tabText(index)
            self.capture(
                self.window,
                "tools-" + title,
                "Tools / " + title,
                "Tools",
                StudioWindow._build_console,
                coverage={"tools": [title]},
            )

    def menus_and_selectors(self) -> None:
        self.reset()
        menus = [(action.text(), action.menu()) for action in self.window.menuBar().actions()]
        menus.append(("Presets", self.window.preset_menu))
        for title, menu in menus:
            if not isinstance(menu, QMenu):
                raise TypeError("Expected native menu")
            menu.popup(self.window.mapToGlobal(QPoint(350, 100)))
            self.capture(
                menu,
                "menu-" + title,
                title + " menu",
                "Menus",
                StudioWindow._build_ui if title == "Presets" else StudioWindow._build_menu,
                coverage={"menus": [title]},
            )
            menu.close()
        selectors = [
            ("Settings page", self.window.page_selector, "Camera", 0, None, StudioWindow._build_ui),
            (
                "Camera input type",
                self.window.input_type,
                "Camera",
                0,
                "Input source",
                StudioWindow._build_source_selector,
            ),
            (
                "Native camera",
                self.window.native_camera,
                "Camera",
                0,
                "Input source",
                StudioWindow._build_source_selector,
            ),
            (
                "Virtual camera resolution",
                self.window.output_resolution,
                "Output & effects",
                0,
                "Video output",
                StudioWindow._build_resolution_selector,
            ),
            (
                "Video quality",
                self.window.video_quality,
                "Video file",
                1,
                None,
                StudioWindow._build_video_setup,
            ),
        ]
        for page, fields in settings.PAGES.items():
            for field in fields:
                editor = self.window.controls[field.name].editor
                if isinstance(editor, QComboBox):
                    section = next(
                        name
                        for (owner, name), item in self.window.sections.items()
                        if owner == page
                        and self.window.controls[field.name].isAncestorOf(editor)
                        and item.isAncestorOf(editor)
                    )
                    selectors.append(
                        (field.label, editor, page, 0, section, StudioWindow._add_control)
                    )
        for title, combo, page, mode, section, source in selectors:
            if title not in self.expected["selectors"]:
                self.expected["selectors"].append(title)
            self.reset(mode)
            self.window.page_selector.setCurrentText(page)
            if section is not None:
                self.window.sections[page, section].set_expanded(True)
            scroll = self.window.pages.currentWidget()
            if isinstance(scroll, QScrollArea):
                scroll.ensureWidgetVisible(combo, 0, 15)
            combo.showPopup()
            self.capture(
                combo.view().window(),
                "selector-" + title,
                title + " choices",
                "Choices",
                source,
                coverage={"selectors": [title]},
            )
            combo.hidePopup()

    def tutorials(self) -> None:
        self.reset()
        for index, (title, _, _) in enumerate(LESSONS):
            self.window.show_tutorial(index)
            dialog = self.window._tutorial
            if dialog is None:
                raise RuntimeError("Tutorial did not open")
            self.settle()
            bar = dialog.text.verticalScrollBar()
            maximum = bar.maximum()
            step = max(80, dialog.text.viewport().height() - 60)
            positions = sorted({0, maximum, *range(0, maximum + 1, step)})
            for part, position in enumerate(positions, 1):
                bar.setValue(position)
                suffix = f" / part {part} of {len(positions)}" if len(positions) > 1 else ""
                self.capture(
                    dialog,
                    f"tutorial-{index}-part-{part}",
                    title + suffix,
                    "Tutorial",
                    StudioWindow.show_tutorial,
                    coverage={"tutorials": [title]},
                )
            dialog.close()
        self.window.show_tutorial(0)
        dialog = self.window._tutorial
        if dialog is None:
            raise RuntimeError("Tutorial did not open")
        title = "Tutorial lesson"
        if title not in self.expected["selectors"]:
            self.expected["selectors"].append(title)
        dialog.selector.showPopup()
        self.capture(
            dialog.selector.view().window(),
            "selector-tutorial",
            "Tutorial lesson choices",
            "Choices",
            StudioWindow.show_tutorial,
            coverage={"selectors": [title]},
        )
        dialog.selector.hidePopup()
        dialog.close()

    def file_picker(
        self,
        purpose: str,
        source: object,
        save: bool = False,
        directory: bool = False,
    ):
        def show(parent: QWidget, title: str, *args, **kwargs):
            dialog = QFileDialog(parent, title, str(self.fixtures))
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            dialog.setSidebarUrls([QUrl.fromLocalFile(str(self.fixtures))])
            if directory:
                dialog.setFileMode(QFileDialog.FileMode.Directory)
                dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            elif save:
                dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
                dialog.setFileMode(QFileDialog.FileMode.AnyFile)
                dialog.selectFile("example-new-output.mkv")
            else:
                dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            if len(args) > 1 and args[1]:
                dialog.setNameFilter(args[1])
            dialog.resize(900, 600)
            dialog.show()
            self.window._style_titlebar(dialog)
            self.capture(
                dialog,
                "picker-" + purpose,
                purpose,
                "File dialogs",
                source,
                coverage={"dialogs": [purpose]},
                note="Controlled Qt file-picker specimen with example files; the normal OS "
                "picker can look different. This capture is cancelled and writes no user data.",
            )
            dialog.reject()
            return "" if directory else ("", "")

        return show

    def file_dialogs(self) -> None:
        self.reset()
        for field in ("source", *sorted(settings.PATH_FIELDS)):
            purpose = "Source picker" if field == "source" else field + " picker"
            method = self.window.controls[field]._browse
            with patch.object(QFileDialog, "getOpenFileName", self.file_picker(purpose, method)):
                method()
        for purpose, method, save, directory in (
            ("Video input picker", self.window._choose_video_input, False, False),
            ("Video output picker", self.window._choose_video_output, True, False),
            ("Preset save picker", self.window._save_preset_dialog, True, False),
            ("Preset load picker", self.window._load_preset_dialog, False, False),
            ("Recording folder picker", self.window._choose_record_folder, False, True),
        ):
            function = (
                "getExistingDirectory"
                if directory
                else "getSaveFileName"
                if save
                else "getOpenFileName"
            )
            with (
                patch("kardboard_vtuber.gui.window.data_root", lambda: self.fixtures),
                patch.object(
                    QFileDialog, function, self.file_picker(purpose, method, save, directory)
                ),
            ):
                method()

    def consent_dialogs(self) -> None:
        def warning(purpose: str):
            def show(parent, title, message, *args):
                dialog = QMessageBox(parent)
                dialog.setIcon(QMessageBox.Icon.Warning)
                dialog.setWindowTitle(title)
                dialog.setText(message)
                dialog.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                dialog.setDefaultButton(QMessageBox.StandardButton.No)
                dialog.show()
                self.window._style_titlebar(dialog)
                self.capture(
                    dialog,
                    "consent-" + purpose,
                    purpose,
                    "Consent",
                    StudioWindow._confirm,
                    coverage={"dialogs": [purpose]},
                    note="The actual consent text; answered No. No camera or recording starts.",
                )
                dialog.reject()
                return QMessageBox.StandardButton.No

            return show

        self.reset()
        self.window.controls["debug_face_preview"].set_value(True)
        with patch.object(QMessageBox, "warning", warning("Raw camera consent")):
            self.window.start_camera()
        if self.window.worker is not None:
            raise RuntimeError("Declined raw consent must not start a worker")
        self.reset()
        with patch.object(QMessageBox, "warning", warning("Private recording consent")):
            self.window.start_recording()
        if self.window.job is not None:
            raise RuntimeError("Declined recording consent must not start a job")

    def calibration(self) -> None:
        stages = self.expected["dialogs"][-8:]
        for title in stages:
            dialog = EyeCalibrationDialog(self.window)
            if title in ("Open countdown", "Open sampling", "Open samples collected"):
                dialog.begin()
                if title != "Open countdown":
                    dialog.deadline = time.monotonic() - 1
                    dialog.tick()
                    dialog.tick()
                if title == "Open samples collected":
                    dialog.open_samples = [(0.92, 0.94)] * 16
                    dialog.deadline = time.monotonic() - 1
                    dialog.tick()
            elif title in ("Closed countdown", "Closed sampling", "Overlapping samples"):
                dialog.open_samples = [(0.92, 0.94)] * 16
                dialog.sampling = True
                dialog.deadline = time.monotonic() - 1
                dialog.tick()
                dialog.begin()
                if title != "Closed countdown":
                    dialog.deadline = time.monotonic() - 1
                    dialog.tick()
                    dialog.tick()
                if title == "Overlapping samples":
                    dialog.open_samples = [(0.55, 0.55)] * 16
                    dialog.closed_samples = [(0.53, 0.53)] * 16
                    dialog.deadline = time.monotonic() - 1
                    dialog.tick()
            elif title == "Insufficient observations":
                dialog.begin()
                dialog.sampling = True
                dialog.deadline = time.monotonic() - 1
                dialog.tick()
            dialog.timer.stop()
            dialog.show()
            self.window._style_titlebar(dialog)
            self.capture(
                dialog,
                "calibration-" + title,
                title,
                "Eye calibration",
                EyeCalibrationDialog.tick,
                coverage={"dialogs": [title]},
                note="Actual calibration widgets driven by synthetic numeric fixtures. "
                "No face image or personal calibration is collected.",
            )
            dialog.reject()
        self.reset()
        self.window.page_selector.setCurrentText("Avatar & eyes")
        self.window.sections["Avatar & eyes", "Eye tuning"].set_expanded(True)
        self.window._apply_eye_calibration(
            calibrate_eyes([(0.92, 0.94)] * 16, [(0.12, 0.15)] * 16),
        )
        self.scroll_capture(
            "calibration-applied",
            "Synthetic calibration applied to eye controls",
            "Eye calibration",
            StudioWindow._apply_eye_calibration,
            {"states": ["Synthetic calibration applied"]},
        )

    def states(self) -> None:
        self.reset()
        self.window.preview.set_frame(None)
        self.capture(
            self.window,
            "idle",
            "Idle / no source opened",
            "Work modes",
            StudioWindow._clear_signals,
            coverage={"states": ["Idle"]},
        )
        self.window.controls["headless"].set_value(True)
        self.window._refresh_settings()
        self.window._set_preview_hint(suppressed=True)
        self.window.preview.set_frame(None)
        self.capture(
            self.window,
            "headless",
            "Explicitly suppressed preview",
            "Work modes",
            StudioWindow._set_preview_hint,
            coverage={"states": ["Preview suppressed"]},
        )
        self.reset(1)
        self.capture(
            self.window,
            "video-ready",
            "Video file / ready",
            "Work modes",
            StudioWindow._build_video_setup,
            coverage={"states": ["Video ready"]},
        )
        self.window._processing_video = True
        self.window._set_busy(True)
        self.window.video_progress.setValue(420)
        self.window.video_progress_label.setText(
            "ILLUSTRATIVE PROGRESS / 42 frames / 1.40s of source / 1280 x 720",
        )
        self.window.status.setText("ILLUSTRATIVE EXPORT STATE / NO VIDEO JOB RUNNING")
        self.capture(
            self.window,
            "video-progress",
            "Video export progress and locked controls",
            "Work modes",
            StudioWindow._display_export_progress,
            coverage={"states": ["Illustrative Video progress"]},
            note="Illustrative state of the actual progress/lock widgets; no video is processed.",
        )
        self.reset()
        self.window._show_error(
            "ILLUSTRATIVE ERROR: the selected model is missing. Open Models to choose a path "
            "or verify/download it. No camera was opened.",
        )
        self.capture(
            self.window,
            "error",
            "Recoverable error details",
            "Work modes",
            StudioWindow._show_error,
            coverage={"states": ["Illustrative error"]},
        )
        self.reset()
        self.window.page_selector.setCurrentText("Models")
        self.window.sections["Models", "Model files"].set_expanded(True)
        self.window._set_busy(True)
        self.window.job_progress.show()
        self.window.status.setText("ILLUSTRATIVE HELPER LOCK / NO DOWNLOAD OR CAPTURE RUNNING")
        self.capture(
            self.window,
            "helper-job",
            "Helper-job lock state",
            "Work modes",
            StudioWindow._set_busy,
            coverage={"states": ["Illustrative helper job"]},
            note="Actual lock/progress widgets in an illustrative helper state; no job starts.",
        )
        self.window._set_busy(False)

    def complete_controls(self) -> None:
        visible = {
            name
            for image in self.images
            if image["theme"] == self.theme
            for name in image["visibleControls"] + image["representedControls"]
        }
        for page, fields in settings.PAGES.items():
            for field in fields:
                if field.name in visible:
                    continue
                self.reset()
                self.window.page_selector.setCurrentText(page)
                for (owner, _), section in self.window.sections.items():
                    if owner == page:
                        section.set_expanded(True)
                if field.name == "source":
                    self.window.input_type.setCurrentIndex(1)
                scroll = self.window.pages.currentWidget()
                if not isinstance(scroll, QScrollArea):
                    raise TypeError("Expected settings scroll area")
                scroll.ensureWidgetVisible(self.window.controls[field.name].editor, 0, 20)
                self.capture(
                    self.window,
                    "control-detail-" + field.name,
                    field.label + " / complete control",
                    "Control details",
                    StudioWindow._add_control,
                )

    def run(self) -> Path:
        try:
            self.demo()
            for theme in ("dark", "light"):
                self.set_theme(theme)
                self.settings_views()
                self.tools_and_diagnostics()
                self.menus_and_selectors()
                self.tutorials()
                self.file_dialogs()
                self.consent_dialogs()
                self.calibration()
                self.states()
                self.complete_controls()
            references = [
                source_reference(symbol)
                for symbol in (
                    StudioWindow._build_ui,
                    DisclosureSection,
                    EyeCalibrationDialog,
                    VideoCanvas,
                    StudioWindow._apply_theme,
                )
            ]
            from kardboard_vtuber.gui.output import CleanOutputWindow
            from kardboard_vtuber.gui.theme import stylesheet
            from kardboard_vtuber.gui.tutorial import TutorialDialog

            references.extend(
                (
                    source_reference(CleanOutputWindow),
                    source_reference(TutorialDialog),
                    source_reference(settings.RecordingOptions),
                    source_reference(stylesheet),
                    source_reference(_synthetic_debug_state),
                    source_reference(_synthetic_body_state),
                )
            )
            files = sorted(
                {
                    *[reference["file"] for reference in references],
                    str(Path(__file__).resolve().relative_to(ROOT)),
                    "pyproject.toml",
                    str(Path("src") / "kardboard_vtuber" / "__init__.py"),
                }
            )
            source_hashes = {
                filename: hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
                for filename in files
            }
            manifest = {
                "schemaVersion": 1,
                "version": __version__,
                "capturedAt": datetime.now(UTC).isoformat(),
                "syntheticOnly": True,
                "platform": QApplication.platformName(),
                "runtimeControls": sorted(settings.parser_actions()),
                "expected": self.expected,
                "sources": references,
                "sourceHashes": source_hashes,
                "screenshots": self.images,
                "scope": "Every current named Studio page/section/tab/menu/selector/dialog and "
                "major operating view, including all necessary scroll parts, in both themes. "
                "Not every numeric value, resizing combination or OS file-dialog variant.",
            }
            validate_coverage(manifest)
            output = self.output / "capture-manifest.json"
            output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(
                json.dumps({"screenshots": len(self.images), "manifest": str(output)}), flush=True
            )
            return output
        finally:
            self.window._processing_video = False
            if self.window.worker is not None:
                self.window.stop()
                deadline = time.monotonic() + 10
                while self.window.worker is not None and time.monotonic() < deadline:
                    self.app.processEvents()
                    time.sleep(0.01)
                if self.window.worker is not None:
                    raise RuntimeError("Owned synthetic worker did not finish during cleanup")
            self.window._set_busy(False)
            if self.window._tutorial is not None:
                self.window._tutorial.close()
            self.window.close()
            self.settle()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build" / "gui-visual-reference")
    args = parser.parse_args()
    ReferenceCapture(args.output_dir).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
