"""KardboardCode Studio: native controls around the shared camera runtime."""

from __future__ import annotations

import argparse
import codecs
import os
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QProcess, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QDesktopServices,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from kardboard_vtuber.app_paths import command_prefix, data_root, recordings_root, scripts_root
from kardboard_vtuber.camera.devices import LocalCameraDevice, decode_camera_inventory
from kardboard_vtuber.cli import live_tuning
from kardboard_vtuber.gui import settings
from kardboard_vtuber.gui.calibration import EyeCalibrationDialog
from kardboard_vtuber.gui.output import CleanOutputWindow
from kardboard_vtuber.gui.settings import (
    LIVE_FIELDS,
    MODEL_SCRIPTS,
    PAGES,
    RecordingOptions,
    SettingValue,
)
from kardboard_vtuber.gui.tutorial import LESSONS, TutorialDialog
from kardboard_vtuber.gui.video_worker import VideoExportWorker
from kardboard_vtuber.gui.widgets import (
    DisclosureSection,
    ErrorBanner,
    OptionControl,
    VideoCanvas,
)
from kardboard_vtuber.gui.worker import SessionWorker
from kardboard_vtuber.runtime import RuntimeBridge, RuntimeTelemetry, redact
from kardboard_vtuber.tracking.eyes import EyeSensitivity
from kardboard_vtuber.video import VideoExportOptions, VideoProgress

ICON_PATH = Path(__file__).parent / "assets" / "kardboardcode-icon.ico"


class StudioWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KardboardCode Studio")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setMinimumSize(960, 600)
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        width = min(
            1440, available.width() - 32, (available.height() - 64) * 16 // 9,
        ) if available is not None else 1440
        width = width // 16 * 16
        self.resize(width, width // 16 * 9)
        self.values = settings.defaults()
        self.controls: dict[str, OptionControl] = {}
        self.sections: dict[tuple[str, str], DisclosureSection] = {}
        self.worker: SessionWorker | VideoExportWorker | None = None
        self.bridge: RuntimeBridge | None = None
        self.job: QProcess | None = None
        self._job_kind = ""
        self._camera_output = ""
        self._native_devices: tuple[LocalCameraDevice, ...] = ()
        self._native_pair_shown: tuple[str, str] | None = None
        self._source_mode = 0
        self._local_source = "0"
        self._local_backend = "auto"
        self._custom_source = ""
        self._custom_backend = "auto"
        self._job_error = False
        self._job_stop: Path | None = None
        self._job_temp: tempfile.TemporaryDirectory[str] | None = None
        self._download_temp: Path | None = None
        self._pending_output = ""
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._closing = False
        self._exit_code = 0
        self._last_packet_at = 0.0
        self._dark = True
        self._mode = 0
        self._processing_video = False
        self._calibration: EyeCalibrationDialog | None = None
        self._tutorial: TutorialDialog | None = None
        self._model_status: dict[str, QLabel] = {}
        self._model_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self.output_window = CleanOutputWindow(self, self.windowIcon())
        self._sync_source_mode()
        self._apply_theme()
        self._refresh_settings()
        self._set_busy(False)
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._poll_runtime)
        self.timer.start()
        self._append_log("[STUDIO] Ready. No camera or output is open. Try demo or open Tutorial.")

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)
        header = QHBoxLayout()
        header.setSpacing(8)
        logo = QLabel()
        logo.setPixmap(self.windowIcon().pixmap(32, 32))
        header.addWidget(logo)
        title = QLabel("Kardboard / Studio")
        title.setObjectName("appTitle")
        header.addWidget(title)
        self.work_mode = QTabBar()
        self.work_mode.setObjectName("workMode")
        self.work_mode.setExpanding(False)
        self.work_mode.setDrawBase(False)
        self.work_mode.addTab("Live")
        self.work_mode.addTab("Video")
        self.work_mode.setTabToolTip(0, "Camera and streaming")
        self.work_mode.setTabToolTip(1, "Process a prerecorded video")
        self.work_mode.currentChanged.connect(self._change_work_mode)
        header.addWidget(self.work_mode)
        header.addStretch()
        self.theme_button = QPushButton("Theme")
        self.theme_button.setToolTip("Switch dark / light theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.help_button = QPushButton("Tutorial")
        self.help_button.clicked.connect(self.show_tutorial)
        self.demo_button = QPushButton("Try demo")
        self.demo_button.clicked.connect(self.start_demo)
        self.start_button = QPushButton("Start camera")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        for button in (
            self.theme_button,
            self.help_button,
            self.demo_button,
            self.start_button,
            self.stop_button,
        ):
            button.setMinimumHeight(32)
            header.addWidget(button)
        root.addLayout(header)
        self.status = QLabel("IDLE / NO CAMERA CONNECTED")
        self.status.setObjectName("status")
        self.status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        root.addWidget(self.status)
        self.error_label = ErrorBanner()
        self.error_label.hide()
        root.addWidget(self.error_label)
        self.workspace_split = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_split.setChildrenCollapsible(False)
        controls_panel = QFrame()
        controls_panel.setObjectName("panel")
        controls_panel.setMinimumWidth(300)
        controls_panel.setMaximumWidth(420)
        panel_layout = QVBoxLayout(controls_panel)
        panel_layout.setContentsMargins(12, 10, 12, 8)
        panel_layout.setSpacing(8)
        top = QHBoxLayout()
        heading = QLabel("Settings")
        heading.setObjectName("panelTitle")
        top.addWidget(heading, 1)
        self.preset_menu = QMenu(self)
        self.save_action = QAction("Save source-free preset...", self)
        self.save_action.triggered.connect(self._save_preset_dialog)
        self.load_action = QAction("Load preset...", self)
        self.load_action.triggered.connect(self._load_preset_dialog)
        self.reset_action = QAction("Reset settings", self)
        self.reset_action.triggered.connect(self.reset_settings)
        self.preset_menu.addActions((self.save_action, self.load_action, self.reset_action))
        presets = QPushButton("Presets")
        presets.setMenu(self.preset_menu)
        top.addWidget(presets)
        panel_layout.addLayout(top)
        self.page_selector = QComboBox()
        self.page_selector.setAccessibleName("Settings page")
        self.page_names = [
            "Camera",
            "Video file",
            "Avatar & eyes",
            "Output & effects",
            "Tracking labs",
            "Private capture",
            "Models",
            "Tutorial",
        ]
        self.page_selector.addItems(self.page_names)
        panel_layout.addWidget(self.page_selector)
        self.live_hint = QLabel(
            "LIVE controls apply immediately. Other settings unlock after Stop."
        )
        self.live_hint.setObjectName("hint")
        self.live_hint.setWordWrap(True)
        panel_layout.addWidget(self.live_hint)
        self.pages = QStackedWidget()
        self.pages.setMinimumSize(0, 0)
        actions = settings.parser_actions()
        for name in self.page_names:
            page = QWidget()
            content = QVBoxLayout(page)
            content.setContentsMargins(0, 8, 8, 8)
            content.setSpacing(10)
            if name in PAGES:
                self._build_control_page(name, content, actions)
            elif name == "Video file":
                self._build_video_setup(content)
            elif name == "Private capture":
                self._build_recording_page(content)
            else:
                self._build_guide_page(content)
            content.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setMinimumSize(0, 0)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
        self.page_selector.currentIndexChanged.connect(self.pages.setCurrentIndex)
        panel_layout.addWidget(self.pages, 1)
        self.workspace_split.addWidget(controls_panel)
        self.workspace_split.addWidget(self._build_workspace())
        self.workspace_split.setStretchFactor(0, 0)
        self.workspace_split.setStretchFactor(1, 1)
        self.workspace_split.setSizes([340, 1000])
        root.addWidget(self.workspace_split, 1)
        self.setCentralWidget(central)
        self._build_menu()

    def _build_control_page(
        self,
        name: str,
        layout: QVBoxLayout,
        actions: dict[str, argparse.Action],
    ) -> None:
        descriptions = {
            "Camera": "Choose an input. Only Start camera opens capture.",
            "Avatar & eyes": (
                "Tune while watching the preview. Calibrate with your actual live eye scores."
            ),
            "Output & effects": "Output settings are independent of capture and local preview.",
            "Tracking labs": "EXPERIMENTAL / Face-only remains the selected workflow.",
            "Models": "Present does not mean checksum verified. Verify / download to check.",
        }
        intro = QLabel(descriptions[name])
        intro.setObjectName("sectionIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        if name == "Models":
            self.model_force = QCheckBox("Force re-download / replace an existing model")
            self.model_force.setToolTip(
                "Explicitly run the checksum-verifying downloader with --force.",
            )
            layout.addWidget(self.model_force)
        fields = {field.name: field for field in PAGES[name]}
        sections = settings.SECTIONS.get(name, (
            settings.Section("Model files", tuple(fields), True),
        ))
        for definition in sections:
            section = DisclosureSection(definition.title, expanded=definition.expanded)
            self.sections[name, definition.title] = section
            layout.addWidget(section)
            if name == "Avatar & eyes" and definition.title == "Eye tuning":
                self.calibrate_button = QPushButton("Calibrate OPEN / CLOSED eyes...")
                self.calibrate_button.setToolTip(
                    "Use real open/closed samples; closed eyes do not always score zero. "
                    "Raise blink thresholds for missed closures; lower them for false closures.",
                )
                self.calibrate_button.clicked.connect(self.start_eye_calibration)
                section.content.addWidget(self.calibrate_button)
                self.eye_states: dict[str, QLabel] = {}
                row = QHBoxLayout()
                for eye, letter in (("left", "K"), ("right", "C")):
                    state = QLabel(f"Your {eye.upper()} / {letter}: --")
                    state.setObjectName("hint")
                    self.eye_states[eye] = state
                    row.addWidget(state)
                section.content.addLayout(row)
            for field_name in definition.fields:
                self._add_control(fields[field_name], actions[field_name], section.content)

    def _add_control(
        self, field: settings.Field, action: argparse.Action, layout: QVBoxLayout,
    ) -> None:
        if field.name == "source":
            self._build_source_selector(layout)
        control = OptionControl(field, action, self.values[field.name])
        self.controls[field.name] = control
        control.changed.connect(self._refresh_settings)
        layout.addWidget(control)
        if field.name in {"virtual_camera_width", "virtual_camera_height"}:
            control.hide()
            if field.name == "virtual_camera_height":
                self._build_resolution_selector(layout)
        if field.name == "source":
            environment = QPushButton("Use KARDBOARD_CAMERA_URL from this process")
            environment.clicked.connect(self._use_environment)
            self.source_environment_button = environment
            layout.addWidget(environment)
        if field.name in MODEL_SCRIPTS:
            row = QHBoxLayout()
            state = QLabel()
            state.setObjectName("hint")
            self._model_status[field.name] = state
            row.addWidget(state, 1)
            download = QPushButton("Verify / download")
            self._model_buttons[field.name] = download
            download.clicked.connect(
                lambda checked=False, model=field.name: self.download_model(model),
            )
            row.addWidget(download)
            layout.addLayout(row)

    def _build_resolution_selector(self, layout: QVBoxLayout) -> None:
        layout.addWidget(QLabel("Virtual camera resolution / restart required"))
        self.output_resolution = QComboBox()
        self.output_resolution.setAccessibleName("Virtual camera output resolution")
        for label, width, height in (
            ("SD / 4:3", 640, 480), ("HD / 720p", 1280, 720),
            ("Full HD / 1080p", 1920, 1080), ("QHD / 1440p (2K class)", 2560, 1440),
            ("UHD / 2160p (4K)", 3840, 2160),
            ("Portrait HD", 720, 1280), ("Portrait Full HD", 1080, 1920),
        ):
            self.output_resolution.addItem(f"{label} / {width} x {height}", (width, height))
        screen = QApplication.primaryScreen()
        if screen is not None:
            size = screen.size()
            ratio = screen.devicePixelRatio()
            width = max(2, round(size.width() * ratio / 2) * 2)
            height = max(2, round(size.height() * ratio / 2) * 2)
            self.output_resolution.addItem(
                f"Current display / {width} x {height}", "monitor",
            )
        self.output_resolution.currentIndexChanged.connect(self._resolution_selected)
        layout.addWidget(self.output_resolution)
        note = QLabel(
            "Standard sizes or this window's current display. Video-file exports always retain "
            "the input dimensions. Changing monitors does not change an active output.",
        )
        note.setObjectName("hint")
        note.setWordWrap(True)
        layout.addWidget(note)

    def _resolution_selected(self, index: int) -> None:
        pair = self.output_resolution.itemData(index)
        if pair == "monitor":
            screen = self.screen()
            size = screen.size()
            ratio = screen.devicePixelRatio()
            pair = (
                max(2, round(size.width() * ratio / 2) * 2),
                max(2, round(size.height() * ratio / 2) * 2),
            )
            self.output_resolution.setItemText(
                index, f"Current display / {pair[0]} x {pair[1]}",
            )
        if not isinstance(pair, tuple) or len(pair) != 2:
            return
        for name, value in zip(
            ("virtual_camera_width", "virtual_camera_height"), pair, strict=True,
        ):
            self.controls[name].set_value(value)
        self._refresh_settings()

    def _sync_resolution(self) -> None:
        pair = (
            self.controls["virtual_camera_width"].value(),
            self.controls["virtual_camera_height"].value(),
        )
        if self.output_resolution.currentData() == "monitor":
            return
        for index in range(self.output_resolution.count()):
            if self.output_resolution.itemData(index) == pair:
                break
        else:
            self.output_resolution.addItem(
                f"Imported CLI size / {pair[0]} x {pair[1]}", pair,
            )
            index = self.output_resolution.count() - 1
        self.output_resolution.blockSignals(True)
        self.output_resolution.setCurrentIndex(index)
        self.output_resolution.blockSignals(False)

    def _build_video_setup(self, layout: QVBoxLayout) -> None:
        self.video_setup = QGroupBox("Video file")
        form = QVBoxLayout(self.video_setup)
        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText("Choose an existing local video")
        self.video_output = QLineEdit()
        self.video_output.setPlaceholderText("Choose a NEW output filename")
        for title, editor, slot in (
            ("Input video", self.video_input, self._choose_video_input),
            ("Output video", self.video_output, self._choose_video_output),
        ):
            form.addWidget(QLabel(title))
            row = QHBoxLayout()
            row.addWidget(editor, 1)
            browse = QPushButton("Browse")
            browse.clicked.connect(slot)
            row.addWidget(browse)
            form.addLayout(row)
        self.video_quality = QComboBox()
        self.video_quality.addItem("Lossless MKV / original size + audio", "lossless")
        self.video_quality.addItem("High-quality MP4 / lossy, smaller", "mp4")
        self.video_quality.currentIndexChanged.connect(self._video_quality_changed)
        form.addWidget(self.video_quality)
        self.video_mirrored = QCheckBox("The input was already recorded mirrored")
        form.addWidget(self.video_mirrored)
        note = QLabel(
            "Every frame is processed, not live-dropped. Original dimensions and source timing "
            "are retained; compatible audio is copied. Opaque 8-bit SDR inputs only. "
            "Lossless MKV can be large. MP4 is not mathematically lossless. "
            "Completed exports open in your default media player.",
        )
        note.setObjectName("hint")
        note.setWordWrap(True)
        form.addWidget(note)
        self.video_input.textChanged.connect(
            lambda _: self.command.setPlainText(self._video_command())
            if hasattr(self, "command") and self._mode == 1 else None,
        )
        self.video_output.textChanged.connect(
            lambda _: self.command.setPlainText(self._video_command())
            if hasattr(self, "command") and self._mode == 1 else None,
        )
        self.video_mirrored.toggled.connect(
            lambda _: self.command.setPlainText(self._video_command())
            if hasattr(self, "command") and self._mode == 1 else None,
        )
        layout.addWidget(self.video_setup)

    def _choose_video_input(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Choose an existing video")
        if filename:
            self.video_input.setText(filename)
            source = Path(filename)
            suffix = ".mkv" if self.video_quality.currentData() == "lossless" else ".mp4"
            self.video_output.setText(str(source.with_name(source.stem + "-kardboard" + suffix)))

    def _choose_video_output(self) -> None:
        suffix = "*.mkv" if self.video_quality.currentData() == "lossless" else "*.mp4"
        filename, _ = QFileDialog.getSaveFileName(
            self, "Choose a NEW output filename (existing files are not replaced)",
            self.video_output.text(), f"Video ({suffix})",
        )
        if filename:
            self.video_output.setText(filename)

    def _video_quality_changed(self) -> None:
        if self.video_output.text():
            suffix = ".mkv" if self.video_quality.currentData() == "lossless" else ".mp4"
            self.video_output.setText(str(Path(self.video_output.text()).with_suffix(suffix)))

    def _change_work_mode(self, index: int) -> None:
        if self.worker is not None or self.job is not None:
            self.work_mode.blockSignals(True)
            self.work_mode.setCurrentIndex(self._mode)
            self.work_mode.blockSignals(False)
            self._show_error("Stop the current work before switching modes.")
            return
        self._mode = index
        self.video_setup.setEnabled(index == 1)
        self.video_progress_panel.setVisible(index == 1)
        self.start_button.setText("Process video" if index == 1 else "Start camera")
        self.demo_button.setVisible(index == 0)
        self.clean_output_button.setVisible(index == 0)
        self.show_output.setVisible(index == 0)
        self._set_preview_hint()
        self.preview.set_frame(None)
        self.status.setText(
            "VIDEO READY / NO FILE OPENED" if index == 1 else "IDLE / NO CAMERA CONNECTED",
        )
        self.page_selector.setCurrentText("Video file" if index == 1 else "Camera")
        self._set_busy(False)
        self._refresh_settings()

    def _set_preview_hint(self, *, suppressed: bool = False) -> None:
        self.preview.placeholder = (
            "Preview is explicitly suppressed.\n\nProcessing and output continue. "
            "Stop and disable Suppress preview in Camera > Capture & tracking "
            "to display frames here."
            if suppressed else
            "Choose an input video and a NEW output filename.\n\n"
            "Process video renders every frame at original dimensions.\n"
            "No live camera is opened."
            if self._mode == 1 else
            "Your stage is ready.\n\nStart camera when ready, or Try demo "
            "to explore with synthetic imagery.\n\nNo camera starts automatically."
        )

    def _video_command(self) -> str:
        def quote(value: object) -> str:
            return "'" + str(value).replace("'", "''") + "'"
        lines = [
            command_prefix("kardboard_vtuber.video_cli") + " `",
            "  --input-video=" + quote(self.video_input.text()) + " `",
            "  --output-video=" + quote(self.video_output.text()) + " `",
            "  --video-quality " + str(self.video_quality.currentData()) + " `",
        ]
        supported = {
            "physics", "cardboard_renderer", "box_depth_offset", "tracking_width", "face_model",
            "hand_model", "segmentation_model", "brightness", "green_screen", "segmentation_width",
            "hand_occlusion", "hand_tracking_width", "no_motion_filter", *LIVE_FIELDS,
        }
        for name in sorted(supported):
            value = self.values[name]
            if value is False or value is None:
                continue
            flag = "--" + name.replace("_", "-")
            lines.append("  " + flag + ("" if value is True else " " + quote(value)) + " `")
        if self.video_mirrored.isChecked():
            lines.append("  --input-already-mirrored `")
        lines[-1] = lines[-1].removesuffix(" `")
        return "\n".join(lines)

    def start_video(self) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop the current work before starting video processing.")
            return
        if not self.video_input.text().strip() or not self.video_output.text().strip():
            self._show_error("Choose an input video and a new output filename.")
            return
        try:
            values = self.collected_values()
            args = settings.namespace(values)
            quality = self.video_quality.currentData()
            if quality not in ("lossless", "mp4"):
                raise ValueError("Choose lossless MKV or high-quality MP4.")
            options = VideoExportOptions(
                Path(self.video_input.text()), Path(self.video_output.text()), quality,
            )
            self.bridge = RuntimeBridge(live_tuning(args))
            self.worker = VideoExportWorker(
                values, options, self.bridge, already_mirrored=self.video_mirrored.isChecked(),
            )
            self.worker.completed.connect(self._remember_result)
            self.worker.finished.connect(self._worker_finished)
            self.worker.progress.connect(self._display_export_progress)
            self._processing_video = True
            self._exit_code = 0
            self._last_packet_at = 0
            self.video_progress.setRange(0, 1000)
            self.video_progress.setValue(0)
            self.error_label.hide()
            self.output_window.hide()
            self._set_busy(True)
            self.status.setText("VIDEO EXPORT / INITIALIZING MODELS")
            self.video_progress_label.setText("Initializing; no live camera is opened.")
            self.worker.start()
        except (ValueError, OSError) as error:
            self._show_error(str(error))

    def _display_export_progress(self, progress: object) -> None:
        if not isinstance(progress, VideoProgress):
            self._show_error("Video worker returned invalid progress data.")
            return
        if progress.duration and progress.duration > 0:
            self.video_progress.setRange(0, 1000)
            self.video_progress.setValue(min(1000, round(
                progress.seconds / progress.duration * 1000,
            )))
        else:
            self.video_progress.setRange(0, 0)
        self.video_progress_label.setText(
            f"{progress.frames} frames / {progress.seconds:.2f}s of source / "
            f"{progress.width} x {progress.height}",
        )

    def _toggle_clean_output(self, enabled: bool) -> None:
        if not hasattr(self, "output_window"):
            return
        if not enabled:
            self.output_window.hide()
            return
        if self._mode != 0 or self._processing_video:
            self._show_error("Clean output is available in Live mode, not video export.")
            return
        args = settings.namespace(self.values)
        if not self._renders(args):
            self._show_error("Clean output requires cardboard rendering; raw modes stay local.")
            return
        if args.headless:
            self._show_error(
                "Suppress preview is enabled. Stop and disable it for local windows.",
            )
            return
        self.output_window.show()
        self.output_window.raise_()
        self.output_window.activateWindow()

    def start_eye_calibration(self) -> None:
        if (
            self.worker is None or self.worker.demo or self._processing_video
            or self.bridge is None
        ):
            self._show_error("Start a live face-tracking session before calibrating your eyes.")
            return
        if self._calibration is not None:
            self._calibration.reject()
            self._calibration.deleteLater()
        self._calibration = EyeCalibrationDialog(self)
        self._style_titlebar(self._calibration)
        self._calibration.calibrated.connect(self._apply_eye_calibration)
        self._calibration.show()

    def _apply_eye_calibration(self, sensitivity: object) -> None:
        if not isinstance(sensitivity, EyeSensitivity):
            self._show_error("Eye calibration returned an invalid threshold set.")
            return
        updates = {
            "left_blink_threshold": sensitivity.left_closed,
            "right_blink_threshold": sensitivity.right_closed,
            "eye_open_threshold": sensitivity.opened, "wink_threshold": sensitivity.wink,
            "wink_min_difference": sensitivity.difference,
        }
        for name, value in updates.items():
            self.controls[name].set_value(round(value, 2))
        self._refresh_settings()
        self._append_log(
            "[CALIBRATION] Applied OPEN/CLOSED eye samples. Higher blink thresholds make "
            "closure easier; eye decisions use raw signals while geometry stays smoothed.",
        )

    def _build_source_selector(self, layout: QVBoxLayout) -> None:
        layout.addWidget(QLabel("Input type"))
        self.input_type = QComboBox()
        self.input_type.setAccessibleName("Camera input type")
        self.input_type.addItems(
            [
                "This computer's camera",
                "Phone stream / video file / manual source",
            ]
        )
        self.input_type.currentIndexChanged.connect(self._input_type_changed)
        layout.addWidget(self.input_type)
        self.native_panel = QWidget()
        native_layout = QVBoxLayout(self.native_panel)
        native_layout.setContentsMargins(0, 0, 0, 0)
        native_layout.addWidget(QLabel("Laptop / USB / installed camera device"))
        row = QHBoxLayout()
        self.native_camera = QComboBox()
        self.native_camera.setAccessibleName("Native camera device")
        self.native_camera.setMinimumContentsLength(12)
        self.native_camera.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon,
        )
        self.native_camera.currentIndexChanged.connect(self._native_camera_selected)
        self.native_camera.setToolTip(
            "Index 0 is the first device for an API, not an extra camera. Media Foundation and "
            "DirectShow are alternative Windows capture backends; names can refer "
            "to the same hardware.",
        )
        row.addWidget(self.native_camera, 1)
        self.refresh_cameras_button = QPushButton("Refresh")
        self.refresh_cameras_button.clicked.connect(self.refresh_native_cameras)
        row.addWidget(self.refresh_cameras_button)
        native_layout.addLayout(row)
        self.native_hint = QLabel(
            "Refresh lists capture routes. Start opens the selected camera.",
        )
        self.native_hint.setWordWrap(True)
        self.native_hint.setObjectName("hint")
        native_layout.addWidget(self.native_hint)
        layout.addWidget(self.native_panel)

    def _sync_source_mode(self) -> None:
        source = self.controls["source"].value()
        backend = self.controls["backend"].value()
        assert isinstance(source, str) and isinstance(backend, str)
        self._source_mode = 0 if source.isdecimal() else 1
        if self._source_mode == 0:
            self._local_source, self._local_backend = source, backend
        else:
            self._custom_source, self._custom_backend = source, backend
        self.input_type.blockSignals(True)
        self.input_type.setCurrentIndex(self._source_mode)
        self.input_type.blockSignals(False)
        self._show_source_mode()
        self._populate_native_cameras()

    def _show_source_mode(self) -> None:
        local = self._source_mode == 0
        self.native_panel.setVisible(local)
        self.controls["source"].setVisible(not local)
        self.source_environment_button.setVisible(not local)

    def _input_type_changed(self, index: int) -> None:
        if index == self._source_mode:
            return
        source = self.controls["source"].value()
        backend = self.controls["backend"].value()
        assert isinstance(source, str) and isinstance(backend, str)
        if index == 0:
            self._custom_source, self._custom_backend = source, backend
            self.controls["source"].set_value(self._local_source)
            self.controls["backend"].set_value(self._local_backend)
        else:
            self._local_source, self._local_backend = source, backend
            self.controls["source"].set_value(self._custom_source)
            self.controls["backend"].set_value(self._custom_backend)
        self._source_mode = index
        self._show_source_mode()
        self._populate_native_cameras()
        self._refresh_settings()

    def _populate_native_cameras(self) -> None:
        source = self.controls["source"].value()
        backend = self.controls["backend"].value()
        assert isinstance(source, str) and isinstance(backend, str)
        self.native_camera.blockSignals(True)
        self.native_camera.clear()
        if source.isdecimal():
            self.native_camera.addItem(
                f"Current route / camera {source} / "
                + ("automatic backend" if backend == "auto" else backend),
                None,
            )
        else:
            self.native_camera.addItem("Select a local camera", None)
        selected = 0
        for device in self._native_devices:
            api = (
                "Media Foundation / Windows capture"
                if device.backend == "msmf" else "DirectShow / compatibility capture"
            )
            self.native_camera.addItem(f"{device.name} / {api}", device)
            if source == str(device.index) and backend == device.backend:
                selected = self.native_camera.count() - 1
        self.native_camera.setCurrentIndex(selected)
        self.native_camera.blockSignals(False)
        self._native_pair_shown = (source, backend)

    def _native_camera_selected(self, index: int) -> None:
        device = self.native_camera.itemData(index)
        if not isinstance(device, LocalCameraDevice):
            return
        self.controls["source"].set_value(str(device.index))
        self.controls["backend"].set_value(device.backend)
        self._local_source, self._local_backend = str(device.index), device.backend
        self._refresh_settings()

    def refresh_native_cameras(self) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop the current session/job before refreshing the device list.")
            return
        try:
            self._start_job("cameras", scripts_root() / "list_local_cameras.py", [])
        except (ValueError, OSError) as error:
            self._show_error(str(error))

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        workspace.setObjectName("previewWorkspace")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        top = QHBoxLayout()
        heading = QLabel("Preview")
        heading.setObjectName("panelTitle")
        top.addWidget(heading)
        self.diagnostics_notice = QLabel("Diagnostics / local only")
        self.diagnostics_notice.setObjectName("privateNotice")
        self.diagnostics_notice.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed,
        )
        self.diagnostics_notice.hide()
        top.addWidget(self.diagnostics_notice, 1)
        self.preview_note = QLabel("No input / nothing is being published")
        self.preview_note.setObjectName("hint")
        self.preview_note.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.preview_note.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        top.addWidget(self.preview_note, 1)
        self.clean_output_action = QAction("Show clean output", self)
        self.clean_output_action.triggered.connect(lambda: self._toggle_clean_output(True))
        self.clean_output_button = QToolButton()
        self.clean_output_button.setDefaultAction(self.clean_output_action)
        self.clean_output_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.clean_output_button.setAccessibleName("Show or reopen clean output window")
        top.addWidget(self.clean_output_button)
        self.show_output = QCheckBox("Auto-open")
        self.show_output.setChecked(True)
        self.show_output.setToolTip(
            "Open clean output automatically when Live/demo starts. "
            "Unchecking hides it; Show clean output can reopen it without changing "
            "this preference.",
        )
        self.show_output.toggled.connect(self._toggle_clean_output)
        top.addWidget(self.show_output)
        layout.addLayout(top)
        self.preview = VideoCanvas(
            "Your stage is ready.\n\nStart camera when you are ready, or Try demo "
            "to explore with synthetic imagery.\n\nNo camera starts automatically.",
        )
        self.preview.setMinimumSize(320, 180)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_split = QSplitter(Qt.Orientation.Horizontal)
        self.preview_split.setChildrenCollapsible(False)
        self.preview_split.addWidget(self.preview)
        self.preview_split.addWidget(self._build_diagnostics())
        self.preview_split.setStretchFactor(0, 1)
        self.preview_split.setStretchFactor(1, 0)
        layout.addWidget(self.preview_split, 1)
        self.video_progress_panel = QWidget()
        progress = QVBoxLayout(self.video_progress_panel)
        progress.setContentsMargins(0, 0, 0, 0)
        progress.setSpacing(4)
        self.video_progress = QProgressBar()
        self.video_progress.setRange(0, 1000)
        self.video_progress.setValue(0)
        progress.addWidget(self.video_progress)
        self.video_progress_label = QLabel("Choose a video, then Process video.")
        self.video_progress_label.setObjectName("hint")
        progress.addWidget(self.video_progress_label)
        self.video_progress_panel.hide()
        layout.addWidget(self.video_progress_panel)
        self.command = QPlainTextEdit()
        self.command.setReadOnly(True)
        self.command.setMinimumSize(0, 0)
        self.command.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.command.setObjectName("command")
        self._build_console()
        footer = QHBoxLayout()
        footer.setSpacing(6)
        footer.addWidget(self.tools_button)
        self.metrics_strip = self._build_metrics()
        footer.addWidget(self.metrics_strip, 3)
        self.session_summary = QLabel("No input / not publishing")
        self.session_summary.setObjectName("hint")
        self.session_summary.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.session_summary.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        footer.addWidget(self.session_summary, 1)
        layout.addLayout(footer)
        layout.addWidget(self.tools_drawer)
        return workspace

    def _build_metrics(self) -> QWidget:
        strip = QWidget()
        strip.setAccessibleName("Live performance and output cards")
        strip.setMaximumWidth(720)
        row = QHBoxLayout(strip)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.metrics: dict[str, QLabel] = {}
        for name, title in (
            ("camera", "CAMERA FPS"), ("tracking", "TRACKING FPS"),
            ("age", "INTERNAL FRAME AGE"), ("output", "VIDEO OUTPUT"),
        ):
            card = QFrame()
            card.setObjectName("metric")
            card.setAccessibleName(title)
            card.setMinimumWidth(124 if name in ("age", "output") else 116)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 3, 8, 3)
            card_layout.setSpacing(1)
            caption = QLabel(title)
            caption.setObjectName("eyebrow")
            value = QLabel("--")
            value.setObjectName("metricValue")
            value.setAccessibleName(title + " value")
            self.metrics[name] = value
            card_layout.addWidget(caption)
            card_layout.addWidget(value)
            row.addWidget(card, 1)
        return strip

    def _build_diagnostics(self) -> QWidget:
        self.raw_face = VideoCanvas("No face observation.\nNever included in clean output.")
        self.raw_face.setAccessibleName("Raw face diagnostic, local only")
        self.raw_face.setAccessibleDescription("Private pixels; never included in clean output.")
        self.face_mesh = VideoCanvas("Face mesh / pose diagnostic")
        self.face_mesh.setAccessibleName("Face mesh and pose diagnostic, local only")
        self.skeleton = VideoCanvas(
            "Waiting for a body observation.\nThe skeleton never enters clean output.",
        )
        self.skeleton.setAccessibleName("Body skeleton diagnostic, local only")
        for canvas in (self.raw_face, self.face_mesh, self.skeleton):
            canvas.setMinimumSize(120, 120)
            canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.raw_panel = QFrame()
        self.raw_panel.setObjectName("diagnosticCard")
        raw_layout = QVBoxLayout(self.raw_panel)
        raw_layout.setContentsMargins(6, 4, 6, 4)
        raw_layout.setSpacing(4)
        raw_note = QLabel("RAW FACE / LOCAL ONLY")
        raw_note.setObjectName("privateNotice")
        raw_note.setToolTip("Private diagnostic; never included in clean output.")
        raw_layout.addWidget(raw_note)
        raw_layout.addWidget(self.raw_face, 1)
        self.diagnostic_tabs = QTabWidget()
        self.diagnostic_tabs.setAccessibleName("Tracking diagnostics beside the preview")
        self.diagnostic_tabs.addTab(self.face_mesh, "Face / pose")
        self.diagnostic_tabs.addTab(self.skeleton, "Body")
        self.diagnostic_panel = QSplitter(Qt.Orientation.Vertical)
        self.diagnostic_panel.setChildrenCollapsible(False)
        self.diagnostic_panel.setMinimumWidth(240)
        self.diagnostic_panel.setMaximumWidth(480)
        self.diagnostic_panel.addWidget(self.raw_panel)
        self.diagnostic_panel.addWidget(self.diagnostic_tabs)
        self.diagnostic_panel.setStretchFactor(0, 1)
        self.diagnostic_panel.setStretchFactor(1, 1)
        self.diagnostic_panel.hide()
        return self.diagnostic_panel

    def _sync_diagnostics(self) -> None:
        local = self._mode == 0 and not self.values["headless"]
        raw = local and bool(self.values["debug_face_preview"])
        mesh = local and bool(self.values["tracking_debug"])
        body = local and bool(self.values["full_body"])
        opening = self.diagnostic_panel.isHidden() and (raw or mesh or body)
        stacking = raw and (mesh or body) and (
            self.raw_panel.isHidden() or self.diagnostic_tabs.isHidden()
        )
        self.raw_panel.setVisible(raw)
        self.diagnostic_tabs.setTabVisible(0, mesh)
        self.diagnostic_tabs.setTabVisible(1, body)
        self.diagnostic_tabs.setVisible(mesh or body)
        self.diagnostic_panel.setVisible(raw or mesh or body)
        self.preview_split.setMinimumHeight(max(
            self.preview.minimumHeight(),
            self.diagnostic_panel.minimumSizeHint().height() if raw or mesh or body else 0,
        ))
        if opening:
            self.preview_split.setSizes([max(320, self.preview_split.width() - 324), 320])
        if opening or stacking:
            self.diagnostic_panel.setSizes([300, 300])

    def _build_signals(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        signals_page = QWidget()
        signals = QGridLayout(signals_page)
        signals.setContentsMargins(6, 4, 6, 4)
        self.eye_meters: dict[str, QProgressBar] = {}
        self.eye_labels: dict[str, QLabel] = {}
        for row, (name, title) in enumerate(
            (("left", "Your LEFT / K"), ("right", "Your RIGHT / C")),
        ):
            signals.addWidget(QLabel(title), row, 0)
            meter = QProgressBar()
            meter.setRange(0, 1000)
            meter.setTextVisible(False)
            meter.setFixedHeight(8)
            meter.setAccessibleName(title + " openness")
            self.eye_meters[name] = meter
            signals.addWidget(meter, row, 1)
            label = QLabel("raw -- / filtered --")
            label.setObjectName("hint")
            self.eye_labels[name] = label
            signals.addWidget(label, row, 2)
        self.pose_label = QLabel("Yaw --   Pitch --   Roll --   /   Action --")
        self.pose_label.setObjectName("hint")
        signals.addWidget(self.pose_label, 2, 0, 1, 3)
        layout.addWidget(signals_page, 1)
        return panel

    def _build_console(self) -> None:
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(1500)
        self.console.setMinimumSize(0, 0)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setObjectName("console")
        self.tools_drawer = QScrollArea()
        self.tools_drawer.setObjectName("toolsPanel")
        self.tools_drawer.setWidgetResizable(True)
        # Zero retains Qt's 70px scroll-area minimum hint and can clip the image workspace.
        self.tools_drawer.setMinimumSize(0, 1)
        self.tools_drawer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(6, 2, 6, 4)
        toolbar = QHBoxLayout()
        hint = QLabel(
            "Session logs / native libraries may also write to stderr."
        )
        hint.setObjectName("hint")
        toolbar.addWidget(hint, 1)
        copy = QPushButton("Copy logs")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.console.toPlainText()))
        clear = QPushButton("Clear")
        clear.clicked.connect(self.console.clear)
        toolbar.addWidget(copy)
        toolbar.addWidget(clear)
        layout.addLayout(toolbar)
        layout.addWidget(self.console)
        self.console_tabs = QTabWidget()
        self.console_tabs.addTab(body, "Logs")
        command_page = QWidget()
        command_layout = QVBoxLayout(command_page)
        command_hint = QLabel(
            "Camera credentials are excluded. Copy includes the complete command.",
        )
        command_hint.setObjectName("hint")
        command_hint.setWordWrap(True)
        command_toolbar = QHBoxLayout()
        command_toolbar.addWidget(command_hint, 1)
        self.copy_command = QPushButton("Copy complete CLI command")
        self.copy_command.clicked.connect(
            lambda: QApplication.clipboard().setText(self.command.toPlainText()),
        )
        command_toolbar.addWidget(self.copy_command)
        command_layout.addLayout(command_toolbar)
        command_layout.addWidget(self.command, 1)
        self.console_tabs.addTab(command_page, "CLI equivalent")
        self.console_tabs.addTab(self._build_signals(), "Signals")
        close = QToolButton()
        close.setText("Hide")
        close.setAccessibleName("Hide session tools")
        close.clicked.connect(lambda: self.tools_action.setChecked(False))
        self.console_tabs.setCornerWidget(close)
        self.tools_drawer.setWidget(self.console_tabs)
        self.tools_drawer.setMaximumHeight(min(220, max(140, self.height() // 4)))
        self.tools_drawer.hide()
        self.tools_action = QAction("Tools", self)
        self.tools_action.setCheckable(True)
        self.tools_action.setShortcut("Ctrl+J")
        self.tools_action.setToolTip(
            "Show or hide logs, CLI equivalent and numeric signals (Ctrl+J)",
        )
        self.tools_action.toggled.connect(self._set_tools_visible)
        self.addAction(self.tools_action)
        self.tools_button = QToolButton()
        self.tools_button.setObjectName("toolsToggle")
        self.tools_button.setDefaultAction(self.tools_action)
        self.tools_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tools_button.setArrowType(Qt.ArrowType.UpArrow)

    def _set_tools_visible(self, visible: bool) -> None:
        self.tools_drawer.setVisible(visible)
        self.tools_button.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.UpArrow,
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "tools_drawer"):
            self.tools_drawer.setMaximumHeight(min(220, max(140, self.height() // 4)))

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("File")
        menu.addActions((self.save_action, self.load_action, self.reset_action))
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        view = self.menuBar().addMenu("View")
        view.addAction(self.tools_action)
        theme = QAction("Toggle dark / light", self)
        theme.triggered.connect(self.toggle_theme)
        view.addAction(theme)
        view.addAction(self.clean_output_action)
        help_menu = self.menuBar().addMenu("Help")
        guide = QAction("Studio tutorial", self)
        guide.setShortcut("F1")
        guide.triggered.connect(self.show_tutorial)
        help_menu.addAction(guide)

    def _build_recording_page(self, layout: QVBoxLayout) -> None:
        warning = QLabel(
            "RAW PRIVATE RECORDING\nMP4 + CSV contain unmasked camera footage. "
            "The recorder opens its own preview. Stop camera/demo before recording.",
        )
        warning.setObjectName("warning")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        self.record_group = QWidget()
        form = QFormLayout(self.record_group)
        form.setContentsMargins(0, 0, 0, 0)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.record_full_body = QCheckBox("Include body telemetry / full-body routine")
        self.record_free = QCheckBox("Free recording (no guided stages)")
        form.addRow(self.record_full_body)
        form.addRow(self.record_free)
        self.record_duration = self._float_spin(1, 86400, 90)
        self.record_pose_width = self._int_spin(1, 4096, 320)
        self.record_pose_fps = self._float_spin(0.1, 60, 10)
        self.record_countdown = self._float_spin(0, 60, 3)
        self.record_preview_height = self._int_spin(240, 4320, 720)
        self.record_folder = QLineEdit(str(recordings_root()))
        self.record_name = QLineEdit("KardboardCode-studio-session")
        for title, control in (
            ("Free duration / seconds", self.record_duration),
            ("Pose input width", self.record_pose_width),
            ("Pose submissions / second", self.record_pose_fps),
            ("Countdown / seconds", self.record_countdown),
            ("Raw preview height", self.record_preview_height),
            ("Output folder", self.record_folder),
            ("Filename stem", self.record_name),
        ):
            form.addRow(title, control)
        folder = QPushButton("Choose output folder")
        folder.clicked.connect(self._choose_record_folder)
        form.addRow(folder)
        layout.addWidget(self.record_group)
        note = QLabel(
            "Uses Camera source, transforms, brightness, face input width and Models selections. "
            "Guided routines set their own duration. The existing fixed-FPS writer may compress "
            "playback when delivered camera FPS is lower.",
        )
        note.setObjectName("hint")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.record_button = QPushButton("Start PRIVATE recording...")
        self.record_button.clicked.connect(self.start_recording)
        layout.addWidget(self.record_button)
        self.job_progress = QProgressBar()
        self.job_progress.setRange(0, 0)
        self.job_progress.setTextVisible(False)
        self.job_progress.hide()
        layout.addWidget(self.job_progress)

    @staticmethod
    def _int_spin(low: int, high: int, value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(low, high)
        widget.setValue(value)
        return widget

    @staticmethod
    def _float_spin(low: float, high: float, value: float) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(low, high)
        widget.setDecimals(1)
        widget.setValue(value)
        return widget

    def _build_guide_page(self, layout: QVBoxLayout) -> None:
        title = QLabel("From first launch to your first call")
        title.setObjectName("sectionIntro")
        title.setWordWrap(True)
        layout.addWidget(title)
        for index, (heading, _, _) in enumerate(LESSONS):
            button = QPushButton(heading)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.clicked.connect(lambda checked=False, step=index: self.show_tutorial(step))
            layout.addWidget(button)

    def collected_values(self) -> dict[str, SettingValue]:
        return {name: control.value() for name, control in self.controls.items()}

    def _refresh_settings(self) -> None:
        try:
            values = self.collected_values()
            args = settings.namespace(values)
        except ValueError as error:
            self.error_label.setText("Not applied: " + redact(str(error)))
            self.error_label.show()
            return
        self.values = values
        self._sync_diagnostics()
        self._sync_resolution()
        clean_available = self._mode == 0 and self._renders(args) and not args.headless
        self.clean_output_action.setEnabled(clean_available)
        self.show_output.setEnabled(clean_available)
        self.clean_output_action.setToolTip(
            "Stop and disable Suppress preview to use local output windows."
            if args.headless else
            "Enable cardboard rendering; unmasked/raw modes cannot populate clean output."
            if not self._renders(args) else
            "Show or reopen the controls-free window for OBS Window Capture. "
            "Closing it does not stop the session. No raw/debug pixels are included.",
        )
        if not clean_available:
            self.output_window.hide()
            self.output_window.canvas.set_frame(None)
        pair = (str(values["source"]), str(values["backend"]))
        if self._source_mode == 0 and pair != self._native_pair_shown:
            self._populate_native_cameras()
        self.error_label.hide()
        self.command.setPlainText(
            self._video_command() if self._mode == 1 else settings.command_preview(values),
        )
        if self.bridge is not None:
            self.bridge.set_tuning(live_tuning(args))
        for label in self._model_status.values():
            label.setText("Path configured / verify to check")
        if self.worker is None and self.job is None:
            self.preview_note.setText(
                "VIDEO / ORIGINAL SIZE / NO CAMERA"
                if self._mode == 1 else "RAW local preview selected"
                if args.debug_face_preview or not self._renders(args)
                else "No input / nothing is being published",
            )

    @staticmethod
    def _renders(args: argparse.Namespace) -> bool:
        return any(
            (
                args.render_cardboard,
                args.physics,
                args.full_body,
                args.body_head_fallback,
                args.hood_marker_tracking,
                args.virtual_camera,
            )
        )

    def _use_environment(self) -> None:
        value = os.environ.get("KARDBOARD_CAMERA_URL")
        if not value:
            self._show_error(
                "KARDBOARD_CAMERA_URL is not set in this process. Enter a source here, "
                "or set it in the same terminal before launching the studio.",
            )
            return
        self.controls["source"].set_value(value)
        self._sync_source_mode()
        self._refresh_settings()

    def _confirm(self, title: str, message: str) -> bool:
        return (
            QMessageBox.warning(
                self,
                title,
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def start_camera(self) -> None:
        if self._mode == 1:
            self.start_video()
        else:
            self._start_session(demo=False)

    def start_demo(self) -> None:
        self._start_session(demo=True)

    def _start_session(self, *, demo: bool) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop the current session/job before starting another.")
            return
        try:
            values = self.collected_values()
            args = settings.namespace(values)
            if not demo and (args.debug_face_preview or not self._renders(args)):
                if not self._confirm(
                    "Unmasked local camera pixels",
                    "This configuration can display your real face locally. Raw previews are not "
                    "sent to virtual output, but screen capture can still see them. Continue?",
                ):
                    return
            self.bridge = RuntimeBridge(live_tuning(args), source=str(args.source))
            self.worker = SessionWorker(values, self.bridge, demo=demo)
            self.worker.completed.connect(self._remember_result)
            self.worker.finished.connect(self._worker_finished)
            self._exit_code = 0
            self._last_packet_at = 0
            self._set_busy(True)
            self.status.setText(
                "STARTING SYNTHETIC DEMO" if demo else "STARTING / INITIALIZING MODELS"
            )
            if self._exit_code:
                self.error_label.setText(
                    "Session failed. The console has the model, camera, or output error.",
                )
                self.error_label.show()
            self.error_label.hide()
            self._append_log(
                "[STUDIO] Starting synthetic demo."
                if demo
                else "[STUDIO] Starting camera pipeline. Source is hidden."
            )
            self.worker.start()
            if self.show_output.isChecked() and not args.headless and self._renders(args):
                self.output_window.canvas.set_frame(None)
                self.output_window.show()
            else:
                self.output_window.hide()
        except (ValueError, OSError) as error:
            self._show_error(str(error))

    def _remember_result(self, code: int) -> None:
        self._exit_code = code

    def stop(self) -> None:
        if self.worker is not None and self.bridge is not None:
            self.bridge.stop_event.set()
            self.status.setText("STOPPING / WAITING FOR OWNED RESOURCES")
            self.stop_button.setEnabled(False)
        elif self.job is not None:
            if self._job_stop is not None:
                try:
                    self._job_stop.touch()
                except OSError as error:
                    self._show_error(f"Could not request recording stop: {error}")
                    return
            else:
                self.job.terminate()
            self.status.setText("STOPPING JOB / WAITING FOR CLEANUP")
            self.stop_button.setEnabled(False)

    def _worker_finished(self) -> None:
        self._poll_runtime()
        worker, self.worker = self.worker, None
        export_result = worker.export_result if isinstance(worker, VideoExportWorker) else None
        self.bridge = None
        was_video = self._processing_video
        self._processing_video = False
        if worker is not None:
            worker.deleteLater()
        self._set_busy(False)
        self._clear_signals()
        self.status.setText(
            ("VIDEO SAVED / SEE LOGS" if self._exit_code == 0 else
             "VIDEO CANCELLED / NO OUTPUT CREATED" if self._exit_code == 130 else
             "VIDEO EXPORT FAILED / SEE LOGS")
            if was_video else
            "STOPPED / NO CAMERA CONNECTED"
            if self._exit_code == 0
            else "SESSION FAILED / SEE CONSOLE",
        )
        if self._calibration is not None:
            self._calibration.reject()
        self._append_log(f"[STUDIO] Session ended with exit code {self._exit_code}.")
        if was_video and self._exit_code == 0 and export_result is not None:
            path = export_result.path.resolve()
            if QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                self._append_log(f"[VIDEO] Opened in the default media player: {path}")
            else:
                self._show_error(
                    "The video was saved, but the default media player could not be opened. "
                    f"Open the saved file manually: {path}",
                )
        if self._closing:
            QTimer.singleShot(0, self.close)

    def _set_busy(self, busy: bool) -> None:
        self.start_button.setEnabled(not busy)
        self.demo_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        self.load_action.setEnabled(not busy)
        self.reset_action.setEnabled(not busy)
        self.record_button.setEnabled(not busy and self._mode == 0)
        self.record_group.setEnabled(not busy and self._mode == 0)
        self.source_environment_button.setEnabled(not busy and self._mode == 0)
        self.input_type.setEnabled(not busy and self._mode == 0)
        self.native_panel.setEnabled(not busy and self._mode == 0)
        self.model_force.setEnabled(not busy)
        for button in self._model_buttons.values():
            button.setEnabled(not busy)
        self.work_mode.setEnabled(not busy)
        self.video_setup.setEnabled(not busy and self._mode == 1)
        for control in self.video_setup.findChildren(QWidget):
            if isinstance(control, (QLineEdit, QComboBox, QCheckBox, QPushButton)):
                control.setEnabled(not busy)
        self.output_resolution.setEnabled(not busy and self._mode == 0)
        self.calibrate_button.setEnabled(
            not self._processing_video and self._mode == 0
            and self.worker is not None and not self.worker.demo,
        )
        self.live_hint.setText(
            "EXPORT LOCKED / Stop cancels processing."
            if busy and self._processing_video else
            "SETUP LOCKED / Live tuning remains available."
            if busy else
            "VIDEO / Original size and timing."
            if self._mode == 1 else
            "Ready / Settings are editable.",
        )
        self.live_hint.setObjectName("sessionHint")
        self.live_hint.setProperty("busy", busy)
        self.live_hint.style().unpolish(self.live_hint)
        self.live_hint.style().polish(self.live_hint)
        live_only = {
            "source", "backend", "width", "height", "fps", "rotate", "mirror", "duration",
            "headless", "preview_height", "virtual_camera", "virtual_camera_width",
            "virtual_camera_height", "virtual_camera_fps", "full_body", "body_head_fallback",
            "hood_marker_tracking", "pose_tracking_width", "tracking_debug", "debug_face_preview",
        }
        for name, control in self.controls.items():
            mode_locked = self._mode == 1 and name in live_only
            editable = (
                not busy or self.worker is not None and not self._processing_video
                and name in LIVE_FIELDS
            )
            control.set_locked(mode_locked or not editable)
            if mode_locked:
                control.state_badge.setText("LIVE ONLY")

    def _clear_signals(self) -> None:
        self._set_preview_hint()
        self.preview.set_frame(None)
        self.skeleton.set_frame(None)
        self.raw_face.set_frame(None)
        self.face_mesh.set_frame(None)
        self.diagnostics_notice.hide()
        self.output_window.canvas.set_frame(None)
        for label in self.metrics.values():
            label.setText("--")
        for meter in self.eye_meters.values():
            meter.setValue(0)
        for label in self.eye_labels.values():
            label.setText("raw -- / filtered --")
        for eye, letter in (("left", "K"), ("right", "C")):
            self.eye_states[eye].setText(f"Your {eye.upper()} / {letter}: --")
        self.pose_label.setText("Yaw --   Pitch --   Roll --   /   Action --")
        self.session_summary.setText("No input / not publishing")
        self.preview_note.setText(
            "VIDEO / ORIGINAL SIZE / NO CAMERA"
            if self._mode == 1 else "No input / nothing is being published",
        )

    def _poll_runtime(self) -> None:
        if self.bridge is None:
            return
        packet, logs = self.bridge.take()
        for line in logs:
            self._append_log(line)
        if packet is not None:
            self._last_packet_at = time.monotonic()
            self.preview.set_frame(packet.frame)
            self.skeleton.set_frame(packet.skeleton)
            self.raw_face.set_frame(packet.raw_face)
            self.face_mesh.set_frame(packet.face_mesh)
            raw = packet.raw_face is not None or packet.telemetry.raw_preview
            diagnostics = raw or packet.face_mesh is not None or packet.skeleton is not None
            self.diagnostics_notice.setText(
                "RAW diagnostics / local only"
                if raw else "Diagnostics / local only",
            )
            self.diagnostics_notice.setVisible(diagnostics)
            if packet.clean_frame is not None:
                self.output_window.canvas.set_frame(packet.clean_frame)
            self._display_telemetry(packet.telemetry, packet.frame is None)
        elif (
            self._last_packet_at
            and time.monotonic() - self._last_packet_at > 1
            and not self.bridge.stop_event.is_set()
        ):
            self.status.setText(
                "VIDEO PROCESSING / WAITING FOR THE NEXT COMPLETED FRAME"
                if self._processing_video else
                "SYNTHETIC DEMO / WAITING FOR THE NEXT FRAME"
                if self.worker is not None and self.worker.demo else
                "WAITING FOR CAMERA / RETAINING LAST DISPLAYED FRAME",
            )

    def _display_telemetry(self, state: RuntimeTelemetry, headless: bool) -> None:
        stopping = self.bridge is not None and self.bridge.stop_event.is_set()
        if not stopping:
            self.status.setText(
                "VIDEO PROCESSING / EVERY FRAME, ORIGINAL DIMENSIONS"
                if self._processing_video else state.calibration_status
                if state.calibration_status else "SYNTHETIC DEMO / NO CAMERA INPUT"
                if state.demo
                else "RAW CAMERA MODE / UNMASKED LOCAL PREVIEW"
                if not state.masking_enabled
                else "LIVE / TRACKING"
                if state.effective_detected
                else "FACE NOT ACQUIRED / BLACK OR LAST SAFE COMPOSITE",
            )
        self.preview_note.setText(
            "Preview suppressed / processing continues"
            if headless
            else "RAW FACE DEBUG ENABLED / LOCAL ONLY"
            if state.raw_preview and not state.demo
            else f"{state.frame_size[0]} x {state.frame_size[1]} / "
            + ("processing video" if self._processing_video else
               "synthetic stage" if state.demo else "local preview"),
        )
        self._set_preview_hint(suppressed=headless)
        self.metrics["camera"].setText("-- / demo" if state.demo else f"{state.camera_fps:.1f}")
        self.metrics["tracking"].setText("-- / demo" if state.demo else f"{state.tracking_fps:.1f}")
        self.metrics["age"].setText("-- / demo" if state.demo else f"{state.frame_age_ms:.1f} ms")
        self.metrics["output"].setText(
            "Video file export" if self._processing_video else
            "OBS camera" if state.output_device else
            "Clean window" if self.output_window.isVisible() else "Not publishing",
        )
        summary = (
            "Synthetic demo / " if state.demo else
            f"Capture {state.camera_fps:.1f} fps / Tracking {state.tracking_fps:.1f} fps / "
        )
        self.session_summary.setText(summary + self.metrics["output"].text())
        eyes = self.bridge.tuning().eyes if self.bridge is not None else live_tuning(
            settings.namespace(self.values),
        ).eyes
        visual = state.render_face or state.raw_face
        for name in ("left", "right"):
            filtered = getattr(state.face, name + "_eye_open")
            raw = getattr(state.raw_face, name + "_eye_open")
            self.eye_meters[name].setValue(round(raw * 1000) if state.face.detected else 0)
            displayed = getattr(visual, name + "_eye_open")
            other = visual.right_eye_open if name == "left" else visual.left_eye_open
            threshold = eyes.left_closed if name == "left" else eyes.right_closed
            closed = eyes.closed(displayed, other, left_eye=name == "left")
            decision = ("CLOSED" if closed else "OPEN") if state.face.detected else "--"
            self.eye_states[name].setText(
                f"Your {name.upper()} / {'K' if name == 'left' else 'C'}: {decision}",
            )
            self.eye_labels[name].setText(
                f"{'CLOSED' if closed else 'OPEN'} / raw {raw:.2f} / "
                f"render {displayed:.2f} / blink <= {threshold:.2f} / filtered {filtered:.2f}"
                if state.face.detected
                else "raw -- / filtered --",
            )
        if self._calibration is not None and self._calibration.isVisible():
            self._calibration.observe(state.raw_face)
        pose = state.face.head_pose
        self.pose_label.setText(
            f"Yaw {pose.yaw_degrees:+.1f}   Pitch {pose.pitch_degrees:+.1f}   "
            f"Roll {pose.roll_degrees:+.1f}   /   Action {state.action or '--'}",
        )

    def _append_log(self, message: str) -> None:
        source = self.controls["source"].value()
        assert isinstance(source, str)
        self.console.appendPlainText(redact(message, source=source))

    def _show_error(self, message: str) -> None:
        safe = redact(message)
        self.error_label.setText(safe)
        self.error_label.show()
        self._append_log("[ERROR] " + safe)

    def reset_settings(self) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop before resetting settings.")
            return
        values = settings.defaults()
        values["source"] = self.controls["source"].value()
        self._apply_values(values)

    def _apply_values(self, values: dict[str, SettingValue]) -> None:
        for name, control in self.controls.items():
            control.set_value(values[name])
        self._sync_source_mode()
        self._refresh_settings()

    def _save_preset_dialog(self) -> None:
        folder = data_root() / "presets"
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self._show_error(f"Cannot create the preset folder: {error}")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save source-free preset",
            str(folder / "KardboardCode-studio.json"),
            "Studio preset (*.json)",
        )
        if filename:
            self.save_preset(Path(filename))

    def save_preset(self, path: Path) -> None:
        try:
            settings.save_preset(path, self.collected_values())
            self._append_log(f"[PRESET] Saved without source or raw-preview consent: {path}")
        except (ValueError, OSError) as error:
            self._show_error(str(error))

    def _load_preset_dialog(self) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop before loading a preset.")
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Load source-free preset", "", "*.json")
        if filename:
            self.load_preset(Path(filename))

    def load_preset(self, path: Path) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop before loading a preset.")
            return
        try:
            self._apply_values(settings.load_preset(path, self.collected_values()))
            self._append_log(
                f"[PRESET] Loaded. Source unchanged; raw-preview consent reset: {path}"
            )
        except (ValueError, OSError) as error:
            self._show_error(str(error))

    def show_tutorial(self, step: int = 0) -> None:
        if self._tutorial is None:
            self._tutorial = TutorialDialog(self)
            self._tutorial.navigate.connect(self._navigate)
        self._tutorial.selector.setCurrentIndex(step)
        self._style_titlebar(self._tutorial)
        self._tutorial.show()
        self._tutorial.raise_()

    def _navigate(self, name: str) -> None:
        if name == "Video":
            self.work_mode.setCurrentIndex(1)
            return
        if name in {"Private capture", "Recording"}:
            self.work_mode.setCurrentIndex(0)
        self.page_selector.setCurrentText("Private capture" if name == "Recording" else name)

    def _choose_record_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Private recording output folder")
        if directory:
            self.record_folder.setText(directory)

    def start_recording(self) -> None:
        if self._mode != 0:
            self._show_error(
                "Private camera capture is a Live-mode utility, not video processing.",
            )
            return
        if self.worker is not None or self.job is not None:
            self._show_error("Stop the camera/demo/job before recording.")
            return
        try:
            values = self.collected_values()
            settings.namespace(values)
            options = RecordingOptions(
                full_body=self.record_full_body.isChecked(),
                free_recording=self.record_free.isChecked(),
                duration=self.record_duration.value(),
                pose_tracking_width=self.record_pose_width.value(),
                pose_tracking_fps=self.record_pose_fps.value(),
                output_dir=self.record_folder.text(),
                name=self.record_name.text(),
                countdown=self.record_countdown.value(),
                preview_height=self.record_preview_height.value(),
            )
            if not self._confirm(
                "Private RAW recording",
                "This records unmasked camera pixels and tracking telemetry to disk and opens a "
                "raw preview. It is not a recording of the safe cardboard output. Continue?",
            ):
                return
            self._job_temp = tempfile.TemporaryDirectory(prefix="kardboard-studio-")
            self._job_stop = Path(self._job_temp.name) / "stop"
            argv = options.arguments(values, self._job_stop)
            self._start_job("recording", scripts_root() / "record_guided_regression.py", argv)
        except (ValueError, OSError) as error:
            self._clean_job_files()
            self._show_error(str(error))

    def download_model(self, name: str) -> None:
        if self.worker is not None or self.job is not None:
            self._show_error("Stop the camera/demo/job before verifying or downloading a model.")
            return
        try:
            value = self.controls[name].value()
            if not isinstance(value, str) or not value:
                raise ValueError("Choose a model destination first.")
            if "://" in value:
                raise ValueError("Choose a local model destination, not a URL.")
            path = Path(value).expanduser()
            if not path.is_absolute():
                path = data_root() / path
            temporary = path.with_suffix(path.suffix + ".download")
            if temporary.exists():
                raise ValueError(
                    f"A partial or active download already exists at {temporary}. "
                    "Check it before starting another.",
                )
            self._download_temp = temporary
            self._start_job(
                "model",
                scripts_root() / MODEL_SCRIPTS[name],
                ["--destination", str(path)]
                + (["--force"] if self.model_force.isChecked() else []),
            )
        except (ValueError, OSError) as error:
            self._clean_job_files()
            self._show_error(str(error))

    def _start_job(self, kind: str, script: Path, argv: list[str]) -> None:
        if not script.is_file():
            raise ValueError(
                "The required application helper is missing: " + str(script)
            )
        working = data_root()
        working.mkdir(parents=True, exist_ok=True)
        self._job_kind = kind
        self._job_error = False
        self._pending_output = ""
        self._camera_output = ""
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.job = QProcess(self)
        self.job.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.job.setWorkingDirectory(str(working))
        self.job.readyReadStandardOutput.connect(self._read_job_output)
        self.job.finished.connect(self._job_finished)
        self.job.errorOccurred.connect(self._job_failed)
        self._set_busy(True)
        self.job_progress.show()
        self.status.setText(
            "PRIVATE RAW RECORDING"
            if kind == "recording"
            else "LISTING LOCAL CAMERAS / METADATA ONLY"
            if kind == "cameras"
            else "MODEL VERIFICATION / DOWNLOAD"
        )
        self._append_log("[JOB] Starting " + kind + ". Source and command credentials are hidden.")
        self.job.start(sys.executable, ["-u", str(script), *argv])

    def _read_job_output(self) -> None:
        if self.job is None:
            return
        text = self._decoder.decode(bytes(self.job.readAllStandardOutput()))
        if self._job_kind == "cameras":
            self._camera_output += text
            if len(self._camera_output) > 128_000:
                self._job_error = True
                self._show_error("Camera inventory output exceeded its size limit.")
                self.job.kill()
            return
        self._pending_output += text
        lines = self._pending_output.split("\n")
        self._pending_output = lines.pop()
        for line in lines:
            self._append_log(line.rstrip("\r"))
        if len(self._pending_output) > 64_000:
            self._pending_output = ""
            self._append_log("[JOB] Oversized unterminated log line discarded.")

    def _job_failed(self, error: QProcess.ProcessError) -> None:
        if self.job is None:
            return
        self._job_error = True
        self._show_error("Job process error: " + self.job.errorString())
        if error == QProcess.ProcessError.FailedToStart:
            self._job_finished(1)

    def _job_finished(self, code: int, status: object = None) -> None:
        if self.job is None:
            return
        self._read_job_output()
        tail = self._decoder.decode(b"", final=True)
        if self._job_kind == "cameras":
            self._camera_output += tail
            self._accept_camera_inventory(code)
        else:
            self._pending_output += tail
        if self._pending_output:
            self._append_log(self._pending_output)
        self._pending_output = ""
        process, self.job = self.job, None
        process.deleteLater()
        try:
            self._clean_job_files()
        except OSError as error:
            self._job_error = True
            self._show_error(f"Job ended, but temporary-file cleanup failed: {error}")
        self._set_busy(False)
        self.job_progress.hide()
        self.status.setText(
            "JOB FINISHED / NO CAMERA CONNECTED"
            if code == 0 and not self._job_error
            else "JOB ENDED / SEE CONSOLE FOR RESULT",
        )
        self._append_log(f"[JOB] {self._job_kind} ended with exit code {code}.")
        self._refresh_settings()
        if self._closing:
            QTimer.singleShot(0, self.close)

    def _accept_camera_inventory(self, code: int) -> None:
        if code != 0 or self._job_error:
            self._job_error = True
            self.native_hint.setText(
                "Refresh failed. Any previous list may be stale; see the console."
            )
            self._show_error("Camera discovery failed: " + self._camera_output.strip())
            return
        try:
            devices = decode_camera_inventory(self._camera_output)
        except ValueError as error:
            self._job_error = True
            self.native_hint.setText("Invalid camera list. Retry Refresh or use a manual source.")
            self._show_error(f"Could not read the camera list: {error}")
            return
        previous = self.native_camera.currentData()
        if (
            self._source_mode == 0
            and isinstance(previous, LocalCameraDevice)
            and previous not in devices
        ):
            self.controls["source"].set_value("")
        self._native_devices = devices
        self._populate_native_cameras()
        self.native_hint.setText(
            f"{len(devices)} capture routes / names can repeat across Windows APIs. "
            "Start opens the selected route."
            if devices
            else "No camera entries were returned. Check connections/Windows permissions, refresh, "
            "or use a manual device index in the custom source field."
        )
        self._append_log(
            f"[CAMERAS] Listed {len(devices)} backend/device entries; "
            "no capture streams were opened.",
        )

    def _clean_job_files(self) -> None:
        if self._job_temp is not None:
            self._job_temp.cleanup()
            self._job_temp = None
        self._job_stop = None
        if self._download_temp is not None:
            self._download_temp.unlink(missing_ok=True)
            self._download_temp = None

    def toggle_theme(self) -> None:
        self._dark = not self._dark
        self._apply_theme()

    def _apply_theme(self) -> None:
        from kardboard_vtuber.gui.theme import stylesheet

        self.setStyleSheet(stylesheet(self._dark))
        self.theme_button.setIcon(_theme_icon(self._dark))
        self.theme_button.setIconSize(QSize(38, 20))
        self.theme_button.setText("Light" if self._dark else "Dark")
        for window in (self, self.output_window, self._tutorial, self._calibration):
            if window is not None:
                self._style_titlebar(window)

    def _style_titlebar(self, window: QWidget) -> None:
        from kardboard_vtuber.gui.theme import titlebar

        warning = titlebar(window, self._dark)
        if warning:
            self._append_log("[WARNING] " + warning)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker is not None or self.job is not None:
            event.ignore()
            self._closing = True
            self.stop()
            return
        self.timer.stop()
        self.output_window.allow_close = True
        self.output_window.close()
        event.accept()


def _theme_icon(dark: bool) -> QIcon:
    pixmap = QPixmap(40, 20)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#e9bc63" if dark else "#b07214"), 1.5))
    painter.drawEllipse(6, 6, 8, 8)
    for x1, y1, x2, y2 in (
        (10, 1, 10, 3),
        (10, 17, 10, 19),
        (1, 10, 3, 10),
        (17, 10, 19, 10),
        (3, 3, 5, 5),
        (15, 15, 17, 17),
        (3, 17, 5, 15),
        (15, 5, 17, 3),
    ):
        painter.drawLine(x1, y1, x2, y2)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#b2bfdf" if dark else "#5364a1"))
    painter.drawEllipse(25, 3, 13, 14)
    painter.setBrush(QColor("#19332b" if dark else "#fff4db"))
    painter.drawEllipse(30, 0, 13, 14)
    painter.end()
    return QIcon(pixmap)
