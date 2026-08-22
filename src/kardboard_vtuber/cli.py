"""Command-line camera preview and diagnostics."""

from __future__ import annotations

import argparse
import sys
import time

import cv2

from kardboard_vtuber.camera import CameraBackend, CameraConfig, CameraRotation, CameraSource
from kardboard_vtuber.camera.stream import LatestFrameCamera


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kardboard-camera",
        description="Preview a local or phone-hosted camera stream with low-latency buffering.",
    )
    parser.add_argument(
        "--source",
        default="0",
        help="Local device index or URL, for example http://PHONE_IP:8080/video.",
    )
    parser.add_argument(
        "--backend",
        choices=[backend.value for backend in CameraBackend],
        default=CameraBackend.AUTO.value,
        help="OpenCV backend. Use ffmpeg for network streams if auto fails.",
    )
    parser.add_argument("--width", type=int, help="Requested capture width.")
    parser.add_argument("--height", type=int, help="Requested capture height.")
    parser.add_argument("--fps", type=float, help="Requested capture FPS.")
    parser.add_argument(
        "--rotate",
        choices=[rotation.value for rotation in CameraRotation],
        default=CameraRotation.NONE.value,
        help="Rotate frames left, right, or 180 degrees after capture.",
    )
    parser.add_argument("--mirror", action="store_true", help="Mirror frames horizontally.")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Capture and print diagnostics without opening a preview window.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Exit after this many seconds. By default, run until Q or Escape.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CameraConfig(
        source=CameraSource.parse(args.source),
        backend=CameraBackend(args.backend),
        requested_width=args.width,
        requested_height=args.height,
        requested_fps=args.fps,
        rotation=CameraRotation(args.rotate),
        mirror=args.mirror,
    )
    camera = LatestFrameCamera(config)
    started_at = time.monotonic()
    last_sequence: int | None = None
    last_report_at = 0.0
    window_name = "KardboardCode Camera Preview"

    try:
        camera.start()
        while True:
            packet = camera.read(after_sequence=last_sequence, timeout=2.0, copy=False)
            now = time.monotonic()
            if packet is None:
                snapshot = camera.snapshot()
                print(
                    f"camera unavailable: state={snapshot.state.value} "
                    f"error={snapshot.last_error}",
                    file=sys.stderr,
                )
                if snapshot.state.value == "failed":
                    return 1
                continue

            last_sequence = packet.sequence
            if now - last_report_at >= 2.0:
                _print_snapshot(camera)
                last_report_at = now

            if not args.headless:
                frame = packet.frame
                snapshot = camera.snapshot()
                latency_ms = (time.monotonic_ns() - packet.captured_at_ns) / 1_000_000
                label = (
                    f"{packet.width}x{packet.height}  "
                    f"{snapshot.measured_fps:.1f} FPS  "
                    f"{latency_ms:.1f} ms frame age"
                )
                cv2.putText(
                    frame,
                    label,
                    (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (80, 255, 80),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in {ord("q"), 27}:
                    break

            if args.duration is not None and now - started_at >= args.duration:
                break
    except KeyboardInterrupt:
        pass
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        camera.stop()
        cv2.destroyAllWindows()
    return 0


def _print_snapshot(camera: LatestFrameCamera) -> None:
    snapshot = camera.snapshot()
    print(
        " | ".join(
            [
                f"state={snapshot.state.value}",
                f"source={snapshot.source}",
                f"backend={snapshot.backend.value}",
                f"negotiated={snapshot.negotiated_width}x{snapshot.negotiated_height}"
                f"@{snapshot.negotiated_fps:.2f}",
                f"measured_fps={snapshot.measured_fps:.2f}",
                f"received={snapshot.received_frames}",
                f"overwritten={snapshot.overwritten_frames}",
                f"failures={snapshot.read_failures}",
                f"reconnects={snapshot.reconnects}",
            ]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
