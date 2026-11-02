"""Offline video processing, without importing Qt or opening a camera."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from kardboard_vtuber import cli
from kardboard_vtuber.runtime import RuntimeBridge
from kardboard_vtuber.video import ExportCancelled, VideoExportOptions, VideoProgress
from kardboard_vtuber.video_pipeline import VIDEO_FIELDS, render_avatar_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-video", type=Path, required=True)
    parser.add_argument("--output-video", type=Path, required=True)
    parser.add_argument("--video-quality", choices=("lossless", "mp4"), default="lossless")
    for action in cli.build_parser()._actions:
        if action.dest not in VIDEO_FIELDS:
            continue
        kwargs: dict[str, object] = {"default": action.default, "help": action.help}
        if isinstance(action, argparse._StoreTrueAction):
            kwargs["action"] = "store_true"
        else:
            kwargs["type"] = action.type
            if action.choices:
                kwargs["choices"] = action.choices
        parser.add_argument(*action.option_strings, **kwargs)
    return parser


def main(argv: list[str] | None = None) -> int:
    selected = build_parser().parse_args(argv)
    args = cli.build_parser().parse_args([])
    for name in VIDEO_FIELDS:
        setattr(args, name, getattr(selected, name))
    args.render_cardboard, args.headless = True, True
    try:
        cli.validate_options(args)
        bridge = RuntimeBridge(cli.live_tuning(args))
    except ValueError as error:
        print(f"Invalid video settings: {error}", file=sys.stderr)
        return 2
    previous = signal.signal(signal.SIGINT, lambda *_: bridge.stop_event.set())

    def report(progress: VideoProgress) -> None:
        print(
            f"frames={progress.frames} source_seconds={progress.seconds:.2f} "
            f"size={progress.width}x{progress.height}", flush=True,
        )

    try:
        render_avatar_video(
            args, VideoExportOptions(
                selected.input_video, selected.output_video, selected.video_quality,
            ), bridge, report,
        )
        code = 0
    except ExportCancelled:
        print("Cancelled; no completed output created.", file=sys.stderr)
        code = 130
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f"Video export failed: {error}", file=sys.stderr)
        code = 1
    finally:
        signal.signal(signal.SIGINT, previous)
        for line in bridge.take()[1]:
            print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
