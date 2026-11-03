# v1.2.4 release context

- Tag: `v1.2.4`
- Source commit: `e75d5d9d2b0cb1932c3e139021668693a4bf313a`
- Source branch: `workDesk/agentic_GUI`
- Included source differs from that commit: `False`
- Public source SHA-256 fingerprint: `3cd5c505887c0ee552b5e5acaf6584b54eab7a16abcf5fc98699390dacd9c979`
- Generated (UTC): `2026-11-03T01:08:28+00:00`
- Source files: `254`

## Packaging scope

This ZIP is a source release, not an installed Windows app. A separate online, unsigned Windows x64 MSI is available beside it, with installer-manifest.json and INSTALLER_SHA256SUMS.txt. Those generated files are not nested in this archive. Extract its top-level folder, create a Python 3.12 environment, install `.[tracking,virtual-camera,gui]` in editable mode, then run `python -m kardboard_vtuber.gui`. Use Models to download official models explicitly.

Includes public tracked code, scripts, tests, assets and documentation plus release notes. Excludes Git internals, generated release artifacts, private agent context, local credentials/config, environments, recordings/captures, caches and downloaded models.

## Publishing checklist

1. Verify `python scripts\export_release.py --check`.
2. Push the intended source branch/commit using an authorized account. The source must first be committed and re-exported if sourceModified is true. The source commit above identifies export inputs; a later commit may contain only generated release/context files. The source fingerprint is the content-level freshness check.
3. Create the tag against this source or its merged equivalent, not an older main.
4. Paste RELEASE_NOTES.md. Upload the source ZIP/manifest/checksums and the separate MSI/installer-manifest/INSTALLER_SHA256SUMS; verify both build scripts with --check.
5. Keep published release assets immutable; later exports are separate snapshots.

No publishing, pushing, merging, camera capture or model download is performed by this exporter. Known limitations and setup requirements are in RELEASE_NOTES.md.
