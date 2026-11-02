from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from threading import Event

import numpy as np
import pytest

from kardboard_vtuber.video import ExportCancelled, VideoExportOptions, export_video

av = pytest.importorskip("av")


def clip(
    path: Path, *, audio: bool = True, audio_codec: str = "pcm_s16le",
) -> list[np.ndarray]:
    originals = []
    with av.open(str(path), "w") as output:
        video = output.add_stream("ffv1", rate=25)
        video.width, video.height, video.pix_fmt = 80, 64, "bgr0"
        video.time_base = video.codec_context.time_base = Fraction(1, 1000)
        sound = output.add_stream(audio_codec, rate=48000) if audio else None
        if sound is not None:
            sound.layout = "mono"
        for index, timestamp in enumerate((0, 40, 120, 160)):
            image = np.full((64, 80, 3), (index * 40, 50, 180), np.uint8)
            image[:, ::3, 0] = 170
            originals.append(image)
            frame = av.VideoFrame.from_ndarray(image, format="bgr24")
            frame.pts, frame.time_base, frame.duration = timestamp, Fraction(1, 1000), 40
            for packet in video.encode(frame):
                output.mux(packet)
        for packet in video.encode():
            output.mux(packet)
        if sound is not None:
            samples = (np.sin(np.arange(9600) * 0.06) * 8000).astype(np.int16)[None, :]
            frame = av.AudioFrame.from_ndarray(samples, format="s16", layout="mono")
            frame.sample_rate, frame.pts, frame.time_base = 48000, 0, Fraction(1, 48000)
            for packet in sound.encode(frame):
                output.mux(packet)
            for packet in sound.encode():
                output.mux(packet)
    return originals


def timestamps(path: Path) -> list[Fraction]:
    with av.open(str(path)) as container:
        return [frame.pts * frame.time_base for frame in container.decode(video=0)]


def audio_payloads(path: Path) -> list[bytes]:
    with av.open(str(path)) as container:
        return [bytes(packet) for packet in container.demux(audio=0) if packet.size]


def test_lossless_export_keeps_pixels_vfr_timing_and_audio(tmp_path: Path) -> None:
    source, target = tmp_path / "source.mkv", tmp_path / "output.mkv"
    original = clip(source)
    input_bytes = source.read_bytes()
    progress = []
    seen = []

    def process(frame: np.ndarray, timestamp: int) -> None:
        seen.append(timestamp)
        frame[10:20, 20:30] = (5, 15, 25)

    result = export_video(
        VideoExportOptions(source, target), process, cancel=Event(), progress=progress.append,
    )
    assert result.frames == 4 and result.audio_streams == 1
    assert seen == [0, 40, 120, 160]
    with av.open(str(target)) as container:
        decoded = [frame.to_ndarray(format="bgr24") for frame in container.decode(video=0)]
    for before, after in zip(original, decoded, strict=True):
        before[10:20, 20:30] = (5, 15, 25)
        np.testing.assert_array_equal(before, after)
    assert timestamps(target) == timestamps(source)
    assert audio_payloads(target) == audio_payloads(source)
    assert source.read_bytes() == input_bytes
    assert progress[-1].frames == 4
    assert not list(tmp_path.glob(".kardboard-export-*"))


def test_mp4_export_processes_every_frame_without_resizing(tmp_path: Path) -> None:
    source, target = tmp_path / "source.mkv", tmp_path / "output.mp4"
    clip(source, audio=False)
    export_video(
        VideoExportOptions(source, target, "mp4"), lambda frame, timestamp: None,
        cancel=Event(), progress=lambda value: None,
    )
    with av.open(str(target)) as container:
        frames = list(container.decode(video=0))
        assert len(frames) == 4
        assert all((frame.width, frame.height) == (80, 64) for frame in frames)
    assert timestamps(target) == timestamps(source)


def test_cancel_removes_partial_output_and_never_replaces_files(tmp_path: Path) -> None:
    source, target = tmp_path / "source.mkv", tmp_path / "output.mkv"
    clip(source, audio=False)
    cancel = Event()

    def process(frame: np.ndarray, timestamp: int) -> None:
        cancel.set()

    with pytest.raises(ExportCancelled):
        export_video(
            VideoExportOptions(source, target), process, cancel=cancel, progress=lambda value: None,
        )
    assert not target.exists() and not list(tmp_path.glob(".kardboard-export-*"))
    target.write_bytes(b"existing file")
    with pytest.raises(ValueError, match="already exists"):
        VideoExportOptions(source, target).validate()
    with pytest.raises(ValueError, match="input video"):
        VideoExportOptions(source, source).validate()
    assert target.read_bytes() == b"existing file"


def test_mp4_copies_aac_audio_packets_without_reencoding(tmp_path: Path) -> None:
    source, target = tmp_path / "source.mkv", tmp_path / "output.mp4"
    clip(source, audio_codec="aac")
    result = export_video(
        VideoExportOptions(source, target, "mp4"), lambda frame, timestamp: None,
        cancel=Event(), progress=lambda value: None,
    )
    assert result.frames == 4 and result.audio_streams == 1
    assert audio_payloads(target) == audio_payloads(source)
    assert all(
        abs(float(a - b)) < .001 for a, b in zip(
            timestamps(source), timestamps(target), strict=True,
        )
    )


def test_high_bit_depth_is_rejected_without_silent_conversion(tmp_path: Path) -> None:
    source, target = tmp_path / "ten-bit.mkv", tmp_path / "output.mkv"
    with av.open(str(source), "w") as output:
        stream = output.add_stream("ffv1", rate=25)
        stream.width, stream.height, stream.pix_fmt = 80, 64, "yuv444p10le"
        image = av.VideoFrame.from_ndarray(np.zeros((64, 80, 3), np.uint8), format="bgr24")
        image.pts, image.time_base = 0, Fraction(1, 25)
        for packet in stream.encode(image):
            output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    with pytest.raises(ValueError, match="8-bit SDR"):
        export_video(
            VideoExportOptions(source, target), lambda frame, timestamp: None,
            cancel=Event(), progress=lambda value: None,
        )
    assert not target.exists() and not list(tmp_path.glob(".kardboard-export-*"))


def test_concurrently_created_destination_is_never_overwritten(tmp_path: Path) -> None:
    source, target = tmp_path / "source.mkv", tmp_path / "output.mkv"
    clip(source, audio=False)

    def process(frame: np.ndarray, timestamp: int) -> None:
        if not target.exists():
            target.write_bytes(b"belongs to another writer")

    with pytest.raises(ValueError, match="not overwritten"):
        export_video(
            VideoExportOptions(source, target), process, cancel=Event(),
            progress=lambda value: None,
        )
    assert target.read_bytes() == b"belongs to another writer"
