# Latest release export

This tracked folder is the handoff for creating a GitHub release manually. Regenerate it after
source/documentation changes; it always represents the latest exported tool, not a release history.

**v1.0.0 was designated the first official version**, adopting the supplied voxel KC box logo.
The current **v1.2.4** handoff fixes embedded numeric text padding, the optional preview-height
binding and misleading Video-only availability labels after an actual GUI coverage audit.
It retains the preferred four metric cards below the preview,
beside Tools. The drawer opens under the viewer only, keeping settings full-height.
Readable, stacked visual diagnostics stay to the preview's right. **Show clean output** remains available in Live
mode to reopen the separate window; **Auto-open** is an independent startup preference.
Labelled control sections, optional Logs/CLI/Signals tools and clear numeric buttons remain.
It retains online Windows setup,
brown dark-theme sliders and automatic video playback. The earlier
v0.2.0 export was unpublished local staging. A local version/export is not a remote publication.

## Published v1.2.4

[GitHub release](https://github.com/Zanark/KardboardCode-VTuber/releases/tag/v1.2.4) ·
[Windows x64 setup](https://github.com/Zanark/KardboardCode-VTuber/releases/download/v1.2.4/KardboardCode-Studio-windows-x64.msi) ·
[Source ZIP](https://github.com/Zanark/KardboardCode-VTuber/releases/download/v1.2.4/KardboardCode-VTuber-source.zip)

Published November 13, 2026 from merged main commit
`feee3b0f9b1f074487224007a15d01bb954a0eff`. All eight uploaded assets were verified
against their local SHA256 digests. The release includes the separate source/installer
receipts, checksum files, notes and context.

Published assets are immutable snapshots. This tracked folder can subsequently include
newer documentation/tracking exports; do not overwrite v1.2.4 assets with those newer files.
The installer is still online, unsigned and Windows x64 only, with explicit model downloads
and a separate OBS component prerequisite for virtual-camera output.

## Files

| File | Purpose |
|---|---|
| `KardboardCode-Studio-windows-x64.msi` | Online per-user Windows setup with private Python; no manual Python/pip |
| `installer-manifest.json` | Installer version, runtime-input fingerprint, source provenance and MSI hash |
| `INSTALLER_SHA256SUMS.txt` | Checksums for MSI and installer receipt |
| `KardboardCode-VTuber-source.zip` | Uploadable source package with GUI, CLI, scripts, tests, assets and documentation |
| `RELEASE_NOTES.md` | Copy its text into the GitHub release description |
| `RELEASE_CONTEXT.md` | Generated version, source provenance, packaging scope and publishing checklist |
| `manifest.json` | Machine-readable source fingerprint, per-file hashes and archive hash |
| `SHA256SUMS.txt` | Checksums for the archive, release notes, context and manifest |

The MSI is **online, unsigned and Windows x64 only**. First launch offers hash-locked component
downloads from PyPI or an existing verified HTTPS mirror. It includes patched private Python,
without changing system Python/PATH. Models are explicit GUI downloads; OBS's camera component
is separate. Uninstall preserves per-user models, presets, recordings, component environments
and cache. Device policy/SmartScreen may restrict unsigned packages; never disable protections.
See [Windows installation](../docs/09-desktop-studio/windows-installation.md).

The ZIP remains a **source package**, with manual Python/dependency setup. Downloaded models
and generated installer artifacts are intentionally excluded from it.
Release text and installer configuration use canonical LF line endings through `.gitattributes`;
keep that format when editing them. Do not edit generated files manually, because that would
invalidate their checksums. ZIP and MSI files are always binary.
The source ZIP includes these instructions and the notes, but not a nested copy of the generated
release archive/context/manifest/checksums. Regenerate those from a Git checkout when contributing.

## Regenerate and verify

From the repository root, using Windows x64 Python 3.12:

```powershell
git add -- README.md pyproject.toml src scripts tests assets docs TODO AGENTS.md
git add -- installer .gitattributes release/README.md release/RELEASE_NOTES.md
.\.venv312\Scripts\python.exe scripts\build_windows_installer.py
.\.venv312\Scripts\python.exe scripts\build_windows_installer.py --check
.\.venv312\Scripts\python.exe scripts\export_release.py
.\.venv312\Scripts\python.exe scripts\export_release.py --check
```

Stage any other new public files you intend to export too. Do not stage private files. Existing
tracked working-tree edits are included; new public files must first be tracked/staged. Export
changes are never pushed or published automatically.

The archive name stays fixed so the folder does not collect obsolete ZIPs. Version/provenance
are recorded in its manifest/context and in the archive's top-level folder.

Build the MSI with Windows x64 Python 3.12 (`msilib` is build-only). The normal build reuses the
committed dependency lock. Intentional `--update-lock` resolves the installed runtime dependency
closure, downloads binary wheels and compares each with its authoritative PyPI hash. No private
package-feed configuration is embedded. Commit public inputs, then finalize both source and
installer provenance; `--refresh-provenance` does not rebuild or accept changed runtime inputs.

## Create the GitHub release

1. Verify both scripts with `--check`. Review the notes, `RELEASE_CONTEXT.md` and installer receipt.
2. If `sourceModified` is true, commit the public source changes and export again. Push the
   intended source branch/commit with an account that has repository Write access.
3. Create the tag shown in `manifest.json`, targeting that GUI/source commit or its merged
   equivalent. **Do not accidentally target an older `main` that lacks these changes.**
4. Paste `RELEASE_NOTES.md` into the release description.
5. Upload the MSI, `INSTALLER_SHA256SUMS.txt`, `installer-manifest.json`, source ZIP,
   `SHA256SUMS.txt`, `manifest.json`, and optionally context/notes.
6. Preserve published release assets as immutable snapshots. A later update to this folder is
   a new export; it is not permission to overwrite an older published version.

GitHub's automatic source archives are separate from this curated source package.

## Source package setup

Extract the ZIP, open PowerShell in its top-level project folder, and run:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -e ".[tracking,virtual-camera,gui]"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

Use the **Models** page to explicitly verify/download the official models before live tracking.
Use **Try demo** for a camera-free preview. OBS Studio's installed camera component is needed
only for OBS Virtual Camera output; audio remains separate.
