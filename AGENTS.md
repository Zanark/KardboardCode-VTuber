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

# Development manual and GitHub Kanban

- Read the current `development-documentation-manual` skill and its canonical support at
  `C:\devdesk\homedesk\skill-library\skills\development-documentation-manual`, especially
  `docs\GITHUB-TRACKING.md`. Preserve this repository's release, GUI and documentation contracts.
- Keep `TODO\00_INDEX.todo`, stable numbered workstreams, all eight required fields and
  `TODO\05_DEVELOPMENT_LEDGER.todo`. Do not replace them with a flat checklist.
- Tracking is one included actual workstream -> one repository issue -> one issue-containing
  Project item. Canonical repository: `Zanark/KardboardCode-VTuber`; Kanban:
  `https://github.com/users/Zanark/projects/9/views/1`, grouped into Status columns.
- Configuration: `scripts\todo-sync.json`; durable mappings/intents/baselines:
  `scripts\todo-sync-state.json`; tool: `scripts\todo_sync.py`. Preserve permanent `kc-NN`
  identities and managed markers across file/repository renames. Titles alone are not identities.
- After TODO creation, description/task/evidence changes, completion, reopening or cancellation,
  preview and then explicitly apply under the adopted issue/Project authority. New public workstreams
  require a unique permanent ID and explicit configuration inclusion after privacy/status review.
- Run from this root, using the external reviewed credential runner:
  `python "C:\devdesk\homedesk\skill-library\skills\development-documentation-manual\scripts\with_github_token.py" -- python scripts\todo_sync.py`
  Add `--apply` for writes, and `--only kc-01` for a bounded selection. No scheduler is installed.
- Never view/copy the credential file, print tokens or change global `GH_TOKEN`. Review executed code
  before credentialed use. Never run this privileged maintainer tool against untrusted PR code.
- Index00/ledger05 are not feature issues. Private workstreams13/17 have no approved public
  projection and remain excluded. Never mirror private context, raw conversations/media or YTScript.
- Local TODOs own managed issue titles/body/lifecycle and Project Status. Preserve human text
  outside the managed section and all comments. Stop conflicts/uncertain operations for that item;
  keep recoverable progress and continue independent safe items. Never reset baselines casually.
- Read back content, closure reason, item identity, Status and persistent backlink. Do not equate
  implementation/local verification with hosted qualification, human acceptance or publication.
- Follow `docs\github-tracking-adoption.md` for exact mappings, recovery, commands and evidence.
  Keep backlinks/state with their TODO changes when a commit/push is separately authorized.
  This adoption does not authorize commits, pushes, workflow activation/dispatch or releases.

# Repository-local commit attribution

- For future separately authorized commits, set only this repository's Git identity:
  `git config --local user.name "Zanark"`
  `git config --local user.email "32354314+Zanark@users.noreply.github.com"`
- Before committing, verify both `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`.
  Environment overrides must not change the intended attribution. Do not dump the environment.
- Never change global Git identity, rewrite historical attribution, amend without authority or
  substitute a misleading `.mailmap`. Preserve required co-author and actual-session trailers.
- Attribution setup is not permission to commit or push.
