# Latest release export

This tracked folder is the handoff for creating a GitHub release manually. Regenerate it after
source/documentation changes; it always represents the latest exported tool, not a release history.

**v1.0.0 is the first official release**, adopting the supplied voxel KC box logo. The earlier
v0.2.0 export was unpublished local staging, not an official release.

## Files

| File | Purpose |
|---|---|
| `KardboardCode-VTuber-source.zip` | Uploadable source package with GUI, CLI, scripts, tests, assets and documentation |
| `RELEASE_NOTES.md` | Copy its text into the GitHub release description |
| `RELEASE_CONTEXT.md` | Generated version, source provenance, packaging scope and publishing checklist |
| `manifest.json` | Machine-readable source fingerprint, per-file hashes and archive hash |
| `SHA256SUMS.txt` | Checksums for the archive, release notes, context and manifest |

This is **not a standalone Windows executable/installer**. Python and the selected optional
dependencies are installed on the receiving machine. Downloaded models are intentionally excluded.
Release text uses canonical LF line endings through `.gitattributes`; keep that format when
editing these instructions or notes. Do not edit generated files manually, because that would
invalidate their checksums. ZIP files are always binary.
The source ZIP includes these instructions and the notes, but not a nested copy of the generated
release archive/context/manifest/checksums. Regenerate those from a Git checkout when contributing.

## Regenerate and verify

From the repository root, using Python 3.11+:

```powershell
git add -- README.md pyproject.toml src scripts tests assets docs TODO AGENTS.md
.\.venv312\Scripts\python.exe scripts\export_release.py
.\.venv312\Scripts\python.exe scripts\export_release.py --check
```

Stage any other new public files you intend to export too. Do not stage private files. Existing
tracked working-tree edits are included; new public files must first be tracked/staged. Export
changes are never pushed or published automatically.

The archive name stays fixed so the folder does not collect obsolete ZIPs. Version/provenance
are recorded in its manifest/context and in the archive's top-level folder.

## Create the GitHub release

1. Verify the export with `--check`. Review the notes and `RELEASE_CONTEXT.md`.
2. If `sourceModified` is true, commit the public source changes and export again. Push the
   intended source branch/commit with an account that has repository Write access.
3. Create the tag shown in `manifest.json`, targeting that GUI/source commit or its merged
   equivalent. **Do not accidentally target an older `main` that lacks these changes.**
4. Paste `RELEASE_NOTES.md` into the release description.
5. Upload `KardboardCode-VTuber-source.zip`, `SHA256SUMS.txt`, `manifest.json`, and optionally
   `RELEASE_CONTEXT.md` / `RELEASE_NOTES.md`.
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
