"""Export the latest public tracked source and release handoff; no publishing side effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import tomllib
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ARCHIVE = "KardboardCode-VTuber-source.zip"
GENERATED = (ARCHIVE, "RELEASE_CONTEXT.md", "manifest.json", "SHA256SUMS.txt")
PRIVATE_PARTS = frozenset(
    {
        ".git",
        ".agent-context",
        ".zmem",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
        "node_modules",
        "recordings",
        "captures",
        "logs",
        "ytscript",
        "release",
        "dist",
        "venv",
        "env",
        ".idea",
        ".vscode",
    }
)


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    version: str
    commit: str
    branch: str
    modified: bool
    files: dict[str, bytes]
    fingerprint: str


def git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Release export needs a Git checkout and tracked source files: "
            + error.stderr.decode("utf-8", errors="replace").strip(),
        ) from error


def eligible(name: str) -> bool:
    path = PurePosixPath(name)
    parts = tuple(part.lower() for part in path.parts)
    if path.is_absolute() or ".." in parts:
        return False
    if parts[0] == "release":
        return str(path).lower() in {"release/readme.md", "release/release_notes.md"}
    if any(part in PRIVATE_PARTS or part.startswith(".venv") for part in parts):
        return False
    filename = parts[-1]
    if filename.startswith(".env") and filename != ".env.example":
        return False
    if filename == "config.local.toml" or path.suffix.lower() in {".pyc", ".pyo", ".log"}:
        return False
    if parts[0] == "models" and filename != ".gitkeep":
        return False
    if "build" in parts:
        return parts[:3] == ("docs", "book", "build") and (
            path.suffix == ".js" or filename == "package.json"
        )
    return True


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path) -> SourceSnapshot:
    untracked = [
        name
        for name in git(root, "ls-files", "--others", "--exclude-standard", "-z")
        .decode("utf-8")
        .split("\0")
        if name and eligible(name)
    ]
    if untracked:
        raise ValueError(
            "Stage new public source files before exporting: " + ", ".join(sorted(untracked)),
        )
    files = {}
    names = git(root, "ls-files", "--cached", "-z").decode("utf-8").split("\0")
    for name in sorted(set(names)):
        if not name or not eligible(name):
            continue
        path = root / Path(name)
        if path.is_symlink():
            raise ValueError(f"Source symlinks are not supported in release exports: {name}")
        if not path.is_file():
            raise ValueError(f"Tracked source is missing: {name}; stage its deletion first")
        files[name] = path.read_bytes()
    if "pyproject.toml" not in files or "src/kardboard_vtuber/__init__.py" not in files:
        raise ValueError("This is not a complete KardboardCode source checkout")
    version = tomllib.loads(files["pyproject.toml"].decode("utf-8"))["project"]["version"]
    package_version = re.search(
        r'^__version__ = "([^"]+)"',
        files["src/kardboard_vtuber/__init__.py"].decode("utf-8"),
        re.MULTILINE,
    )
    if package_version is None or package_version[1] != version:
        raise ValueError("Package __version__ and pyproject.toml version must match")
    if "release/RELEASE_NOTES.md" not in files:
        raise ValueError("Stage release/RELEASE_NOTES.md before exporting")
    notes_data = files["release/RELEASE_NOTES.md"]
    text = notes_data.decode("utf-8")
    if not text.startswith(f"# v{version} "):
        raise ValueError("Release notes heading must match the current package version")
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        digest.update(name.encode("utf-8") + b"\0" + sha256(data).encode("ascii") + b"\n")
    changes = set(git(root, "diff", "HEAD", "--name-only", "-z").decode("utf-8").split("\0"))
    modified = any(eligible(name) for name in changes if name)
    return SourceSnapshot(
        version,
        git(root, "rev-parse", "HEAD").decode().strip(),
        git(root, "branch", "--show-current").decode().strip(),
        modified,
        files,
        digest.hexdigest(),
    )


def check_export(root: Path, source: SourceSnapshot) -> None:
    folder = root / "release"
    for name in GENERATED:
        if not (folder / name).is_file():
            raise ValueError("Release export is missing; run python scripts\\export_release.py")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("schemaVersion") != 1
        or manifest.get("version") != source.version
        or manifest.get("sourceFingerprint") != source.fingerprint
    ):
        raise ValueError("Release export is stale; run python scripts\\export_release.py")
    if (
        manifest.get("sourceModified") is True
        and not source.modified
        and manifest.get("sourceCommit") != source.commit
    ):
        raise ValueError("Source changes are now committed; regenerate release provenance")
    expected = {
        name: {"bytes": len(data), "sha256": sha256(data)}
        for name, data in sorted(source.files.items())
    }
    if manifest.get("sourceFiles") != expected:
        raise ValueError("Release manifest source inventory does not match the current source")
    payloads = {
        name: (folder / name).read_bytes()
        for name in (ARCHIVE, "RELEASE_NOTES.md", "RELEASE_CONTEXT.md")
    }
    if manifest.get("assets") != {
        name: {"bytes": len(data), "sha256": sha256(data)}
        for name, data in sorted(payloads.items())
    }:
        raise ValueError("Release asset checksum mismatch; regenerate the export")
    checksum_payloads = dict(payloads, **{"manifest.json": (folder / "manifest.json").read_bytes()})
    sums = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(checksum_payloads.items()))
    if (folder / "SHA256SUMS.txt").read_text(encoding="utf-8") != sums:
        raise ValueError("SHA256SUMS does not match the release assets")
    prefix = f"KardboardCode-VTuber-v{source.version}/"
    with zipfile.ZipFile(folder / ARCHIVE) as archive:
        if archive.testzip() is not None:
            raise ValueError("Release archive failed its CRC check")
        if set(archive.namelist()) != {prefix + name for name in source.files}:
            raise ValueError("Release archive contents do not match the source inventory")
        for name, data in source.files.items():
            if archive.read(prefix + name) != data:
                raise ValueError(f"Release archive contains outdated source: {name}")


def export(root: Path) -> bool:
    source = snapshot(root)
    folder = root / "release"
    if all((folder / name).is_file() for name in GENERATED):
        try:
            check_export(root, source)
        except ValueError as error:
            print(f"Regenerating release export: {error}")
        else:
            print("Release export already matches the current source.")
            return False
    folder.mkdir(exist_ok=True)
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    context = (
        f"# v{source.version} release context\n\n"
        f"- Tag: `v{source.version}`\n"
        f"- Source commit: `{source.commit}`\n"
        f"- Source branch: `{source.branch}`\n"
        f"- Included source differs from that commit: `{source.modified}`\n"
        f"- Public source SHA-256 fingerprint: `{source.fingerprint}`\n"
        f"- Generated (UTC): `{generated_at}`\n"
        f"- Source files: `{len(source.files)}`\n\n"
        "## Packaging scope\n\n"
        "This is a source release, not a standalone Windows app or installer. Extract its "
        "top-level folder, create a Python 3.12 environment, install "
        "`.[tracking,virtual-camera,gui]` in editable mode, then run "
        "`python -m kardboard_vtuber.gui`. Use Models to download official models explicitly.\n\n"
        "Includes public tracked code, scripts, tests, assets and documentation plus release "
        "notes. Excludes Git internals, generated release artifacts, private agent context, local "
        "credentials/config, environments, recordings/captures, caches and downloaded models.\n\n"
        "## Publishing checklist\n\n"
        "1. Verify `python scripts\\export_release.py --check`.\n"
        "2. Push the intended source branch/commit using an authorized account. The source "
        "must first be committed and re-exported if sourceModified is true. The source "
        "commit above identifies export inputs; a later commit may contain only generated "
        "release/context files. The source fingerprint is the content-level freshness check.\n"
        "3. Create the tag against this source or its merged equivalent, not an older main.\n"
        "4. Paste RELEASE_NOTES.md and upload the ZIP, manifest and checksums from this folder.\n"
        "5. Keep published release assets immutable; later exports are separate snapshots.\n\n"
        "No publishing, pushing, merging, camera capture or model download is performed by "
        "this exporter. Known limitations and setup requirements are in RELEASE_NOTES.md.\n"
    ).encode()
    with tempfile.TemporaryDirectory(prefix=".export-", dir=folder) as directory:
        staging = Path(directory)
        with zipfile.ZipFile(
            staging / ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name, data in sorted(source.files.items()):
                info = zipfile.ZipInfo(f"KardboardCode-VTuber-v{source.version}/{name}")
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data, compresslevel=9)
        if (staging / ARCHIVE).stat().st_size >= 100 * 1024 * 1024:
            raise ValueError("Source archive exceeds GitHub's regular Git file-size limit")
        payloads = {
            ARCHIVE: (staging / ARCHIVE).read_bytes(),
            "RELEASE_NOTES.md": source.files["release/RELEASE_NOTES.md"],
            "RELEASE_CONTEXT.md": context,
        }
        manifest = {
            "schemaVersion": 1,
            "version": source.version,
            "tag": f"v{source.version}",
            "generatedAt": generated_at,
            "sourceCommit": source.commit,
            "sourceBranch": source.branch,
            "sourceModified": source.modified,
            "sourceFingerprint": source.fingerprint,
            "sourceFiles": {
                name: {"bytes": len(data), "sha256": sha256(data)}
                for name, data in sorted(source.files.items())
            },
            "assets": {
                name: {"bytes": len(data), "sha256": sha256(data)}
                for name, data in sorted(payloads.items())
            },
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (staging / "RELEASE_CONTEXT.md").write_bytes(context)
        checksum_payloads = dict(
            payloads,
            **{"manifest.json": (staging / "manifest.json").read_bytes()},
        )
        (staging / "SHA256SUMS.txt").write_text(
            "".join(
                f"{sha256(data)}  {name}\n" for name, data in sorted(checksum_payloads.items())
            ),
            encoding="utf-8",
        )
        if snapshot(root).fingerprint != source.fingerprint:
            raise ValueError("Source changed during export; retry after edits finish")
        for name in GENERATED:
            (staging / name).replace(folder / name)
    check_export(root, source)
    print(f"Exported v{source.version}: {folder / ARCHIVE}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without modifying exports.")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        if args.check:
            source = snapshot(root)
            check_export(root, source)
            print(f"Release export is current: v{source.version}, {source.fingerprint}")
        else:
            export(root)
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Release export failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
