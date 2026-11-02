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
    window.controls["source"].set_value("rtsp://user:synthetic@invalid/video")
    window.controls["debug_face_preview"].set_value(True)
    path = tmp_path / "studio.json"
    window.save_preset(path)
    window.controls["source"].set_value("2")
    window.load_preset(path)
    assert window.controls["source"].value() == "2"
    assert window.controls["debug_face_preview"].value() is False
    assert "synthetic" not in window.command.toPlainText()
    assert window.worker is None


def test_tutorial_can_jump_to_every_task_without_starting_camera(
    app: QApplication,
    window: StudioWindow,
) -> None:
    window.show_tutorial(3)
    app.processEvents()
    assert window._tutorial is not None and window._tutorial.selector.count() == 9
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
