"""Online component setup for the private Windows installation; no system Python changes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import venv
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit


class SetupCancelled(Exception):
    pass


class PrivateEnvironment(venv.EnvBuilder):
    def _call_new_python(self, context, *args, **kwargs):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return super()._call_new_python(context, *args, **kwargs)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def data_home() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "KardboardCode" / "Studio"


def extended_path(path: Path) -> str:
    name = str(path.resolve())
    if name.startswith("\\\\?\\"):
        return name
    return "\\\\?\\UNC\\" + name[2:] if name.startswith("\\\\") else "\\\\?\\" + name


class Installation:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.payload = self.root / "bootstrap"
        self.manifest = json.loads((self.payload / "setup-manifest.json").read_text("utf-8"))
        if self.manifest.get("schemaVersion") != 1:
            raise ValueError("Unsupported setup manifest.")
        if tuple(sys.version_info[:3]) != tuple(
            int(part) for part in self.manifest["pythonVersion"].split(".")
        ):
            raise ValueError("The private Python runtime does not match this setup.")
        self.requirements = self.file("requirements-windows.txt")
        self.wheel = self.file(self.manifest["applicationWheel"])
        for path, expected in (
            (self.requirements, self.manifest["requirementsSha256"]),
            (self.wheel, self.manifest["applicationSha256"]),
        ):
            if digest(path) != expected:
                raise ValueError(f"Setup payload checksum mismatch: {path.name}")
        identity = "|".join((
            str(self.root).casefold(), self.manifest["requirementsSha256"],
            self.manifest["applicationSha256"], self.manifest["runtimeArchiveSha256"],
        ))
        self.key = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        self.environment = data_home() / "runtimes" / self.key
        self.python = self.environment / "Scripts" / "python.exe"
        self.pythonw = self.environment / "Scripts" / "pythonw.exe"
        self.marker = self.environment / "kardboard-ready.json"

    def file(self, name: str) -> Path:
        path = (self.payload / name).resolve()
        if not path.is_relative_to(self.payload) or not path.is_file():
            raise ValueError("Missing or invalid setup payload path.")
        return path

    def ready(self) -> bool:
        if not self.marker.is_file() or not self.python.is_file() or not self.pythonw.is_file():
            return False
        data = json.loads(self.marker.read_text("utf-8"))
        return (
            data.get("schemaVersion") == 1
            and data.get("applicationSha256") == self.manifest["applicationSha256"]
            and data.get("requirementsSha256") == self.manifest["requirementsSha256"]
        )

    @contextmanager
    def lock(self) -> Iterator[None]:
        import msvcrt

        folder = data_home() / "setup-locks"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / (self.key + ".lock")).open("a+b") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError(
                    "Another component setup is already running. Wait for it to finish.",
                ) from error
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    def prepare(
        self, emit, cancel: threading.Event, *, wheelhouse: Path | None = None,
    ) -> None:
        with self.lock():
            if self.ready():
                emit("Application components are already ready.")
                return
            emit("Creating a private application environment. System Python/PATH are unchanged.")
            if cancel.is_set():
                raise SetupCancelled()
            PrivateEnvironment(with_pip=True, symlinks=False).create(self.environment)
            if cancel.is_set():
                raise SetupCancelled()
            environment = self.package_environment(network=wheelhouse is None)
            command = [
                str(self.python), "-I", "-m", "pip", "install",
                "--disable-pip-version-check", "--no-input", "--progress-bar", "off",
                "--require-hashes", "--only-binary=:all:", "--force-reinstall",
                "--prefix", extended_path(self.environment),
                "--cache-dir", str(data_home() / "download-cache"),
            ]
            if wheelhouse is None:
                emit("Using the default package index or your configured verified HTTPS mirror.")
            else:
                command += ["--no-index", "--find-links", str(wheelhouse)]
            self.run(
                command + ["-r", str(self.requirements)], emit, cancel, environment=environment,
            )
            emit("Installing the verified KardboardCode application.")
            self.run([
                str(self.python), "-I", "-m", "pip", "install",
                "--disable-pip-version-check", "--no-input", "--no-index",
                "--no-deps", "--force-reinstall", "--prefix", extended_path(self.environment),
                str(self.wheel),
            ], emit, cancel, environment=environment)
            emit("Checking application imports and packaged helpers. No camera is opened.")
            code = (
                "import av,cv2,mediapipe,moderngl;"
                "from PySide6 import QtWidgets;"
                "from kardboard_vtuber import __version__;"
                "from kardboard_vtuber.app_paths import scripts_root,SOURCE_ROOT;"
                "assert SOURCE_ROOT is None;"
                f"assert __version__=={self.manifest['version']!r};"
                f"assert all((scripts_root()/name).is_file()"
                f" for name in {self.manifest['helpers']!r});"
                "print('Application components verified.')"
            )
            self.run([str(self.python), "-I", "-c", code], emit, cancel)
            if cancel.is_set():
                raise SetupCancelled()
            temporary = self.marker.with_suffix(".tmp")
            temporary.write_text(json.dumps({
                "schemaVersion": 1, "version": self.manifest["version"],
                "applicationSha256": self.manifest["applicationSha256"],
                "requirementsSha256": self.manifest["requirementsSha256"],
            }, indent=2) + "\n", encoding="utf-8", newline="\n")
            temporary.replace(self.marker)
            emit("Ready. Models remain an explicit download in Studio.")

    def package_environment(self, *, network: bool = True) -> dict[str, str]:
        environment = {
            key: value for key, value in os.environ.items()
            if not key.upper().startswith("PIP_")
        }
        environment["PIP_CONFIG_FILE"] = os.devnull
        if not network:
            return environment
        result = subprocess.run(
            [str(self.python), "-I", "-m", "pip", "config", "list"],
            check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        options: dict[str, tuple[int, str]] = {}
        for line in result.stdout.splitlines():
            if "=" not in line:
                continue
            key, raw = line.split("=", 1)
            try:
                value = str(ast.literal_eval(raw))
            except (ValueError, SyntaxError) as error:
                raise ValueError("Could not read the package network configuration.") from error
            if "trusted-host" in key and value:
                raise ValueError(
                    "Package configuration bypasses TLS verification with trusted-host. "
                    "Use a correctly configured HTTPS package feed/certificate instead.",
                )
            scope, name = key.rsplit(".", 1)
            priority = {":env:": 2, "install": 1, "global": 0}.get(scope)
            if priority is None or name not in {
                "index-url", "extra-index-url", "cert", "client-cert", "proxy",
                "timeout", "retries",
            }:
                continue
            if "index-url" in name:
                for url in value.split():
                    if urlsplit(url).scheme.lower() != "https":
                        raise ValueError("Package setup requires HTTPS indexes with verified TLS.")
            if name not in options or priority >= options[name][0]:
                options[name] = (priority, value)
        for name, (_, value) in options.items():
            environment["PIP_" + name.upper().replace("-", "_")] = value
        return environment

    def run(
        self, command: list[str], emit, cancel: threading.Event,
        *, environment: dict[str, str] | None = None,
    ) -> None:
        lines: queue.Queue[str] = queue.Queue()
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW, env=environment,
        )

        def read() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                lines.put(line.rstrip())

        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        try:
            while process.poll() is None:
                while not lines.empty():
                    emit(re.sub(
                        r"https?://\S+", "[package source]", lines.get_nowait(),
                        flags=re.IGNORECASE,
                    ))
                if cancel.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise SetupCancelled()
                time.sleep(.1)
            reader.join(timeout=3)
            while not lines.empty():
                emit(re.sub(
                    r"https?://\S+", "[package source]", lines.get_nowait(), flags=re.IGNORECASE,
                ))
            if process.returncode:
                raise RuntimeError(
                    f"Component setup failed (exit {process.returncode}). "
                    "Check the connection and the detailed messages, then retry.",
                )
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if process.stdout is not None:
                process.stdout.close()

    def launch(self, argv: list[str]) -> None:
        if not self.ready():
            raise RuntimeError("Application components are not ready.")
        subprocess.Popen(
            [str(self.pythonw), "-I", "-m", "kardboard_vtuber.gui", *argv],
            cwd=data_home(), creationflags=subprocess.CREATE_NO_WINDOW,
        )


def wizard(installation: Installation, argv: list[str]) -> int:
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Tk()
    window.title("KardboardCode Studio / component setup")
    window.geometry("760x540")
    window.configure(background="#19332b")
    icon = installation.payload / "kardboardcode.ico"
    if icon.is_file():
        window.iconbitmap(str(icon))
    tk.Label(
        window, text="UNBOX YOUR STUDIO", bg="#19332b", fg="#fff4db",
        font=("Segoe UI", 23, "bold"),
    ).pack(anchor="w", padx=24, pady=(22, 10))
    tk.Label(
        window,
        text=(
            "Download verified application components from PyPI.\n"
            "Python is private to this app. Models and cameras are not started here.\n"
            "Internet is required for this step; keep the window open until it finishes."
        ),
        justify="left", bg="#19332b", fg="#c2cfb9", font=("Segoe UI", 11),
    ).pack(anchor="w", padx=24, pady=(0, 14))
    console = tk.Text(
        window, bg="#10251e", fg="#fff4db", font=("Consolas", 9),
        relief="flat", wrap="word", height=14,
    )
    console.pack(fill="both", expand=True, padx=24)
    progress = ttk.Progressbar(window, mode="indeterminate")
    progress.pack(fill="x", padx=24, pady=14)
    events: queue.Queue[tuple[str, str]] = queue.Queue()
    cancel = threading.Event()
    running = False
    outcome = 1

    def append(text: str) -> None:
        console.insert("end", text + "\n")
        if int(console.index("end-1c").split(".")[0]) > 350:
            console.delete("1.0", "50.0")
        console.see("end")

    def work() -> None:
        try:
            installation.prepare(lambda line: events.put(("log", line)), cancel)
        except SetupCancelled:
            events.put(("cancelled", "Setup cancelled. Download cache may be reused on retry."))
        except Exception as error:
            events.put(("error", str(error)))
        else:
            events.put(("ready", "Application components are ready."))

    def start() -> None:
        nonlocal running
        running = True
        cancel.clear()
        install.configure(state="disabled")
        progress.start(15)
        threading.Thread(target=work, daemon=True).start()

    def close() -> None:
        if running:
            if messagebox.askyesno("Cancel setup?", "Stop the owned component setup process?"):
                cancel.set()
                append("Cancelling; waiting for the owned process to stop...")
            return
        window.destroy()

    buttons = tk.Frame(window, bg="#19332b")
    buttons.pack(fill="x", padx=24, pady=(0, 22))
    install = tk.Button(
        buttons, text="Install components", command=start, bg="#d5a568", fg="#19332b",
        relief="flat", padx=18, pady=8,
    )
    install.pack(side="left")
    tk.Button(buttons, text="Cancel / close", command=close, padx=16, pady=8).pack(side="right")

    def poll() -> None:
        nonlocal running, outcome
        while not events.empty():
            kind, text = events.get_nowait()
            append(text)
            if kind in {"ready", "error", "cancelled"}:
                running = False
                progress.stop()
                install.configure(state="normal", text="Retry component setup")
                if kind == "ready":
                    outcome = 0
                    installation.launch(argv)
                    window.destroy()
                    return
                if kind == "error":
                    messagebox.showerror("Component setup did not finish", text)
        window.after(100, poll)

    window.protocol("WM_DELETE_WINDOW", close)
    window.after(100, poll)
    window.mainloop()
    return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--wheelhouse", type=Path)
    args, application_args = parser.parse_known_args(argv)
    installation = Installation(Path(__file__).resolve().parent.parent)
    if args.check:
        print(json.dumps({
            "ready": installation.ready(), "version": installation.manifest["version"],
        }))
        return 0 if installation.ready() else 1
    if args.prepare_only:
        installation.prepare(print, threading.Event(), wheelhouse=args.wheelhouse)
        return 0
    if installation.ready():
        installation.launch(application_args)
        return 0
    return wizard(installation, application_args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        if "--prepare-only" in sys.argv or "--check" in sys.argv:
            print(f"Component setup failed: {error}", file=sys.stderr)
            raise SystemExit(1) from error
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None, f"Studio setup could not start:\n{error}", "KardboardCode Studio", 0x10,
        )
        raise SystemExit(1) from error
