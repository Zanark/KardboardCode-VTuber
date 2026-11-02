"""Separate installed resources from writable per-user application data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
_candidate = PACKAGE_ROOT.parent.parent
SOURCE_ROOT = (
    _candidate
    if (_candidate / "pyproject.toml").is_file()
    and (_candidate / "src" / "kardboard_vtuber").resolve() == PACKAGE_ROOT
    else None
)
RESOURCE_ROOT = SOURCE_ROOT or PACKAGE_ROOT


def data_root() -> Path:
    if SOURCE_ROOT is not None:
        return SOURCE_ROOT
    if sys.platform == "win32":
        local = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return local / "KardboardCode" / "Studio"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "KardboardCode" / "Studio"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / (
        "kardboardcode-studio"
    )


def model_path(filename: str) -> Path:
    return (Path("models") if SOURCE_ROOT is not None else data_root() / "models") / filename


def scripts_root() -> Path:
    return SOURCE_ROOT / "scripts" if SOURCE_ROOT is not None else PACKAGE_ROOT / "_tools"


def recordings_root() -> Path:
    return data_root() / "recordings"


def command_prefix(module: str) -> str:
    if SOURCE_ROOT is not None:
        return rf".\.venv312\Scripts\python.exe -m {module}"
    executable = Path(sys.executable).with_name("python.exe")
    quoted = "'" + str(executable).replace("'", "''") + "'"
    return f"& {quoted} -I -m {module}"
