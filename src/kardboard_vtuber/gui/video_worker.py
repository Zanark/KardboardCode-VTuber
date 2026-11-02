"""An owned export thread around the shared, synchronous video pipeline."""

from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from kardboard_vtuber.gui import settings
from kardboard_vtuber.runtime import RuntimeBridge
from kardboard_vtuber.video import ExportCancelled, VideoExportOptions
from kardboard_vtuber.video_pipeline import render_avatar_video


class VideoExportWorker(QThread):
    completed = Signal(int)
    progress = Signal(object)

    def __init__(
        self, values: dict[str, settings.SettingValue], options: VideoExportOptions,
        bridge: RuntimeBridge, *, already_mirrored: bool = False,
    ) -> None:
        super().__init__()
        self.values = dict(values)
        self.options = options
        self.bridge = bridge
        self.already_mirrored = already_mirrored
        self.demo = False

    def run(self) -> None:
        try:
            values = dict(self.values)
            values.update({
                "source": "0", "mirror": False, "rotate": "none", "virtual_camera": False,
                "input_already_mirrored": self.already_mirrored,
                "full_body": False, "body_head_fallback": False, "hood_marker_tracking": False,
                "debug_face_preview": False, "tracking_debug": False,
                "render_cardboard": True, "headless": False,
            })
            render_avatar_video(
                settings.namespace(values), self.options, self.bridge, self.progress.emit,
            )
        except ExportCancelled:
            self.bridge.log("[VIDEO] Cancelled. No completed output file was created.")
            self.completed.emit(130)
        except Exception:
            self.bridge.log("[ERROR] Video export failed: " + traceback.format_exc())
            self.completed.emit(1)
        else:
            self.completed.emit(0)
