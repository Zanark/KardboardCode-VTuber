import pytest

from kardboard_vtuber.camera.models import CameraConfig, CameraSource


def test_camera_source_parses_device_index() -> None:
    source = CameraSource.parse("2")

    assert source.value == 2
    assert not source.is_network_stream


def test_camera_source_preserves_stream_url() -> None:
    source = CameraSource.parse("http://192.168.42.129:8080/video")

    assert source.value == "http://192.168.42.129:8080/video"
    assert source.is_network_stream


def test_camera_source_redacts_credentials() -> None:
    source = CameraSource.parse("rtsp://user:password@192.168.42.129/live")

    assert source.redacted() == "rtsp://***@192.168.42.129/live"


@pytest.mark.parametrize("raw", ["", "   "])
def test_camera_source_rejects_empty_value(raw: str) -> None:
    with pytest.raises(ValueError):
        CameraSource.parse(raw)


def test_camera_config_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError):
        CameraConfig(CameraSource(0), requested_width=0)

