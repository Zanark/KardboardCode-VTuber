"""Threaded latest-frame-only OpenCV capture."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol

import cv2

from kardboard_vtuber.camera.models import (
    CameraConfig,
    CaptureSnapshot,
    CaptureState,
    FramePacket,
)


class VideoCaptureLike(Protocol):
    def isOpened(self) -> bool: ...

    def read(self) -> tuple[bool, object]: ...

    def release(self) -> None: ...

    def set(self, prop_id: int, value: float) -> bool: ...

    def get(self, prop_id: int) -> float: ...


CaptureFactory = Callable[[int | str, int], VideoCaptureLike]


def _default_capture_factory(source: int | str, backend: int) -> VideoCaptureLike:
    return cv2.VideoCapture(source, backend)


class LatestFrameCamera:
    """Continuously captures frames without allowing latency-producing queues.

    The worker stores exactly one frame. If a new frame arrives before the
    consumer reads the previous frame, the previous frame is overwritten.
    This intentionally trades completeness for low latency.
    """

    def __init__(
        self,
        config: CameraConfig,
        *,
        capture_factory: CaptureFactory = _default_capture_factory,
    ) -> None:
        self._config = config
        self._capture_factory = capture_factory
        self._condition = threading.Condition()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._capture: VideoCaptureLike | None = None
        self._latest: FramePacket | None = None
        self._state = CaptureState.STOPPED
        self._sequence = 0
        self._received_frames = 0
        self._overwritten_frames = 0
        self._read_failures = 0
        self._reconnects = 0
        self._last_error: str | None = None
        self._negotiated_width = 0
        self._negotiated_height = 0
        self._negotiated_fps = 0.0
        self._fps_window_started_ns = 0
        self._fps_window_frames = 0
        self._measured_fps = 0.0

    @property
    def config(self) -> CameraConfig:
        return self._config

    def start(self, *, wait_until_running: float = 5.0) -> None:
        with self._condition:
            if self._thread and self._thread.is_alive():
                return
            self._state = CaptureState.STARTING
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="kardboard-camera-capture",
                daemon=True,
            )
            self._thread.start()
            deadline = time.monotonic() + wait_until_running
            while self._state in {CaptureState.STARTING, CaptureState.RECONNECTING}:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(remaining)
            if self._state is CaptureState.FAILED:
                raise RuntimeError(self._last_error or "camera failed to start")

    def stop(self, *, timeout: float = 5.0) -> None:
        self._stop_event.set()
        with self._condition:
            self._condition.notify_all()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout)
        capture = self._capture
        if capture is not None:
            capture.release()
        with self._condition:
            self._capture = None
            self._state = CaptureState.STOPPED
            self._condition.notify_all()

    def read(
        self,
        *,
        after_sequence: int | None = None,
        timeout: float | None = 1.0,
        copy: bool = True,
    ) -> FramePacket | None:
        """Return the newest frame, optionally waiting for a newer sequence."""

        deadline = None if timeout is None else time.monotonic() + timeout
        with self._condition:
            while True:
                packet = self._latest
                is_new = packet is not None and (
                    after_sequence is None or packet.sequence > after_sequence
                )
                if is_new:
                    frame = packet.frame.copy() if copy else packet.frame
                    return FramePacket(packet.sequence, packet.captured_at_ns, frame)
                if self._state in {CaptureState.FAILED, CaptureState.STOPPED}:
                    return None
                if deadline is None:
                    self._condition.wait()
                    continue
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._condition.wait(remaining)

    def snapshot(self) -> CaptureSnapshot:
        with self._condition:
            return CaptureSnapshot(
                state=self._state,
                source=self._config.source.redacted(),
                backend=self._config.backend,
                negotiated_width=self._negotiated_width,
                negotiated_height=self._negotiated_height,
                negotiated_fps=self._negotiated_fps,
                received_frames=self._received_frames,
                overwritten_frames=self._overwritten_frames,
                read_failures=self._read_failures,
                reconnects=self._reconnects,
                measured_fps=self._measured_fps,
                last_error=self._last_error,
            )

    def __enter__(self) -> LatestFrameCamera:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    def _run(self) -> None:
        consecutive_failures = 0
        try:
            while not self._stop_event.is_set():
                if self._capture is None or not self._capture.isOpened():
                    if not self._open():
                        if self._stop_event.wait(self._config.reconnect_delay_seconds):
                            break
                        continue
                    consecutive_failures = 0

                capture = self._capture
                if capture is None:
                    continue
                ok, frame = capture.read()
                if not ok or frame is None:
                    consecutive_failures += 1
                    with self._condition:
                        self._read_failures += 1
                    if consecutive_failures >= self._config.max_consecutive_failures:
                        self._disconnect("camera stopped returning frames")
                    else:
                        time.sleep(0.005)
                    continue

                consecutive_failures = 0
                rotation_code = self._config.rotation.opencv_code
                if rotation_code is not None:
                    frame = cv2.rotate(frame, rotation_code)
                if self._config.mirror:
                    frame = cv2.flip(frame, 1)
                captured_at_ns = time.monotonic_ns()
                with self._condition:
                    self._sequence += 1
                    if self._latest is not None:
                        self._overwritten_frames += 1
                    self._latest = FramePacket(self._sequence, captured_at_ns, frame)
                    self._received_frames += 1
                    self._update_measured_fps(captured_at_ns)
                    self._state = CaptureState.RUNNING
                    self._condition.notify_all()
        except Exception as error:
            with self._condition:
                self._last_error = f"{type(error).__name__}: {error}"
                self._state = CaptureState.FAILED
                self._condition.notify_all()
        finally:
            capture = self._capture
            if capture is not None:
                capture.release()
            with self._condition:
                self._capture = None
                if self._state is not CaptureState.FAILED:
                    self._state = CaptureState.STOPPED
                self._condition.notify_all()

    def _open(self) -> bool:
        with self._condition:
            self._state = (
                CaptureState.STARTING
                if self._received_frames == 0
                else CaptureState.RECONNECTING
            )
            self._condition.notify_all()

        capture = self._capture_factory(
            self._config.source.value,
            self._config.backend.opencv_id,
        )
        self._apply_requests(capture)
        if not capture.isOpened():
            capture.release()
            with self._condition:
                self._last_error = (
                    f"could not open camera source {self._config.source.redacted()} "
                    f"with backend {self._config.backend.value}"
                )
                self._state = CaptureState.RECONNECTING
                self._reconnects += 1
                self._condition.notify_all()
            return False

        with self._condition:
            self._capture = capture
            self._negotiated_width = round(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self._negotiated_height = round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._negotiated_fps = capture.get(cv2.CAP_PROP_FPS)
            self._fps_window_started_ns = time.monotonic_ns()
            self._fps_window_frames = 0
            self._last_error = None
            self._state = CaptureState.RUNNING
            self._condition.notify_all()
        return True

    def _apply_requests(self, capture: VideoCaptureLike) -> None:
        capture.set(cv2.CAP_PROP_BUFFERSIZE, float(self._config.buffer_size))
        if self._config.requested_width is not None:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._config.requested_width))
        if self._config.requested_height is not None:
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._config.requested_height))
        if self._config.requested_fps is not None:
            capture.set(cv2.CAP_PROP_FPS, self._config.requested_fps)

    def _disconnect(self, error: str) -> None:
        capture = self._capture
        if capture is not None:
            capture.release()
        with self._condition:
            self._capture = None
            self._last_error = error
            self._state = CaptureState.RECONNECTING
            self._reconnects += 1
            self._condition.notify_all()

    def _update_measured_fps(self, now_ns: int) -> None:
        self._fps_window_frames += 1
        elapsed_seconds = (now_ns - self._fps_window_started_ns) / 1_000_000_000
        if elapsed_seconds >= 1.0:
            self._measured_fps = self._fps_window_frames / elapsed_seconds
            self._fps_window_started_ns = now_ns
            self._fps_window_frames = 0
