from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from kardboard_vtuber.camera.devices import LocalCameraDevice
from kardboard_vtuber.gui import settings
from kardboard_vtuber.gui.window import StudioWindow
from kardboard_vtuber.runtime import RuntimeBridge


@pytest.fixture(scope="module")
def app() -> QApplication:
    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    return application


def wait_until(app: QApplication, predicate, timeout: float = 6) -> None:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
    assert predicate()


@pytest.fixture
def window(app: QApplication):
    studio = StudioWindow()
    studio.show()
    app.processEvents()
    yield studio
    if studio._tutorial is not None:
        studio._tutorial.close()
    studio.stop()
    wait_until(app, lambda: studio.worker is None and studio.job is None)
    studio.close()
    app.processEvents()


def test_window_has_all_controls_and_no_implicit_capture(window: StudioWindow) -> None:
    from kardboard_vtuber.gui.settings import parser_actions

    assert set(window.controls) == set(parser_actions())
    assert window.worker is None and window.job is None
    assert not window.stop_button.isEnabled()
    assert window.preview.image.isNull()
    source = window.controls["source"].editor
    assert isinstance(source, QLineEdit) and source.echoMode() == QLineEdit.EchoMode.Password
    assert not window.error_label.isVisible()
    assert not window.windowIcon().isNull()


def test_live_per_eye_edit_applies_atomically_and_invalid_edit_is_visible(
    window: StudioWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: pytest.fail("Live edits must not query disk/network files on the UI thread"),
    )
    window.bridge = RuntimeBridge()
    control = window.controls["left_blink_threshold"]
    control.set_value(0.25)
    control.changed.emit()
    assert window.bridge.tuning().eyes.left_closed == 0.25
    previous = window.bridge.tuning()
    window.controls["right_blink_threshold"].set_value(0.9)
    window.controls["right_blink_threshold"].changed.emit()
    assert window.error_label.isVisible()
    assert window.bridge.tuning() == previous
    window.bridge = None


def test_preset_import_does_not_restore_source_or_raw_consent(
    window: StudioWindow,
    tmp_path: Path,
) -> None:
    source = "user:synthetic'secret@invalid/video"
    window.controls["source"].set_value(source)
    window.controls["debug_face_preview"].set_value(True)
    path = tmp_path / "studio.json"
    window.save_preset(path)
    window._append_log("Failed to open: " + source)
    assert "secret" not in window.console.toPlainText()
    window.controls["source"].set_value("2")
    window.load_preset(path)
    assert window.controls["source"].value() == "2"
    assert window.controls["debug_face_preview"].value() is False
    assert "synthetic" not in window.command.toPlainText()
    assert window.worker is None


def test_unwritable_user_data_reports_error_without_starting_a_helper(
    window: StudioWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("Existing user file", encoding="utf-8")
    monkeypatch.setattr("kardboard_vtuber.gui.window.data_root", lambda: blocked)
    window._save_preset_dialog()
    assert "Cannot create the preset folder" in window.error_label.text()
    with pytest.raises(OSError):
        window._start_job("cameras", Path(__file__), [])
    assert window.job is None


def test_tutorial_can_jump_to_every_task_without_starting_camera(
    app: QApplication,
    window: StudioWindow,
) -> None:
    window.show_tutorial(3)
    app.processEvents()
    from kardboard_vtuber.gui.tutorial import LESSONS

    assert window._tutorial is not None and window._tutorial.selector.count() == len(LESSONS)
    window._tutorial.navigate.emit("Avatar & eyes")
    assert window.page_selector.currentText() == "Avatar & eyes"
    assert window.worker is None


def test_declining_raw_consent_never_creates_worker(
    monkeypatch: pytest.MonkeyPatch,
    window: StudioWindow,
) -> None:
    window.controls["debug_face_preview"].set_value(True)
    monkeypatch.setattr(window, "_confirm", lambda *args: False)
    window.start_camera()
    assert window.worker is None and not window.stop_button.isEnabled()


def test_demo_keeps_ui_heartbeat_and_cooperatively_stops(
    app: QApplication,
    window: StudioWindow,
) -> None:
    window.controls["physics"].set_value(False)
    window.controls["cardboard_renderer"].set_value("procedural-2d")
    beats: list[float] = []
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: beats.append(time.monotonic()))
    timer.start()
    try:
        window.start_demo()
        wait_until(app, lambda: not window.preview.image.isNull())
        assert window.controls["left_blink_threshold"].isEnabled()
        assert not window.controls["source"].isEnabled()
        assert "LOCKED" in window.controls["source"].state_badge.text()
        assert "LOCKED" in window.live_hint.text()
        assert window.output_window.isVisible()
        assert not window.output_window.canvas.image.isNull()
        window.controls["left_blink_threshold"].set_value(0.22)
        window.controls["left_blink_threshold"].changed.emit()
        assert window.bridge is not None and window.bridge.tuning().eyes.left_closed == 0.22
        QTest.qWait(250)
        assert len(beats) >= 10
        assert "SYNTHETIC" in window.status.text()
        window.stop()
        wait_until(app, lambda: window.worker is None)
        assert window.start_button.isEnabled() and window.preview.image.isNull()
    finally:
        timer.stop()


