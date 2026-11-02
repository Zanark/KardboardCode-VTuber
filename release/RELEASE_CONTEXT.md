# v1.1.0 release context

- Tag: `v1.1.0`
- Source commit: `4590ca7e6a6fa4b05ac13e1a9dae866782990e56`
- Source branch: `workDesk/agentic_GUI`
- Included source differs from that commit: `False`
- Public source SHA-256 fingerprint: `05e322ac47665f43f619792bb0df6277f7974123c5d69725ce4c744f326baea3`
- Generated (UTC): `2026-11-02T14:46:42+00:00`
- Source files: `221`

## Packaging scope

This is a source release, not a standalone Windows app or installer. Extract its top-level folder, create a Python 3.12 environment, install `.[tracking,virtual-camera,gui]` in editable mode, then run `python -m kardboard_vtuber.gui`. Use Models to download official models explicitly.

Includes public tracked code, scripts, tests, assets and documentation plus release notes. Excludes Git internals, generated release artifacts, private agent context, local credentials/config, environments, recordings/captures, caches and downloaded models.

## Publishing checklist

1. Verify `python scripts\export_release.py --check`.
2. Push the intended source branch/commit using an authorized account. The source must first be committed and re-exported if sourceModified is true. The source commit above identifies export inputs; a later commit may contain only generated release/context files. The source fingerprint is the content-level freshness check.
3. Create the tag against this source or its merged equivalent, not an older main.
4. Paste RELEASE_NOTES.md and upload the ZIP, manifest and checksums from this folder.
5. Keep published release assets immutable; later exports are separate snapshots.

No publishing, pushing, merging, camera capture or model download is performed by this exporter. Known limitations and setup requirements are in RELEASE_NOTES.md.
