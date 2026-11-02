from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.export_release import ARCHIVE, check_export, export, snapshot


def command(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    command(tmp_path, "init", "-q")
    command(tmp_path, "config", "user.name", "Export Tests")
    command(tmp_path, "config", "user.email", "export-tests@example.invalid")
    for name, text in {
        ".gitattributes": "/release/** text eol=lf\n/release/*.zip -text\n",
        "pyproject.toml": '[project]\nname = "kardboard-vtuber"\nversion = "0.2.0"\n',
        "src/kardboard_vtuber/__init__.py": '__version__ = "0.2.0"\n',
        "scripts/example.py": 'print("source")\n',
        "README.md": "# Public source\n",
        "models/.gitkeep": "",
        "release/README.md": "Release staging\n",
        "release/RELEASE_NOTES.md": "# v0.2.0 - Studio\n\nSource release.\n",
        ".agent-context/STATE.md": "do-not-export-private-context",
        ".env": "do-not-export-local-credentials",
        "recordings/private.mp4": "do-not-export-raw-recording",
        "models/face.task": "do-not-export-model",
        ".venv/example.py": "do-not-export-environment",
    }.items():
        write(tmp_path, name, text)
    command(tmp_path, "add", ".")
    command(tmp_path, "commit", "-qm", "Initial public source and excluded fixtures")
    return tmp_path


def test_export_contains_public_source_only_and_is_repeatable(repository: Path) -> None:
    assert export(repository)
    folder = repository / "release"
    original = (folder / ARCHIVE).read_bytes()
    with zipfile.ZipFile(folder / ARCHIVE) as archive:
        names = archive.namelist()
        assert all(name.startswith("KardboardCode-VTuber-v0.2.0/") for name in names)
        assert any(name.endswith("/RELEASE_NOTES.md") for name in names)
        assert not any(
            part in name
            for name in names
            for part in (
                ".agent-context",
                ".env",
                "recordings",
                "face.task",
                ".venv",
            )
        )
        assert {
            name.removeprefix("KardboardCode-VTuber-v0.2.0/")
            for name in names
            if "/release/" in name
        } == {"release/README.md", "release/RELEASE_NOTES.md"}
        assert all(b"do-not-export" not in archive.read(name) for name in names)
    check_export(repository, snapshot(repository))
    command(repository, "add", ".")
    command(repository, "commit", "-qm", "Generated release files")
    for path in folder.iterdir():
        if path.is_file():
            name = path.relative_to(repository).as_posix()
            stored = subprocess.check_output(["git", "-C", str(repository), "show", "HEAD:" + name])
            assert stored == path.read_bytes()
    assert not export(repository)
    assert (folder / ARCHIVE).read_bytes() == original


def test_readme_change_is_detected_and_regenerated(repository: Path) -> None:
    export(repository)
    write(repository, "README.md", "# Updated documentation\n")
    with pytest.raises(ValueError, match="stale"):
        check_export(repository, snapshot(repository))
    assert export(repository)
    check_export(repository, snapshot(repository))
    manifest = json.loads((repository / "release" / "manifest.json").read_text())
    assert manifest["sourceModified"]
    command(repository, "add", "README.md")
    command(repository, "commit", "-qm", "Commit source documentation")
    with pytest.raises(ValueError, match="committed"):
        check_export(repository, snapshot(repository))
    assert export(repository)
    manifest = json.loads((repository / "release" / "manifest.json").read_text())
    assert not manifest["sourceModified"]
    assert manifest["sourceCommit"] == snapshot(repository).commit


def test_new_source_cannot_be_silently_omitted(repository: Path) -> None:
    write(repository, "src/kardboard_vtuber/new_feature.py", "FEATURE = True\n")
    with pytest.raises(ValueError, match="Stage new public source"):
        export(repository)
    command(repository, "add", "src/kardboard_vtuber/new_feature.py")
    assert export(repository)
    with zipfile.ZipFile(repository / "release" / ARCHIVE) as archive:
        assert any(name.endswith("/new_feature.py") for name in archive.namelist())


def test_modified_release_asset_fails_check_without_repairing_it(repository: Path) -> None:
    export(repository)
    context = repository / "release" / "RELEASE_CONTEXT.md"
    context.write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        check_export(repository, snapshot(repository))
    assert context.read_text() == "tampered"


def test_version_mismatch_is_rejected(repository: Path) -> None:
    write(repository, "src/kardboard_vtuber/__init__.py", '__version__ = "0.1.0"\n')
    with pytest.raises(ValueError, match="must match"):
        export(repository)
