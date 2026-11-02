"""Native runtime isolation; only the main Qt thread touches widgets."""

from __future__ import annotations

import math
import time
import traceback
from dataclasses import replace

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from kardboard_vtuber import cli
from kardboard_vtuber.gui.settings import SettingValue, arguments, namespace
from kardboard_vtuber.runtime import RuntimeBridge, RuntimeTelemetry
from kardboard_vtuber.tracking.events import FaceActionDetector
from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose


class SessionWorker(QThread):
    completed = Signal(int)

    def __init__(
        self,
        values: dict[str, SettingValue],
        bridge: RuntimeBridge,
        *,
        demo: bool = False,
    ) -> None:
        super().__init__()
        self.values = dict(values)
        self.bridge = bridge
        self.demo = demo

    def run(self) -> None:
        try:
            if not self.demo:
                from kardboard_vtuber.gui.settings import required_models

                missing = required_models(self.values)
                if missing:
                    raise ValueError(
                        "Missing models: " + ", ".join(missing) + ". Open Models to set them up.",
                    )
            result = (
                self._run_demo()
                if self.demo
                else cli.main(
                    arguments(self.values),
                    runtime=self.bridge,
                )
            )
        except Exception:
            # A thread boundary must report unexpected native/setup failures to the operator.
            self.bridge.log("[ERROR] " + traceback.format_exc())
            result = 1
        self.completed.emit(result)

    def _run_demo(self) -> int:
        args = namespace(self.values)
        self.bridge.log(
            "[DEMO] Synthetic stage only. No camera, microphone, or virtual output opened."
        )
        renderer = cli._create_renderer(
            args,
            report=lambda message, **_: self.bridge.log(message),
        )
        detector = FaceActionDetector(self.bridge.tuning().action_thresholds())
        last_action = ""
        current_tuning = None
        started = time.monotonic()
        try:
            while not self.bridge.stop_event.is_set():
                tick = time.monotonic()
                elapsed = tick - started
                if args.duration is not None and elapsed >= args.duration:
                    break
                tuning = self.bridge.tuning()
                if tuning != current_tuning:
                    renderer.set_eye_sensitivity(tuning.eyes)
                    detector.set_thresholds(tuning.action_thresholds())
                    current_tuning = tuning
                frame = _synthetic_stage(args.green_screen)
                state = FaceTrackingState(
                    timestamp_ms=time.monotonic_ns() // 1_000_000,
                    detected=True,
                    landmarks=(),
                    center_x=0.5,
                    center_y=0.54,
                    face_width=0.11,
                    face_height=0.20,
                    left_eye_open=0.92 if elapsed % 7 > 0.3 else 0.20,
                    right_eye_open=0.94 if elapsed % 9 > 0.3 else 0.20,
                    mouth_open=(1 + math.sin(elapsed * 1.8)) * 0.25,
                    head_pose=HeadPose(
                        0,
                        0,
                        0,
                        -10 + 12 * math.sin(elapsed * 0.6),
                        24 * math.sin(elapsed * 0.45),
                        5 * math.sin(elapsed * 0.8),
                    ),
                )
                renderer.render(frame, state)
                events = detector.update(state)
                if events:
                    last_action = events[0].action.value
                    for event in events:
                        self.bridge.log("[DEMO] " + event.format_log())
                if args.tracking_debug:
                    from kardboard_vtuber.tracking.mediapipe_tracker import draw_tracking_debug

                    draw_tracking_debug(frame, state, action=last_action, draw_frame_geometry=False)
                cv2.putText(
                    frame,
                    "SYNTHETIC DEMO / NO CAMERA INPUT",
                    (28, 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (192, 230, 219),
                    1,
                    cv2.LINE_AA,
                )
                telemetry = RuntimeTelemetry(
                    face=state,
                    raw_face=replace(state),
                    effective_detected=True,
                    frame_size=(1280, 720),
                    capture_state="synthetic",
                    action=last_action,
                    demo=True,
                )
                self.bridge.publish(None if args.headless else frame, telemetry)
                self.bridge.stop_event.wait(max(0.0, 1 / 30 - (time.monotonic() - tick)))
        finally:
            renderer.close()
        return 0


def _synthetic_stage(green_screen: bool) -> np.ndarray:
    frame = np.empty((720, 1280, 3), dtype=np.uint8)
    if green_screen:
        frame[:] = (0, 255, 0)
    else:
        for row in range(720):
            level = int(20 + 14 * row / 720)
            frame[row] = (level + 9, level + 5, level)
        for x in range(0, 1280, 80):
            cv2.line(frame, (x, 0), (x, 720), (49, 49, 40), 1)
        for y in range(80, 720, 80):
            cv2.line(frame, (0, y), (1280, y), (49, 49, 40), 1)
    cv2.ellipse(frame, (640, 690), (235, 25), 0, 0, 360, (13, 19, 18), -1)
    torso = np.array(
        [(555, 420), (725, 420), (815, 500), (850, 720), (430, 720), (465, 500)], dtype=np.int32
    )
    cv2.fillConvexPoly(frame, torso, (40, 43, 42))
    cv2.line(frame, (640, 480), (640, 720), (70, 76, 72), 2)
    return frame