def test_video_canvas_copies_buffer_before_owner_changes(window: StudioWindow) -> None:
    frame = np.full((30, 40, 3), (10, 20, 30), dtype=np.uint8)
    window.preview.set_frame(frame)
    frame[:] = 0
    color = window.preview.image.pixelColor(5, 5)
    assert (color.red(), color.green(), color.blue()) == (30, 20, 10)


def test_close_while_demo_running_defers_until_thread_finishes(
    app: QApplication,
    window: StudioWindow,
) -> None:
    window.controls["physics"].set_value(False)
    window.controls["cardboard_renderer"].set_value("procedural-2d")
    window.start_demo()
    wait_until(app, lambda: not window.preview.image.isNull())
    window.close()
    assert window._closing
    wait_until(app, lambda: window.worker is None and not window.isVisible())


def test_model_verification_is_async_and_does_not_open_capture(
    app: QApplication,
    window: StudioWindow,
) -> None:
    model = Path(str(window.controls["face_model"].value()))
    from kardboard_vtuber.gui.settings import ROOT

    if not (ROOT / model).is_file():
        pytest.skip("Offline model is not installed")
    window.download_model("face_model")
    assert window.job is not None and window.worker is None
    wait_until(app, lambda: window.job is None, timeout=15)
    assert "verified" in window.console.toPlainText()
    assert window.start_button.isEnabled()


