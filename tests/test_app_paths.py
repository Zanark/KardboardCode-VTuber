from __future__ import annotations

from pathlib import Path

from kardboard_vtuber import app_paths, cli


def test_installed_models_data_and_helpers_do_not_depend_on_checkout(
    tmp_path: Path, monkeypatch,
) -> None:
    package = tmp_path / "environment" / "Lib" / "site-packages" / "kardboard_vtuber"
    monkeypatch.setattr(app_paths, "SOURCE_ROOT", None)
    monkeypatch.setattr(app_paths, "PACKAGE_ROOT", package)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user-data"))
    monkeypatch.setattr(app_paths.sys, "platform", "win32")
    args = cli.build_parser().parse_args([])
    assert args.face_model == tmp_path / "user-data" / "KardboardCode" / "Studio" / (
        "models"
    ) / "face_landmarker.task"
    assert app_paths.scripts_root() == package / "_tools"
    assert app_paths.recordings_root().is_relative_to(tmp_path / "user-data")


def test_installed_command_uses_private_python_and_safe_powershell_quoting(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(app_paths, "SOURCE_ROOT", None)
    monkeypatch.setattr(app_paths.sys, "executable", str(tmp_path / "user's env" / "pythonw.exe"))
    command = app_paths.command_prefix("kardboard_vtuber.video_cli")
    assert "user''s env" in command
    assert "python.exe' -I -m kardboard_vtuber.video_cli" in command
    assert ".venv312" not in command
