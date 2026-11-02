from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "installer" / "windows" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("windows_setup", BOOTSTRAP)
assert spec is not None and spec.loader is not None
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@pytest.fixture
def payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "installed"
    folder = root / "bootstrap"
    (folder / "wheels").mkdir(parents=True)
    requirements = b"example==1 --hash=sha256:example\n"
    wheel = b"application wheel bytes for payload verification"
    (folder / "requirements-windows.txt").write_bytes(requirements)
    (folder / "wheels" / "app.whl").write_bytes(wheel)
    manifest = {
        "schemaVersion": 1,
        "version": "1.1.1",
        "pythonVersion": platform.python_version(),
        "runtimeArchiveSha256": "test-runtime",
        "applicationWheel": "wheels/app.whl",
        "applicationSha256": hashlib.sha256(wheel).hexdigest(),
        "requirementsSha256": hashlib.sha256(requirements).hexdigest(),
    }
    (folder / "setup-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(setup, "data_home", lambda: tmp_path / "user-data")
    return root


@pytest.mark.parametrize("filename", ["requirements-windows.txt", "wheels/app.whl"])
def test_setup_refuses_modified_payload(payload: Path, filename: str) -> None:
    (payload / "bootstrap" / filename).write_bytes(b"modified")
    with pytest.raises(ValueError, match="checksum mismatch"):
        setup.Installation(payload)


def test_setup_refuses_payload_paths_outside_installation(payload: Path) -> None:
    installation = setup.Installation(payload)
    (payload / "outside.whl").write_bytes(b"not an installation payload")
    with pytest.raises(ValueError, match="invalid setup payload path"):
        installation.file("../outside.whl")


def test_setup_keeps_https_mirror_but_ignores_external_install_targets(
    payload: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = (
        "global.index-url='https://mirror.example/simple/'\n"
        "install.index-url='https://install.example/simple/'\n"
        ":env:.index-url='https://environment.example/simple/'\n"
        "global.target='external-directory'\n"
        "global.user='true'\n"
    )
    monkeypatch.setattr(setup.subprocess, "CREATE_NO_WINDOW", 0, raising=False)
    monkeypatch.setattr(
        setup.subprocess, "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=output),
    )
    monkeypatch.setenv("PIP_TARGET", "external-directory")
    monkeypatch.setenv("PIP_USER", "1")
    environment = setup.Installation(payload).package_environment()
    assert environment["PIP_INDEX_URL"] == "https://environment.example/simple/"
    assert environment["PIP_CONFIG_FILE"] == os.devnull
    assert "PIP_TARGET" not in environment and "PIP_USER" not in environment


@pytest.mark.parametrize("output", [
    "global.trusted-host='mirror.example'\n",
    "global.index-url='http://mirror.example/simple/'\n",
])
def test_setup_rejects_tls_bypass_configuration(
    payload: Path, monkeypatch: pytest.MonkeyPatch, output: str,
) -> None:
    monkeypatch.setattr(setup.subprocess, "CREATE_NO_WINDOW", 0, raising=False)
    monkeypatch.setattr(
        setup.subprocess, "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=output),
    )
    with pytest.raises(ValueError, match="TLS"):
        setup.Installation(payload).package_environment()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows byte-range setup lock")
def test_cancelled_and_failed_preparation_do_not_publish_ready(
    payload: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    installation = setup.Installation(payload)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(setup.SetupCancelled):
        installation.prepare(lambda line: None, cancel)
    assert not installation.marker.exists()
    cancel.clear()
    monkeypatch.setattr(setup.PrivateEnvironment, "create", lambda *args: None)
    monkeypatch.setattr(installation, "package_environment", lambda **kwargs: {})

    def fail(*args, **kwargs) -> None:
        raise RuntimeError("Simulated component download failure")

    monkeypatch.setattr(installation, "run", fail)
    with pytest.raises(RuntimeError, match="download failure"):
        installation.prepare(lambda line: None, cancel)
    assert not installation.marker.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows byte-range setup lock")
def test_setup_lock_rejects_concurrent_preparation_without_growing_file(payload: Path) -> None:
    installation = setup.Installation(payload)
    for _ in range(2):
        with installation.lock(), pytest.raises(RuntimeError, match="already running"):
            with installation.lock():
                pytest.fail("A concurrent setup acquired the same installation lock")
    lock = setup.data_home() / "setup-locks" / (installation.key + ".lock")
    assert lock.stat().st_size == 1


def test_headless_setup_failure_is_reported_without_opening_a_dialog() -> None:
    result = subprocess.run(
        [sys.executable, "-I", str(BOOTSTRAP), "--check"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "Component setup failed:" in result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows extended-length installation")
def test_private_prefix_installs_long_wheel_paths_without_system_changes(tmp_path: Path) -> None:
    wheel = tmp_path / "longpath_probe-1.0-py3-none-any.whl"
    member = "longpath_probe/" + "/".join(["long-component-name"] * 9) + "/payload.txt"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(member, b"verified long-path payload")
        archive.writestr(
            "longpath_probe-1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: longpath-probe\nVersion: 1.0\n",
        )
        archive.writestr(
            "longpath_probe-1.0.dist-info/WHEEL",
            "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr("longpath_probe-1.0.dist-info/RECORD", "")
    prefix = setup.extended_path(tmp_path / "private-prefix")
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().startswith("PIP_")
    }
    environment["PIP_CONFIG_FILE"] = os.devnull
    try:
        result = subprocess.run(
            [
                sys.executable, "-I", "-m", "pip", "install", "--no-index", "--no-deps",
                "--disable-pip-version-check", "--prefix", prefix, str(wheel),
            ],
            env=environment, capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        installed = Path(prefix) / "Lib" / "site-packages" / member
        assert len(str(installed)) > 260
        assert installed.read_bytes() == b"verified long-path payload"
    finally:
        if Path(prefix).exists():
            shutil.rmtree(prefix)


@pytest.mark.skipif(
    sys.platform != "win32" or sys.version_info[:2] != (3, 12),
    reason="Windows Python 3.12 build-only msilib",
)
def test_msi_owns_runtime_bytecode_directories_and_cancel_binding(tmp_path: Path) -> None:
    import msilib

    from scripts.build_windows_installer import author_msi

    image = tmp_path / "image"
    package = image / "runtime" / "Lib" / "example"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("value = 1\n", encoding="utf-8")
    (image / "runtime" / "pythonw.exe").write_bytes(b"synthetic build-only file")
    (image / "bootstrap").mkdir()
    shutil.copy2(
        ROOT / "src" / "kardboard_vtuber" / "gui" / "assets" / "kardboardcode-icon.ico",
        image / "bootstrap" / "kardboardcode.ico",
    )
    artifact = tmp_path / "setup.msi"
    author_msi(image, artifact)
    database = msilib.OpenDatabase(str(artifact), msilib.MSIDBOPEN_READONLY)
    folders = database.OpenView("SELECT `Directory_`, `Component_` FROM `CreateFolder`")
    folders.Execute(None)
    owned = []
    while row := folders.Fetch():
        if row.GetString(1).startswith("cache_"):
            owned.append((row.GetString(1), row.GetString(2)))
    assert len(owned) == 1
    directory, component = owned[0]
    assert component.startswith("cachecmp_")
    view = database.OpenView(
        f"SELECT `Directory_` FROM `Component` WHERE `Component`='{component}' "
        "AND `KeyPath` IS NULL",
    )
    view.Execute(None)
    row = view.Fetch()
    assert row is not None and row.GetString(1) == directory
    view = database.OpenView(
        "SELECT `Control_Cancel` FROM `Dialog` WHERE `Dialog`='WelcomeDlg'",
    )
    view.Execute(None)
    assert view.Fetch().GetString(1) == "Cancel"