def test_worker_reports_parser_exit_as_failure_instead_of_success(
    app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kardboard_vtuber.gui import settings
    from kardboard_vtuber.gui.worker import SessionWorker

    def fail(*args: object, **kwargs: object) -> int:
        raise SystemExit(2)

    monkeypatch.setattr(settings, "required_models", lambda values: ())
    monkeypatch.setattr("kardboard_vtuber.gui.worker.cli.main", fail)
    bridge = RuntimeBridge()
    worker = SessionWorker(settings.defaults(), bridge)
    codes: list[int] = []
    worker.completed.connect(codes.append)
    worker.run()
    assert codes == [2]
    assert "exited unexpectedly" in "\n".join(bridge.take()[1])


def test_named_laptop_selection_routes_matching_native_backend_and_index(
    window: StudioWindow,
) -> None:
    window._native_devices = (
        LocalCameraDevice(2, "msmf", "Laptop RGB Camera"),
        LocalCameraDevice(0, "dshow", "Laptop RGB Camera"),
    )
    window._populate_native_cameras()
    window.native_camera.setCurrentIndex(1)
    args = settings.namespace(window.collected_values())
    assert args.source == "2" and args.backend == "msmf"
    assert "--source=2" in window.command.toPlainText()
    assert "$env:KARDBOARD_CAMERA_URL" not in window.command.toPlainText()
    assert window.worker is None and window.job is None
    window.native_camera.setCurrentIndex(2)
    args = settings.namespace(window.collected_values())
    assert args.source == "0" and args.backend == "dshow"


def test_switching_native_and_stream_sources_preserves_each_source_and_backend(
    window: StudioWindow,
) -> None:
    window.input_type.setCurrentIndex(1)
    window.controls["source"].set_value("rtsp://synthetic.invalid/video")
    window.controls["backend"].set_value("ffmpeg")
    window.input_type.setCurrentIndex(0)
    assert window.controls["source"].value() == "0"
    assert window.controls["backend"].value() == "auto"
    window._native_devices = (LocalCameraDevice(1, "dshow", "USB Camera"),)
    window._populate_native_cameras()
    window.native_camera.setCurrentIndex(1)
    window.input_type.setCurrentIndex(1)
    assert window.controls["source"].value() == "rtsp://synthetic.invalid/video"
    assert window.controls["backend"].value() == "ffmpeg"
    window.input_type.setCurrentIndex(0)
    assert window.controls["source"].value() == "1"
    assert window.controls["backend"].value() == "dshow"


def test_camera_inventory_does_not_open_capture_and_missing_selection_requires_reselection(
    window: StudioWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "kardboard_vtuber.cli.LatestFrameCamera",
        lambda config: pytest.fail("Accepting metadata must never open a camera"),
    )
    window._job_error = False
    window._camera_output = '[{"index":1,"backend":"dshow","name":"Laptop Camera"}]'
    window._accept_camera_inventory(0)
    window.native_camera.setCurrentIndex(1)
    assert window.controls["source"].value() == "1"
    window._camera_output = "[]"
    window._accept_camera_inventory(0)
    assert window.controls["source"].value() == ""
    assert "No camera entries" in window.native_hint.text()
    assert window.worker is None


def test_invalid_camera_inventory_is_explicit_and_does_not_replace_previous_list(
    window: StudioWindow,
) -> None:
    original = (LocalCameraDevice(0, "dshow", "Laptop Camera"),)
    window._native_devices = original
    window._camera_output = "not valid JSON"
    window._job_error = False
    window._accept_camera_inventory(0)
    assert window._job_error
    assert window._native_devices == original
    assert "Could not read the camera list" in window.console.toPlainText()


@pytest.mark.skipif(os.name != "nt", reason="Named device discovery uses Windows metadata APIs")
def test_native_inventory_job_completes_without_starting_capture(
    app: QApplication,
    window: StudioWindow,
) -> None:
    pytest.importorskip("cv2_enumerate_cameras")
    window.refresh_native_cameras()
    assert window.job is not None and window.worker is None
    wait_until(app, lambda: window.job is None, timeout=15)
    assert "[CAMERAS] Listed" in window.console.toPlainText()
    assert window.worker is None and window.start_button.isEnabled()


def test_bottom_command_tab_copies_the_complete_redacted_command(
    app: QApplication, window: StudioWindow,
) -> None:
    from PySide6.QtCore import Qt

    window.controls["source"].set_value("https://synthetic:secret@invalid/video")
    window._refresh_settings()
    window.console_tabs.setCurrentIndex(1)
    app.processEvents()
    QTest.mouseClick(window.copy_command, Qt.MouseButton.LeftButton)
    copied = app.clipboard().text()
    assert copied == window.command.toPlainText()
    assert "secret" not in copied and "Read-Host" in copied
    assert window.console_tabs.tabText(0) == "Logs"
    assert window.console_tabs.tabText(1) == "CLI equivalent"


def test_standard_resolution_selector_updates_both_values_without_unit_editors(
    window: StudioWindow,
) -> None:
    index = next(
        i for i in range(window.output_resolution.count())
        if window.output_resolution.itemData(i) == (1920, 1080)
    )
    window.output_resolution.setCurrentIndex(index)
    assert window.controls["virtual_camera_width"].value() == 1920
    assert window.controls["virtual_camera_height"].value() == 1080
    assert not window.controls["virtual_camera_width"].isVisible()
    assert not window.controls["virtual_camera_height"].isVisible()


def test_video_work_mode_is_not_private_camera_recording(window: StudioWindow) -> None:
    window.work_mode.setCurrentIndex(1)
    window.video_input.setText(r"C:\videos\my input.mp4")
    window.video_output.setText(r"C:\videos\my output.mkv")
    assert window.video_setup.isVisible()
    assert window.start_button.text() == "Process video"
    assert "VIDEO READY" in window.status.text()
    assert "input video" in window.preview.placeholder
    assert not window.controls["source"].isEnabled()
    assert window.controls["source"].state_badge.text() == "LIVE ONLY"
    assert "video_cli" in window.command.toPlainText()
    assert "--input-video=" in window.command.toPlainText()
    assert "record_guided_regression" not in window.command.toPlainText()
    window.work_mode.setCurrentIndex(0)
    assert window.controls["source"].isEnabled()


def test_raw_debug_channels_never_cover_program_or_clean_window(window: StudioWindow) -> None:
    from kardboard_vtuber.runtime import RuntimeTelemetry

    window.bridge = RuntimeBridge()
    clean = np.full((60, 80, 3), (10, 20, 30), np.uint8)
    raw = np.full_like(clean, (100, 110, 120))
    debug = np.full_like(clean, (200, 210, 220))
    window.bridge.publish(
        clean, RuntimeTelemetry(), clean_frame=clean, raw_face=raw, face_mesh=debug,
    )
    window._poll_runtime()
    assert window.raw_panel.isVisible() and window.diagnostic_panel.isVisible()
    assert window.preview.image.pixelColor(5, 5).red() == 30
    assert window.output_window.canvas.image.pixelColor(5, 5).red() == 30
    assert window.raw_face.image.pixelColor(5, 5).red() == 120
    assert window.face_mesh.image.pixelColor(5, 5).red() == 220
    window.bridge = None


def test_checkbox_visual_states_are_distinct_in_both_themes(
    app: QApplication, window: StudioWindow,
) -> None:
    from PySide6.QtWidgets import QCheckBox, QStyle, QStyleOptionButton

    window.page_selector.setCurrentText("Tracking labs")
    editor = window.controls["full_body"].editor
    assert isinstance(editor, QCheckBox)
    for _ in range(2):
        editor.setChecked(False)
        app.processEvents()
        unchecked = editor.grab().toImage()
        editor.setChecked(True)
        app.processEvents()
        checked = editor.grab().toImage()
        assert unchecked != checked
        option = QStyleOptionButton()
        editor.initStyleOption(option)
        indicator = editor.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, option, editor,
        )
        tick = checked.copy(indicator)
        expected = "#19332b" if window._dark else "#fff4db"
        assert any(
            tick.pixelColor(x, y).name() == expected
            for x in range(4, tick.width() - 4)
            for y in range(4, tick.height() - 4)
        ), "A filled square without a visible tick is not a checked-state affordance."
        assert "QCheckBox::indicator:checked" in window.styleSheet()
        window.toggle_theme()


