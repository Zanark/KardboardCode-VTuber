# Repository release staging

- Keep the tracked `release` folder current with the latest public source export after code,
  configuration, tests, assets, or documentation changes.
- Stage new public source files first, then run:
  `python scripts\export_release.py`
- Verify freshness before handing off changes:
  `python scripts\export_release.py --check`
- The archive is a source release, not a standalone executable or installer. Preserve its
  setup instructions and known limitations.
- Never export `.agent-context`, credentials/local environment files, raw recordings/captures,
  downloaded models, virtual environments, caches, Git internals, or the release archive itself.
- Update `release\RELEASE_NOTES.md` when preparing a new version. Keep its version aligned with
  `pyproject.toml` and the package's `__version__`.
- Export from a Git checkout. Only tracked/staged public files are eligible; the exporter rejects
  untracked public source changes rather than silently omit them.
- Do not publish, push, tag, or merge merely because an export was regenerated. Those actions
  require the user's authorization and repository permissions.
