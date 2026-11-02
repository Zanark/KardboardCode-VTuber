"""Frame-complete local video export with source timing and audio stream copying."""

from __future__ import annotations

import os
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from threading import Event
from typing import Literal

import numpy as np
from numpy import ndarray


class ExportCancelled(Exception):
    """Cooperative cancellation; no completed output has been published."""


@dataclass(frozen=True, slots=True)
class VideoExportOptions:
    source: Path
    destination: Path
    quality: Literal["lossless", "mp4"] = "lossless"

    def validate(self) -> None:
        if self.quality not in {"lossless", "mp4"}:
            raise ValueError("Choose lossless MKV or high-quality MP4.")
        if not self.source.is_file():
            raise ValueError("Choose an existing local input video file.")
        if self.source.resolve() == self.destination.resolve():
            raise ValueError("The output must never replace the input video.")
        if self.destination.exists() or self.destination.is_symlink():
            raise ValueError(
                "The output already exists. Choose a new filename; it is not overwritten.",
            )
        extension = ".mkv" if self.quality == "lossless" else ".mp4"
        if self.destination.suffix.lower() != extension:
            raise ValueError(f"The selected format needs a {extension} output filename.")


@dataclass(frozen=True, slots=True)
class VideoProgress:
    frames: int
    seconds: float
    duration: float | None
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class VideoExportResult:
    path: Path
    frames: int
    width: int
    height: int
    audio_streams: int


def export_video(
    options: VideoExportOptions,
    process: Callable[[ndarray, int], None],
    *,
    cancel: Event,
    progress: Callable[[VideoProgress], None],
) -> VideoExportResult:
    import av

    options.validate()
    if cancel.is_set():
        raise ExportCancelled()
    options.destination.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(options.source)) as source:
        if len(source.streams.video) != 1:
            raise ValueError("Choose a video containing exactly one video stream.")
        if any(stream.type not in {"video", "audio"} for stream in source.streams):
            raise ValueError(
                "Subtitle/data/attachment streams are unsupported and were not silently discarded.",
            )
        original = source.streams.video[0]
        rate = original.average_rate or original.base_rate
        if rate is None:
            raise ValueError("The source has no usable frame-rate metadata; no rate was invented.")
        width, height = original.width, original.height
        if width <= 0 or height <= 0 or original.time_base is None:
            raise ValueError("The source has no usable dimensions or presentation time base.")
        if original.sample_aspect_ratio not in (None, Fraction(1, 1)):
            raise ValueError("Non-square-pixel video needs normalization before this export.")
        if options.quality == "mp4" and (width % 2 or height % 2):
            raise ValueError("MP4 needs even source dimensions; use lossless MKV for this input.")
        duration = (
            float(original.duration * original.time_base)
            if original.duration is not None else
            source.duration / av.time_base if source.duration is not None else None
        )
        with tempfile.TemporaryDirectory(
            prefix=".kardboard-export-", dir=options.destination.parent,
        ) as directory:
            temporary = Path(directory) / ("video" + options.destination.suffix.lower())
            audio_count = len(source.streams.audio)
            frames = 0
            first_time: Fraction | None = None
            previous_time: Fraction | None = None
            last_report = 0.0
            format_name = "matroska" if options.quality == "lossless" else "mp4"
            with av.open(str(temporary), "w", format=format_name) as output:
                output.metadata.update(source.metadata)
                target = output.add_stream(
                    "ffv1" if options.quality == "lossless" else "libx264",
                    rate=rate,
                )
                target.width, target.height = width, height
                target.time_base = original.time_base
                target.codec_context.time_base = original.time_base
                target.pix_fmt = "bgr0" if options.quality == "lossless" else "yuv420p"
                target.options = (
                    {"level": "3", "coder": "1", "context": "1", "slicecrc": "1"}
                    if options.quality == "lossless" else
                    {"crf": "17", "preset": "medium"}
                )
                audio = {
                    stream.index: output.add_stream_from_template(stream)
                    for stream in source.streams.audio
                }
                for packet in source.demux([original, *source.streams.audio]):
                    if cancel.is_set():
                        raise ExportCancelled()
                    stream_index = packet.stream.index
                    if stream_index in audio:
                        if packet.dts is not None:
                            packet.stream = audio[stream_index]
                            output.mux(packet)
                        continue
                    for decoded in packet.decode():
                        if cancel.is_set():
                            raise ExportCancelled()
                        if decoded.pts is None or decoded.time_base is None:
                            raise ValueError(
                                "A source frame has no timestamp; timing cannot be preserved.",
                            )
                        if decoded.rotation:
                            raise ValueError(
                                "Rotation-metadata video needs normalization first. "
                                "No automatic rotation or rescaling was performed.",
                            )
                        if decoded.interlaced_frame:
                            raise ValueError("Interlaced input needs normalization before export.")
                        if any(component.bits > 8 or component.is_alpha
                               for component in decoded.format.components):
                            raise ValueError(
                                "This renderer accepts opaque 8-bit SDR video. "
                                "HDR/high-bit-depth/alpha conversion is not performed silently.",
                            )
                        if getattr(original.codec_context, "color_trc", 2) in (16, 18):
                            raise ValueError(
                                "HDR transfer functions are unsupported; "
                                "no SDR conversion was made.",
                            )
                        if decoded.width != width or decoded.height != height:
                            raise ValueError(
                                "Source dimensions change mid-video; export was stopped.",
                            )
                        timestamp = decoded.pts * decoded.time_base
                        if previous_time is not None and timestamp <= previous_time:
                            raise ValueError("Source frame timestamps are not strictly increasing.")
                        if first_time is None:
                            first_time = timestamp
                        previous_time = timestamp
                        frame = decoded.to_ndarray(format="bgr24")
                        process(frame, round(float(timestamp - first_time) * 1000))
                        if frame.dtype != np.uint8 or frame.shape != (height, width, 3):
                            raise ValueError(
                                "The processor changed source dimensions or pixel type.",
                            )
                        encoded_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
                        encoded_frame.pts = decoded.pts
                        encoded_frame.time_base = decoded.time_base
                        encoded_frame.duration = decoded.duration
                        for encoded in target.encode(encoded_frame):
                            output.mux(encoded)
                        frames += 1
                        now = time.monotonic()
                        if now - last_report >= 0.1:
                            progress(VideoProgress(
                                frames, float(timestamp - first_time), duration, width, height,
                            ))
                            last_report = now
                for encoded in target.encode():
                    output.mux(encoded)
            if not frames:
                raise ValueError("No video frames could be decoded.")
            if cancel.is_set():
                raise ExportCancelled()
            # Atomic no-overwrite publication; the temporary lives on the destination filesystem.
            try:
                os.link(temporary, options.destination)
            except FileExistsError as error:
                raise ValueError(
                    "Another file appeared at the output path. It was not overwritten.",
                ) from error
            except OSError as error:
                raise RuntimeError(
                    "Could not publish the completed video without overwriting. Check permissions "
                    "and use a filesystem supporting hard links, such as a local NTFS folder.",
                ) from error
            progress(VideoProgress(frames, duration or 0.0, duration, width, height))
            return VideoExportResult(options.destination, frames, width, height, audio_count)
