"""Build/check the per-user Windows x64 online MSI without changing system Python."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import struct
import subprocess
import sys
import tarfile
import tomllib
import urllib.request
import uuid
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "installer" / "windows"
BUILD = ROOT / "build" / "windows"
RELEASE = ROOT / "release"
SETUP = "KardboardCode-Studio-windows-x64.msi"
RECEIPT = "installer-manifest.json"
SUMS = "INSTALLER_SHA256SUMS.txt"
NAMESPACE = uuid.UUID("5850fa62-b48b-542b-ac2d-751448765ac0")
HELPERS = (
    "download_face_landmarker_model.py", "download_hand_landmarker_model.py",
    "download_pose_landmarker_model.py", "download_selfie_segmenter_model.py",
    "list_local_cameras.py", "record_guided_regression.py",
)


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def project() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def declarations() -> list[str]:
    data = project()
    return data["dependencies"] + [
        item for extra in ("gui", "tracking", "virtual-camera")
        for item in data["optional-dependencies"][extra]
    ]


def fingerprint() -> str:
    files = [ROOT / "pyproject.toml", ROOT / "README.md", Path(__file__)]
    files += [
        path for path in (ROOT / "src" / "kardboard_vtuber").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    files += [ROOT / "scripts" / name for name in HELPERS]
    files += [path for path in CONFIG.iterdir() if path.is_file()]
    value = hashlib.sha256()
    for path in sorted(set(files)):
        value.update(
            path.relative_to(ROOT).as_posix().encode() + b"\0" + sha(path).encode() + b"\n",
        )
    return value.hexdigest()


def run(command: list[str], **kwargs) -> None:
    print("Running:", command[0], " ".join(command[1:4]), flush=True)
    subprocess.run(command, check=True, **kwargs)


def runtime() -> Path:
    data = json.loads((CONFIG / "python-runtime.json").read_text(encoding="utf-8"))
    BUILD.mkdir(parents=True, exist_ok=True)
    archive = BUILD / "cpython-3.12.16-windows-x64.tar.gz"
    if not archive.is_file():
        print("Downloading pinned private Python runtime...", flush=True)
        urllib.request.urlretrieve(data["url"], archive)
    if sha(archive) != data["sha256"]:
        raise ValueError("Private Python runtime archive checksum mismatch.")
    folder = BUILD / "runtime"
    executable = folder / "python" / "python.exe"
    if not executable.is_file():
        folder.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as source:
            source.extractall(folder, filter="data")
    version = subprocess.check_output(
        [str(executable), "-I", "-c", "import platform;print(platform.python_version())"],
        text=True,
    ).strip()
    if version != data["version"]:
        raise ValueError("Extracted Python version does not match the pinned runtime.")
    try:
        subprocess.run(
            [str(executable), "-I", "-m", "pip", "--version"], check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        run([str(executable), "-I", "-m", "ensurepip"])
    return executable


def resolve_versions() -> dict[str, str]:
    pending = [Requirement(text) for text in declarations()]
    versions: dict[str, str] = {}
    seen_extras: set[tuple[str, tuple[str, ...]]] = set()
    while pending:
        requirement = pending.pop()
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        distribution = importlib.metadata.distribution(requirement.name)
        name = distribution.metadata["Name"]
        if distribution.version not in requirement.specifier:
            raise ValueError(f"Installed {name} {distribution.version} violates {requirement}.")
        versions[name] = distribution.version
        extras = tuple(sorted(requirement.extras))
        identity = (name.lower(), extras)
        if identity in seen_extras:
            continue
        seen_extras.add(identity)
        for text in distribution.requires or ():
            child = Requirement(text)
            if not child.marker or any(
                child.marker.evaluate({"extra": extra}) for extra in ("", *extras)
            ):
                child.marker = None
                pending.append(child)
    return versions


def update_lock() -> None:
    versions = resolve_versions()
    pins = BUILD / "runtime-pins.txt"
    pins.write_text(
        "".join(f"{name}=={version}\n" for name, version in sorted(versions.items())),
        encoding="utf-8", newline="\n",
    )
    wheels = BUILD / "wheelhouse"
    wheels.mkdir(exist_ok=True)
    run([
        sys.executable, "-I", "-m", "pip", "download", "--disable-pip-version-check",
        "--only-binary=:all:", "--no-deps",
        "-r", str(pins), "--dest", str(wheels),
    ])
    import email.parser
    import zipfile

    locked = {}
    for wheel in sorted(wheels.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            metadata = [
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata) != 1:
                raise ValueError("Invalid wheel metadata.")
            message = email.parser.Parser().parsestr(archive.read(metadata[0]).decode("utf-8"))
        name, version = message["Name"], message["Version"]
        if name not in versions or versions[name] != version:
            continue
        if name in locked:
            raise ValueError(f"Multiple wheel candidates for {name}; use a clean owned wheelhouse.")
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json") as response:
            published = json.load(response)
        expected = next(
            (item["digests"]["sha256"] for item in published["urls"]
             if item["filename"] == wheel.name), None,
        )
        if expected != sha(wheel):
            raise ValueError(f"The {name} wheel differs from its authoritative PyPI hash.")
        locked[name] = {"version": version, "filename": wheel.name, "sha256": sha(wheel)}
    if set(locked) != set(versions):
        raise ValueError("Downloaded wheels do not cover the complete dependency closure.")
    (CONFIG / "requirements-lock.json").write_text(json.dumps({
        "schemaVersion": 1, "python": "3.12", "platform": "win_amd64",
        "declarations": declarations(), "packages": locked,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (CONFIG / "requirements-windows.txt").write_text(
        "".join(
            f"{name}=={entry['version']} --hash=sha256:{entry['sha256']}\n"
            for name, entry in sorted(locked.items())
        ), encoding="utf-8", newline="\n",
    )
    print(f"Locked {len(locked)} original upstream wheels with SHA-256.")


def prepare_image(python: Path) -> Path:
    lock = json.loads((CONFIG / "requirements-lock.json").read_text(encoding="utf-8"))
    if lock["declarations"] != declarations():
        raise ValueError("Runtime dependency declarations changed. Re-run --update-lock.")
    wheel_folder = BUILD / "app-wheel"
    wheel_folder.mkdir(exist_ok=True)
    run([
        sys.executable, "-I", "-m", "pip", "wheel", "--disable-pip-version-check",
        "--no-deps", "--wheel-dir", str(wheel_folder),
        str(ROOT),
    ])
    version = project()["version"]
    wheels = list(wheel_folder.glob(f"kardboard_vtuber-{version}-*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected exactly one application wheel.")
    image = BUILD / "image"
    if image.exists():
        marker = image / ".kardboard-owned-build"
        if not marker.is_file() or marker.read_text() != str(ROOT):
            raise ValueError("Refusing to replace an unrecognized installer image directory.")
        shutil.rmtree(image)
    image.mkdir()
    (image / ".kardboard-owned-build").write_text(str(ROOT))
    shutil.copytree(
        python.parent, image / "runtime",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    payload = image / "bootstrap"
    (payload / "wheels").mkdir(parents=True)
    for name in ("bootstrap.py", "requirements-windows.txt"):
        shutil.copy2(CONFIG / name, payload / name)
    shutil.copy2(wheels[0], payload / "wheels" / wheels[0].name)
    shutil.copy2(
        ROOT / "src" / "kardboard_vtuber" / "gui" / "assets" / "kardboardcode-icon.ico",
        payload / "kardboardcode.ico",
    )
    pin = json.loads((CONFIG / "python-runtime.json").read_text(encoding="utf-8"))
    manifest = {
        "schemaVersion": 1, "version": version, "pythonVersion": pin["version"],
        "runtimeArchiveSha256": pin["sha256"],
        "applicationWheel": "wheels/" + wheels[0].name,
        "applicationSha256": sha(wheels[0]),
        "requirementsSha256": sha(payload / "requirements-windows.txt"),
        "helpers": list(HELPERS),
    }
    (payload / "setup-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n",
    )
    (payload / "README.txt").write_text(
        "KardboardCode Studio Windows setup\n\n"
        "This per-user installer includes private Python. First launch offers hash-verified\n"
        "downloads from PyPI or your configured HTTPS mirror, then starts Studio.\n"
        "No manual Python/pip or PATH changes. TLS verification is never disabled.\n"
        "AI models remain explicit downloads in Models; OBS's camera component is separate.\n"
        "Uninstall removes installed files, not private app data/models/presets/recordings.\n"
        "Original upstream components retain their licenses in the installed environment.\n",
        encoding="utf-8", newline="\n",
    )
    return image


def guid(name: str) -> str:
    return "{" + str(uuid.uuid5(NAMESPACE, name)).upper() + "}"


def author_msi(image: Path, destination: Path) -> dict[str, str]:
    import msilib
    from msilib import schema, sequence

    version = project()["version"]
    product_code = guid("product/" + version)
    upgrade_code = guid("upgrade/windows-x64")
    database = msilib.init_database(
        str(destination), schema, "KardboardCode Studio", product_code, version, "KardboardCode",
    )
    msilib.add_tables(database, sequence)
    msilib.add_data(database, "Property", [
        ("UpgradeCode", upgrade_code), ("ARPPRODUCTICON", "KardboardIcon"),
        ("ARPNOMODIFY", "1"),
        ("ARPURLINFOABOUT", "https://github.com/Zanark/KardboardCode-VTuber"),
        ("SecureCustomProperties", "OLDPRODUCTS;NEWERPRODUCT"),
        ("DefaultUIFont", "BodyFont"), ("ErrorDialog", "ErrorDlg"),
    ])
    msilib.add_data(database, "TextStyle", [
        ("BodyFont", "Segoe UI", 9, None, 0), ("TitleFont", "Segoe UI", 18, 2839321, 1),
    ])
    msilib.add_data(database, "LaunchCondition", [
        ("VersionNT64", "This setup requires 64-bit Windows 10/11."),
        ("NOT ALLUSERS", "This installer is per-user. Do not set ALLUSERS."),
        ("NOT NEWERPRODUCT", "A newer KardboardCode Studio is already installed."),
    ])
    msilib.add_data(database, "Upgrade", [
        (upgrade_code, None, version, None, 512, None, "OLDPRODUCTS"),
        (upgrade_code, version, None, None, 2, None, "NEWERPRODUCT"),
    ])
    for table in ("InstallUISequence", "InstallExecuteSequence"):
        database.OpenView(
            f"UPDATE `{table}` SET `Sequence`=300 WHERE `Action`='LaunchConditions'",
        ).Execute(None)
    database.OpenView(
        "UPDATE `InstallExecuteSequence` SET `Sequence`=1501 "
        "WHERE `Action`='RemoveExistingProducts'",
    ).Execute(None)
    summary = database.GetSummaryInformation(20)
    summary.SetProperty(msilib.PID_WORDCOUNT, 10)
    summary.Persist()
    cabinet = msilib.CAB("KardboardPayload")
    feature = msilib.Feature(
        database, "Studio", "KardboardCode Studio",
        "Private Python, application and verified online component setup", 1, 1,
    )
    feature.set_current()
    target = msilib.Directory(database, cabinet, None, str(image), "TARGETDIR", "SourceDir")
    local = msilib.Directory(database, cabinet, target, ".", "LocalAppDataFolder", ".")
    programs = msilib.Directory(database, cabinet, local, ".", "ProgramsFolder", "Programs")
    company = msilib.Directory(database, cabinet, programs, ".", "CompanyFolder", "KardboardCode")
    install = msilib.Directory(database, cabinet, company, ".", "INSTALLDIR", "Studio")
    directories = {Path(): install}
    file_ids = {}
    python_directories = set()
    for file in sorted(image.rglob("*")):
        if not file.is_file() or file.name == ".kardboard-owned-build":
            continue
        relative = file.relative_to(image)
        parent = Path()
        for segment in relative.parent.parts:
            child = parent / segment
            if child not in directories:
                identity = hashlib.sha256(str(child).encode()).hexdigest()[:20]
                directories[child] = msilib.Directory(
                    database, cabinet, directories[parent], segment, "dir_" + identity, segment,
                )
            parent = child
        identity = hashlib.sha256(relative.as_posix().encode()).hexdigest()[:24]
        directory = directories[relative.parent]
        directory.start_component(
            "cmp_" + identity, feature=feature, flags=0, keyfile=file.name,
            uuid=guid("component/" + relative.as_posix()),
        )
        file_ids[relative.as_posix()] = (
            directory.add_file(file.name), directory.component,
        )
        if file.suffix == ".py":
            python_directories.add(relative.parent)
    # Python may create bytecode after installation; own only its named cache directories.
    for parent in sorted(python_directories):
        identity = hashlib.sha256(parent.as_posix().encode()).hexdigest()[:20]
        cache = msilib.Directory(
            database, cabinet, directories[parent], "__pycache__",
            "cache_" + identity, "__pycache__",
        )
        cache.start_component(
            "cachecmp_" + identity, feature=feature, flags=0,
            uuid=guid("bytecode-cache/" + parent.as_posix()),
        )
        msilib.add_data(database, "CreateFolder", [(cache.logical, cache.component)])
        msilib.add_data(database, "RemoveFile", [
            ("clear_" + identity, cache.component, "*.pyc", cache.logical, 2),
        ])
    menu = msilib.Directory(database, cabinet, target, ".", "ProgramMenuFolder", ".")
    app_menu = msilib.Directory(
        database, cabinet, menu, ".", "StudioMenu", "KARDBO~1|KardboardCode Studio",
    )
    executable, component = file_ids["runtime/pythonw.exe"]
    msilib.add_data(database, "Icon", [
        ("KardboardIcon", msilib.Binary(str(image / "bootstrap" / "kardboardcode.ico"))),
    ])
    msilib.add_data(database, "Shortcut", [(
        "StudioShortcut", app_menu.logical, "KARDBO~1|KardboardCode Studio", component,
        f"[#{executable}]", '-I "[INSTALLDIR]bootstrap\\bootstrap.py"',
        "Launch Studio; first launch offers online component setup", None,
        "KardboardIcon", 0, 1, "INSTALLDIR",
    )])
    msilib.add_data(database, "CreateFolder", [(app_menu.logical, component)])
    msilib.add_data(database, "RemoveFile", [
        ("RemoveStudioMenu", component, None, app_menu.logical, 2),
    ])
    dialogs(database)
    cabinet.commit(database)
    database.Commit()
    del database
    return {"productCode": product_code, "upgradeCode": upgrade_code}


def dialogs(database) -> None:
    import msilib

    for name, title, content in (
        ("WelcomeDlg", "Install KardboardCode Studio",
         "Installs a private Python runtime and Start-menu launch.\n\n"
         "First launch downloads hash-verified components from PyPI or your HTTPS mirror. "
         "No manual Python/pip is needed. Models and cameras do not start here.\n\n"
         "Destination: [INSTALLDIR]\n\n"
         "Uninstall preserves private app data. This package is unsigned."),
        ("ExitDialog", "Setup completed",
         "Installation or removal has completed.\n\n"
         "After installation, open KardboardCode Studio from the Start menu.\n\n"
         "On first launch, choose Install components and keep the setup window open. "
         "Studio then opens without camera capture.\n\n"
         "Uninstall preserves private app data. Models and OBS's camera component are separate."),
        ("FatalError", "Setup could not complete",
         "The installer could not finish. Check the Windows Installer error/log and retry."),
        ("UserExit", "Setup cancelled", "No further installation actions will be performed."),
    ):
        dialog = msilib.Dialog(
            database, name, 50, 50, 390, 285, 3, "[ProductName] Setup", "Next", "Next",
            "Cancel" if name == "WelcomeDlg" else "Next",
        )
        dialog.text("Heading", 20, 18, 350, 38, 3, "{\\TitleFont}" + title)
        dialog.text("Description", 22, 75, 345, 160, 3, content)
        dialog.line("Rule", 15, 245, 360, 1)
        button = dialog.pushbutton(
            "Next", 290, 255, 75, 18, 3, "Install" if name == "WelcomeDlg" else "Finish", None,
        )
        button.event("EndDialog", "Return")
        if name == "WelcomeDlg":
            cancel = dialog.pushbutton("Cancel", 205, 255, 75, 18, 3, "Cancel", "Next")
            cancel.event("EndDialog", "Exit")
    progress = msilib.Dialog(
        database, "ProgressDlg", 50, 50, 390, 210, 1, "[ProductName] Setup",
        "Cancel", "Cancel", "Cancel",
    )
    progress.text("Heading", 20, 18, 350, 35, 3, "{\\TitleFont}Updating Studio")
    progress.text("Status", 22, 75, 345, 32, 3, "Applying the requested installation/removal...")
    progress.control("Progress", "ProgressBar", 22, 120, 345, 18, 65537, None, None, None, None)
    progress.pushbutton("Cancel", 290, 175, 75, 18, 3, "Cancel", None).event("EndDialog", "Exit")
    msilib.add_data(database, "EventMapping", [
        ("ProgressDlg", "Progress", "SetProgress", "Progress"),
        ("ProgressDlg", "Status", "ActionText", "Text"),
    ])
    error = msilib.Dialog(
        database, "ErrorDlg", 50, 50, 390, 180, 65543, "[ProductName] Setup",
        "OK", "OK", "OK",
    )
    error.text("ErrorText", 20, 20, 350, 110, 3, "[ErrorText]")
    error.pushbutton("OK", 300, 145, 65, 18, 3, "OK", None).event("EndDialog", "Return")
    msilib.add_data(database, "InstallUISequence", [
        ("WelcomeDlg", "NOT Installed", 1230),
        ("ProgressDlg", None, 1280),
    ])


def write_receipt(details: dict[str, str]) -> None:
    artifact = RELEASE / SETUP
    data = {
        "schemaVersion": 1, "version": project()["version"], "platform": "windows-x64",
        "type": "online-per-user-msi", "signed": False,
        "runtimeInputFingerprint": fingerprint(),
        "sourceCommit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
        ).strip(),
        "sourceModified": bool(subprocess.check_output(
            ["git", "-C", str(ROOT), "diff", "HEAD", "--name-only", "--",
             "src", "installer", "scripts/build_windows_installer.py",
             "pyproject.toml", "README.md"],
        ).strip()),
        "artifact": {"name": SETUP, "bytes": artifact.stat().st_size, "sha256": sha(artifact)},
        "pythonVersion": "3.12.16", **details,
    }
    (RELEASE / RECEIPT).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    (RELEASE / SUMS).write_text(
        f"{sha(artifact)}  {SETUP}\n{sha(RELEASE / RECEIPT)}  {RECEIPT}\n",
        encoding="utf-8", newline="\n",
    )


def check() -> None:
    data = json.loads((RELEASE / RECEIPT).read_text(encoding="utf-8"))
    artifact = RELEASE / SETUP
    if data["version"] != project()["version"] or data["runtimeInputFingerprint"] != fingerprint():
        raise ValueError("Windows setup is stale; rebuild it from current runtime inputs.")
    expected_artifact = {"name": SETUP, "bytes": artifact.stat().st_size, "sha256": sha(artifact)}
    if data["artifact"] != expected_artifact:
        raise ValueError("Windows setup checksum/size does not match its manifest.")
    expected = f"{sha(artifact)}  {SETUP}\n{sha(RELEASE / RECEIPT)}  {RECEIPT}\n"
    if (RELEASE / SUMS).read_text(encoding="utf-8") != expected:
        raise ValueError("Installer checksum file is stale.")
    print("Windows setup is current:", artifact)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-lock", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh-provenance", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
        return 0
    if (
        sys.platform != "win32" or sys.version_info[:2] != (3, 12)
        or struct.calcsize("P") != 8
    ):
        parser.error(
            "Build with Windows x64 Python 3.12 (msilib is a build-only stdlib dependency).",
        )
    if args.refresh_provenance:
        check()
        previous = json.loads((RELEASE / RECEIPT).read_text(encoding="utf-8"))
        write_receipt({name: previous[name] for name in ("productCode", "upgradeCode")})
        check()
        return 0
    python = runtime()
    if args.update_lock:
        update_lock()
    image = prepare_image(python)
    RELEASE.mkdir(exist_ok=True)
    destination = BUILD / SETUP
    details = author_msi(image, destination)
    shutil.copy2(destination, RELEASE / SETUP)
    write_receipt(details)
    check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
