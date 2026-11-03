# Repository release staging

- Keep the tracked `release` folder current with the latest public source export after code,
  configuration, tests, assets, or documentation changes.
- Stage new public source files first, then run:
  `python scripts\export_release.py`
- Verify freshness before handing off changes:
  `python scripts\export_release.py --check`
- The ZIP remains source-only. The separately generated online per-user Windows x64 MSI
  includes patched private Python and the application wheel; first launch downloads locked
  dependencies. Keep its explicit model/OBS prerequisites and unsigned status clear.
- After installed runtime inputs change, build with Windows x64 Python 3.12:
  `.\.venv312\Scripts\python.exe scripts\build_windows_installer.py`
  Verify with `--check`. Update the lock only intentionally using `--update-lock` from a
  compatible environment; each downloaded wheel must match authoritative PyPI hashes.
- Commit public runtime inputs before finalizing provenance. After that commit, use
  `--refresh-provenance` only if the runtime fingerprint and MSI hash remain unchanged.
  Keep installer receipt/checksums separate from the source ZIP manifest/checksums.
- Never export `.agent-context`, credentials/local environment files, raw recordings/captures,
  downloaded models, development environments, caches, Git internals, or generated artifacts
  inside the source archive. Only the MSI intentionally redistributes its pinned private runtime.
- Update `release\RELEASE_NOTES.md` when preparing a new version. Keep its version aligned with
  `pyproject.toml` and the package's `__version__`.
- Export from a Git checkout. Only tracked/staged public files are eligible; the exporter rejects
  untracked public source changes rather than silently omit them.
- Do not publish, push, tag, or merge merely because an export was regenerated. Those actions
  require the user's authorization and repository permissions.

# Complete GUI visual reference

- Keep `docs\KardboardCode-Studio-GUI-Visual-Reference.html` current after GUI layout,
  page/section/control, menu, dialog or tutorial changes.
- Capture owned native widgets only, using synthetic/example data. Never capture the desktop,
  real camera endpoints/face pixels, personal calibration or user-folder contents.
- From a Windows source checkout with the existing GUI environment, regenerate and verify:
  `.\.venv312\Scripts\python.exe scripts\capture_gui_visual_reference.py`
  `node scripts\build_gui_visual_reference.mjs`
  `node scripts\build_gui_visual_reference.mjs --check`
- The deliverable is one self-contained HTML file. Capture PNGs/manifest remain in ignored
  `build\gui-visual-reference`; the reader embeds their bytes and source/coverage receipt.
- Keep all named surfaces and required scroll parts represented in both themes. Label
  illustrative operating states and controlled Qt file-picker specimens accurately.
- Keep the main README minimal; link the complete reference rather than adding its screenshots.