def test_effective_calibrated_eye_decisions_are_visible(window: StudioWindow) -> None:
    from dataclasses import replace

    from kardboard_vtuber.runtime import RuntimeTelemetry
    from kardboard_vtuber.tracking.eyes import calibrate_eyes
    from tests.test_ps1_cardboard_renderer import state

    window.bridge = RuntimeBridge()
    window._apply_eye_calibration(calibrate_eyes([(.93, .94)] * 15, [(.51, .66)] * 15))
    raw = replace(state(1), left_eye_open=.51, right_eye_open=.66)
    window._display_telemetry(RuntimeTelemetry(face=raw, raw_face=raw), False)
    assert "CLOSED" in window.eye_labels["left"].text()
    assert "CLOSED" in window.eye_labels["right"].text()
    assert not window.error_label.isVisible()
    window.bridge = None


@pytest.mark.parametrize("player_accepts", [True, False])
def test_video_mode_exports_and_opens_actual_result_without_opening_a_camera(
    app: QApplication, window: StudioWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    player_accepts: bool,
) -> None:
    from types import SimpleNamespace

    from PySide6.QtCore import QThread

    from tests.test_ps1_cardboard_renderer import state
    from tests.test_video_export import clip

    closed = {"tracker": False, "renderer": False}

    class Tracker:
        def __init__(self, config) -> None:
            assert config.video_mode
            self.current = state(0)

        def submit(self, frame, captured_at_ns) -> None:
            self.current = state(captured_at_ns // 1_000_000)

        def snapshot(self):
            return SimpleNamespace(state=self.current, raw_state=self.current)

        def close(self) -> None:
            closed["tracker"] = True

    class Renderer:
        def render(self, frame, face) -> None:
            frame[10:20, 10:20] = (5, 15, 25)

        def close(self) -> None:
            closed["renderer"] = True

    source, target = tmp_path / "input.mkv", tmp_path / "processed video #1.mkv"
    clip(source)
    opened = []

    def open_player(url) -> bool:
        assert QThread.currentThread() == app.thread()
        assert target.is_file()
        assert all(closed.values())
        assert url.isLocalFile()
        opened.append(Path(url.toLocalFile()))
        return player_accepts

    monkeypatch.setattr("kardboard_vtuber.gui.window.QDesktopServices.openUrl", open_player)
    model = tmp_path / "face.task"
    model.write_bytes(b"synthetic model fixture")
    window.controls["face_model"].set_value(str(model))
    monkeypatch.setattr("kardboard_vtuber.video_pipeline.MediaPipeFaceTracker", Tracker)
    monkeypatch.setattr("kardboard_vtuber.cli._create_renderer", lambda *args, **kw: Renderer())
    monkeypatch.setattr(
        "kardboard_vtuber.cli.LatestFrameCamera",
        lambda *args: pytest.fail("Offline processing must not open a camera"),
    )
    window.work_mode.setCurrentIndex(1)
    window.video_input.setText(str(source))
    window.video_output.setText(str(target))
    window.start_camera()
    assert window._processing_video and window.worker is not None
    assert not window.controls["left_blink_threshold"].isEnabled()
    window.video_output.setText(str(tmp_path / "not-the-exported-file.mkv"))
    wait_until(app, lambda: window.worker is None, timeout=15)
    assert target.is_file()
    assert opened == [target.resolve()]
    assert "VIDEO SAVED" in window.status.text()
    assert "4 frames" in window.video_progress_label.text()
    assert window.error_label.isVisible() == (not player_accepts)
    if not player_accepts:
        assert "video was saved" in window.error_label.text()
        assert str(target.resolve()) in window.error_label.text()


@pytest.mark.parametrize("cancelled", [True, False])
def test_failed_or_cancelled_video_never_opens_default_player(
    app: QApplication, window: StudioWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    cancelled: bool,
) -> None:
    from kardboard_vtuber.video import ExportCancelled

    def fail(*args, **kwargs):
        if cancelled:
            raise ExportCancelled()
        raise RuntimeError("Simulated video export failure")

    monkeypatch.setattr("kardboard_vtuber.gui.video_worker.render_avatar_video", fail)
    monkeypatch.setattr(
        "kardboard_vtuber.gui.window.QDesktopServices.openUrl",
        lambda *_: pytest.fail("An incomplete export must never launch a player"),
    )
    target = tmp_path / "unfinished.mkv"
    window.work_mode.setCurrentIndex(1)
    window.video_input.setText(str(tmp_path / "input.mkv"))
    window.video_output.setText(str(target))
    window.start_camera()
    wait_until(app, lambda: window.worker is None)
    expected_status = "VIDEO CANCELLED" if cancelled else "VIDEO EXPORT FAILED"
    assert expected_status in window.status.text()
    assert not target.exists()
