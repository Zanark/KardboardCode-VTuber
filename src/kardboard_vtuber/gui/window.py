"""KardboardCode Studio: native controls around the shared camera runtime."""

from __future__ import annotations

import argparse
import codecs
import os
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QProcess, QSize, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
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
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from kardboard_vtuber.camera.devices import LocalCameraDevice, decode_camera_inventory
from kardboard_vtuber.cli import live_tuning
from kardboard_vtuber.gui import settings
from kardboard_vtuber.gui.settings import (
    LIVE_FIELDS,
    MODEL_SCRIPTS,
    PAGES,
    ROOT,
    RecordingOptions,
    SettingValue,
)
from kardboard_vtuber.gui.tutorial import LESSONS, TutorialDialog
from kardboard_vtuber.gui.widgets import OptionControl, VideoCanvas
from kardboard_vtuber.gui.worker import SessionWorker
from kardboard_vtuber.runtime import RuntimeBridge, RuntimeTelemetry, redact

ICON_PATH = Path(__file__).parent / "assets" / "kardboardcode-icon.ico"


class StudioWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KardboardCode Studio")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1500, 980)
        self.setMinimumSize(1080, 720)
        self.values = settings.defaults()
        self.controls: dict[str, OptionControl] = {}
        self.worker: SessionWorker | None = None
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
        self._tutorial: TutorialDialog | None = None
        self._model_status: dict[str, QLabel] = {}
        self._build_ui()
        self._sync_source_mode()
        self._apply_theme()
        self._refresh_settings()
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._poll_runtime)
        self.timer.start()
        self._append_log("[STUDIO] Ready. No camera or output is open. Try demo or open Tutorial.")

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 16, 22, 12)
        root.setSpacing(14)
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(self.windowIcon().pixmap(54, 54))
        header.addWidget(logo)
        identity = QVBoxLayout()
        title = QLabel("KARDBOARD / STUDIO")
        title.setObjectName("appTitle")
        identity.addWidget(title)
        subtitle = QLabel("YOUR CAMERA. YOUR CARDBOARD. YOUR CONTROLS.")
        subtitle.setObjectName("eyebrow")
        identity.addWidget(subtitle)
        header.addLayout(identity)
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
            button.setMinimumHeight(36)
            header.addWidget(button)
        root.addLayout(header)

        self.status = QLabel("IDLE / NO CAMERA CONNECTED")
        self.status.setObjectName("status")
        root.addWidget(self.status)
        self.error_label = QLabel()
        self.error_label.setTextFormat(Qt.TextFormat.PlainText)
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        root.addWidget(self.error_label)
        split = QSplitter(Qt.Orientation.Horizontal)
        controls_panel = QFrame()
        controls_panel.setObjectName("panel")
        panel_layout = QVBoxLayout(controls_panel)
        panel_layout.setContentsMargins(16, 14, 16, 12)
        top = QHBoxLayout()
        top.addWidget(QLabel("CONTROL ROOM"), 1)
        save = QPushButton("Save preset")
        save.clicked.connect(self._save_preset_dialog)
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self._load_preset_dialog)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        for button in (save, self.load_button, self.reset_button):
            top.addWidget(button)
        panel_layout.addLayout(top)
        self.page_selector = QComboBox()
        self.page_selector.setAccessibleName("Settings page")
        self.page_names = [
            "Camera",
            "Avatar & eyes",
            "Output & effects",
            "Tracking labs",
            "Recording",
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
        actions = settings.parser_actions()
        for name in self.page_names:
            page = QWidget()
            content = QVBoxLayout(page)
            content.setContentsMargins(0, 8, 8, 8)
            content.setSpacing(10)
            if name in PAGES:
                self._build_control_page(name, content, actions)
            elif name == "Recording":
                self._build_recording_page(content)
            else:
                self._build_guide_page(content)
            content.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
        self.page_selector.currentIndexChanged.connect(self.pages.setCurrentIndex)
        panel_layout.addWidget(self.pages, 1)
        split.addWidget(controls_panel)
        split.addWidget(self._build_workspace())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([420, 1000])
        controls_panel.setMinimumWidth(360)
        root.addWidget(split, 1)
        footer = QLabel(
            "LOCAL-FIRST  /  source-free presets  /  clean virtual output  /  "
            "no automatic camera connection",
        )
        footer.setObjectName("hint")
        root.addWidget(footer)
        self.setCentralWidget(central)
        self._build_console()
        self._build_menu()

    def _build_control_page(
        self,
        name: str,
        layout: QVBoxLayout,
        actions: dict[str, argparse.Action],
    ) -> None:
        descriptions = {
            "Camera": "Connect a local camera, phone stream, or recorded file.",
            "Avatar & eyes": (
                "Calibrate anatomical eyes. Lower closure thresholds are less sensitive."
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
        fields = PAGES[name]
        if name == "Avatar & eyes":
            fields = tuple(field for field in fields if field.name in LIVE_FIELDS) + tuple(
                field for field in fields if field.name not in LIVE_FIELDS
            )
        for field in fields:
            if field.name == "source":
                self._build_source_selector(layout)
            control = OptionControl(field, actions[field.name], self.values[field.name])
            self.controls[field.name] = control
            control.changed.connect(self._refresh_settings)
            layout.addWidget(control)
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
                download.clicked.connect(
                    lambda checked=False, model=field.name: self.download_model(model),
                )
                row.addWidget(download)
                layout.addLayout(row)

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
        row.addWidget(self.native_camera, 1)
        self.refresh_cameras_button = QPushButton("Refresh")
        self.refresh_cameras_button.clicked.connect(self.refresh_native_cameras)
        row.addWidget(self.refresh_cameras_button)
        native_layout.addLayout(row)
        self.native_hint = QLabel(
            "Refresh lists camera names without opening them. Choose your laptop/USB camera, "
            "then Start camera. Virtual cameras can also appear.",
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
            self.native_camera.addItem(f"Device index {source} / {backend} (manual)", None)
        else:
            self.native_camera.addItem("Select a local camera", None)
        selected = 0
        for device in self._native_devices:
            self.native_camera.addItem(device.label, device)
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
            self._start_job("cameras", ROOT / "scripts" / "list_local_cameras.py", [])
        except (ValueError, OSError) as error:
            self._show_error(str(error))

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(12)
        top = QHBoxLayout()
        heading = QLabel("PROGRAM / LOCAL PREVIEW")
        heading.setObjectName("eyebrow")
        top.addWidget(heading, 1)
        self.preview_note = QLabel("No input / nothing is being published")
        self.preview_note.setObjectName("hint")
        top.addWidget(self.preview_note)
        layout.addLayout(top)
        self.preview = VideoCanvas(
            "Your stage is ready.\n\nStart camera when you are ready, or Try demo "
            "to explore with synthetic imagery.\n\nNo camera starts automatically.",
        )
        self.skeleton = VideoCanvas(
            "Enable the separate skeleton diagnostic in Tracking labs.\n"
            "The skeleton is not composited onto your camera output.",
        )
        self.command = QPlainTextEdit()
        self.command.setReadOnly(True)
        self.command.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.preview, "Preview")
        self.tabs.addTab(self.skeleton, "Skeleton")
        self.tabs.addTab(self.command, "CLI equivalent (credentials excluded)")
        layout.addWidget(self.tabs, 1)
        self.metrics: dict[str, QLabel] = {}
        metrics_row = QHBoxLayout()
        for name, title in (
            ("camera", "CAMERA FPS"),
            ("tracking", "TRACKING FPS"),
            ("age", "INTERNAL FRAME AGE"),
            ("output", "VIDEO OUTPUT"),
        ):
            card = QFrame()
            card.setObjectName("metric")
            card_layout = QVBoxLayout(card)
            caption = QLabel(title)
            caption.setObjectName("eyebrow")
            value = QLabel("--")
            value.setObjectName("metricValue")
            self.metrics[name] = value
            card_layout.addWidget(caption)
            card_layout.addWidget(value)
            metrics_row.addWidget(card, 1)
        layout.addLayout(metrics_row)
        eyes = QGroupBox("LIVE SIGNALS / ANATOMICAL EYES")
        signals = QGridLayout(eyes)
        self.eye_meters: dict[str, QProgressBar] = {}
        self.eye_labels: dict[str, QLabel] = {}
        for row, (name, title) in enumerate(
            (("left", "Your LEFT / K"), ("right", "Your RIGHT / C"))
        ):
            signals.addWidget(QLabel(title), row, 0)
            meter = QProgressBar()
            meter.setRange(0, 1000)
            meter.setTextVisible(False)
            meter.setFixedHeight(10)
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
        layout.addWidget(eyes)
        return workspace

    def _build_console(self) -> None:
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(1500)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setObjectName("console")
        dock = QDockWidget("SESSION CONSOLE / redacted, bounded, selectable", self)
        dock.setObjectName("consoleDock")
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(6, 2, 6, 4)
        toolbar = QHBoxLayout()
        hint = QLabel(
            "CLI diagnostics remain available here. Native library messages may also use stderr."
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
        dock.setWidget(body)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.resizeDocks([dock], [155], Qt.Orientation.Vertical)
        self.console_dock = dock

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("File")
        for label, slot in (
            ("Save source-free preset...", self._save_preset_dialog),
            ("Load preset...", self._load_preset_dialog),
            ("Reset settings", self.reset_settings),
            ("Exit", self.close),
        ):
            action = QAction(label, self)
            action.triggered.connect(slot)
            menu.addAction(action)
        view = self.menuBar().addMenu("View")
        view.addAction(self.console_dock.toggleViewAction())
        theme = QAction("Toggle dark / light", self)
        theme.triggered.connect(self.toggle_theme)
        view.addAction(theme)
        help_menu = self.menuBar().addMenu("Help")
        guide = QAction("Studio tutorial", self)
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
        self.record_folder = QLineEdit(str(ROOT / "recordings"))
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
        pair = (str(values["source"]), str(values["backend"]))
        if self._source_mode == 0 and pair != self._native_pair_shown:
            self._populate_native_cameras()
        self.error_label.hide()
        self.command.setPlainText(settings.command_preview(values))
        if self.bridge is not None:
            self.bridge.set_tuning(live_tuning(args))
        for label in self._model_status.values():
            label.setText("Path configured / verify to check")
        if self.worker is None and self.job is None:
            self.preview_note.setText(
                "RAW local preview selected"
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
        self.bridge = None
        if worker is not None:
            worker.deleteLater()
        self._set_busy(False)
        self._clear_signals()
        self.status.setText(
            "STOPPED / NO CAMERA CONNECTED"
            if self._exit_code == 0
            else "SESSION FAILED / SEE CONSOLE",
        )
        self._append_log(f"[STUDIO] Session ended with exit code {self._exit_code}.")
        if self._closing:
            QTimer.singleShot(0, self.close)

    def _set_busy(self, busy: bool) -> None:
        self.start_button.setEnabled(not busy)
        self.demo_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        self.load_button.setEnabled(not busy)
        self.reset_button.setEnabled(not busy)
        self.record_button.setEnabled(not busy)
        self.record_group.setEnabled(not busy)
        self.source_environment_button.setEnabled(not busy)
        self.input_type.setEnabled(not busy)
        self.native_panel.setEnabled(not busy)
        self.model_force.setEnabled(not busy)
        for name, control in self.controls.items():
            control.setEnabled(not busy or self.worker is not None and name in LIVE_FIELDS)

    def _clear_signals(self) -> None:
        self.preview.set_frame(None)
        self.skeleton.set_frame(None)
        for label in self.metrics.values():
            label.setText("--")
        for meter in self.eye_meters.values():
            meter.setValue(0)
        for label in self.eye_labels.values():
            label.setText("raw -- / filtered --")
        self.pose_label.setText("Yaw --   Pitch --   Roll --   /   Action --")
        self.preview_note.setText("No input / nothing is being published")

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
            self._display_telemetry(packet.telemetry, packet.frame is None)
        elif (
            self._last_packet_at
            and time.monotonic() - self._last_packet_at > 1
            and not self.bridge.stop_event.is_set()
        ):
            self.status.setText("WAITING FOR CAMERA / RETAINING LAST DISPLAYED FRAME")

    def _display_telemetry(self, state: RuntimeTelemetry, headless: bool) -> None:
        stopping = self.bridge is not None and self.bridge.stop_event.is_set()
        if not stopping:
            self.status.setText(
                "SYNTHETIC DEMO / NO CAMERA INPUT"
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
            + ("synthetic stage" if state.demo else "local preview"),
        )
        self.metrics["camera"].setText("-- / demo" if state.demo else f"{state.camera_fps:.1f}")
        self.metrics["tracking"].setText("-- / demo" if state.demo else f"{state.tracking_fps:.1f}")
        self.metrics["age"].setText("-- / demo" if state.demo else f"{state.frame_age_ms:.1f} ms")
        self.metrics["output"].setText("OBS camera" if state.output_device else "Not publishing")
        for name in ("left", "right"):
            filtered = getattr(state.face, name + "_eye_open")
            raw = getattr(state.raw_face, name + "_eye_open")
            self.eye_meters[name].setValue(round(filtered * 1000) if state.face.detected else 0)
            self.eye_labels[name].setText(
                f"raw {raw:.2f} / filtered {filtered:.2f}"
                if state.face.detected
                else "raw -- / filtered --",
            )
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
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save source-free preset",
            "KardboardCode-studio.json",
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
        self._tutorial.show()
        self._tutorial.raise_()

    def _navigate(self, name: str) -> None:
        self.page_selector.setCurrentText(name)

    def _choose_record_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Private recording output folder")
        if directory:
            self.record_folder.setText(directory)

    def start_recording(self) -> None:
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
            self._start_job("recording", ROOT / "scripts" / "record_guided_regression.py", argv)
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
                path = ROOT / path
            temporary = path.with_suffix(path.suffix + ".download")
            if temporary.exists():
                raise ValueError(
                    f"A partial or active download already exists at {temporary}. "
                    "Check it before starting another.",
                )
            self._download_temp = temporary
            self._start_job(
                "model",
                ROOT / "scripts" / MODEL_SCRIPTS[name],
                ["--destination", str(path)]
                + (["--force"] if self.model_force.isChecked() else []),
            )
        except (ValueError, OSError) as error:
            self._clean_job_files()
            self._show_error(str(error))

    def _start_job(self, kind: str, script: Path, argv: list[str]) -> None:
        if not script.is_file():
            raise ValueError(
                "This operation needs the source checkout's scripts folder: " + str(script)
            )
        self._job_kind = kind
        self._job_error = False
        self._pending_output = ""
        self._camera_output = ""
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.job = QProcess(self)
        self.job.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.job.setWorkingDirectory(str(ROOT))
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
            "Choose the laptop/USB camera. Each entry includes its capture API; the same "
            "device may appear twice. Refresh after device changes. Start opens the camera."
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
        bg, panel, text, muted, border, field = (
            ("#111a19", "#1a2623", "#e7f2eb", "#94aca3", "#34463e", "#101c18")
            if self._dark
            else ("#edf3ef", "#ffffff", "#19352b", "#506e61", "#c5d6cc", "#f4f8f5")
        )
        self.setStyleSheet(f"""
            QMainWindow, QDialog {{ background:{bg}; color:{text}; }}
            QWidget {{ color:{text}; font-family:'Segoe UI'; font-size:12px; }}
            QFrame#panel, QFrame#metric, QGroupBox {{
                background:{panel}; border:1px solid {border}; border-radius:10px;
            }}
            QGroupBox {{ margin-top:10px; padding:14px 10px 8px; }}
            QGroupBox::title {{ subcontrol-origin:margin; left:12px; padding:0 6px; }}
            QScrollArea, QScrollArea > QWidget > QWidget, QStackedWidget {{ background:{panel}; }}
            QLabel {{ background:transparent; }}
            QLabel#appTitle {{ font-size:23px; font-weight:700; letter-spacing:1px; }}
            QLabel#eyebrow {{ color:{muted}; font-size:10px; font-weight:600; }}
            QLabel#hint {{ color:{muted}; font-size:11px; }}
            QLabel#status {{ background:{panel}; border-left:3px solid #6bdbb0;
                padding:9px 13px; font-weight:600; }}
            QLabel#error, QLabel#warning {{ color:#e7ad70; background:{panel};
                border:1px solid #93683e; border-radius:6px; padding:10px; }}
            QLabel#sectionIntro {{ color:{muted}; padding-bottom:6px; }}
            QLabel#metricValue {{ font-size:18px; font-weight:600; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextBrowser {{
                background:{field}; border:1px solid {border}; border-radius:5px;
                padding:6px; selection-background-color:#376954;
            }}
            QComboBox, QSpinBox, QDoubleSpinBox {{ min-height:20px; }}
            QPushButton {{ background:{panel}; border:1px solid {border}; border-radius:6px;
                padding:7px 10px; font-weight:500; }}
            QPushButton:hover {{ border-color:#6bdbb0; background:{field}; }}
            QPushButton#primary {{ background:#78dcb1; color:#10291e; border-color:#78dcb1; }}
            QPushButton#primary:disabled {{
                background:{panel}; color:{muted}; border-color:{border};
            }}
            QPushButton#stop {{ color:#eea09b; border-color:#995b57; min-width:56px; }}
            QPushButton:disabled, QWidget:disabled {{ color:{muted}; }}
            QCheckBox {{ spacing:8px; }}
            QCheckBox::indicator {{ width:15px; height:15px; }}
            QSlider::groove:horizontal {{ height:5px; background:{border}; border-radius:2px; }}
            QSlider::sub-page:horizontal {{ background:#78dcb1; border-radius:2px; }}
            QSlider::handle:horizontal {{ width:13px; margin:-5px 0; background:#b3f0d4;
                border:1px solid #376954; border-radius:6px; }}
            QProgressBar {{ border:0; border-radius:4px; background:{border}; }}
            QProgressBar::chunk {{ background:#78dcb1; border-radius:4px; }}
            QTabWidget::pane {{ border:1px solid {border}; border-radius:6px; }}
            QTabBar::tab {{ background:{panel}; border:1px solid {border}; padding:7px 12px; }}
            QTabBar::tab:selected {{ border-bottom:2px solid #78dcb1; }}
            QDockWidget {{ color:{muted}; }}
            QPlainTextEdit#console {{ font-family:Consolas; font-size:11px; }}
            QMenuBar, QMenu {{ background:{panel}; color:{text}; }}
        """)
        self.theme_button.setIcon(_theme_icon(self._dark))
        self.theme_button.setIconSize(QSize(38, 20))
        self.theme_button.setText("Light" if self._dark else "Dark")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker is not None or self.job is not None:
            event.ignore()
            self._closing = True
            self.stop()
            return
        self.timer.stop()
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
    painter.setBrush(QColor("#1a2623" if dark else "#ffffff"))
    painter.drawEllipse(30, 0, 13, 14)
    painter.end()
    return QIcon(pixmap)
