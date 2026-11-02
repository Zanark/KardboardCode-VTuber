> **Last updated:** 2026-11-02 (Asia/Kolkata) - Native desktop studio delivered locally and opened in a camera-free demo.
> **Last context offload:** 2026-11-02T14:33:17+05:30

# KardboardCode-VTuber State

> Resume as the KardboardCode VTuber engineering and streaming-output partner. Read both context stores below before continuing; preserve the user's face-only choice and privacy requirements.

## Current focus

The native PySide6 studio is delivered. The user's follow-up request for explicit native machine/laptop camera selection is also implemented: Camera now separates computer cameras from custom URL/file/index sources, with asynchronous named Windows device discovery. Selection pairs the proper backend/index; refreshing/selecting does not open a stream. All 45 runtime options, live eye calibration, KC icon, recording/model actions, presets, themes, logs and tutorial remain available. No live camera has been opened by this agent; user appearance and physical-device capture qualification remain pending.

The user still chose **face mesh tracking with a frozen last-safe frame on face loss** as the default after unreliable body/hood-marker experiments. Exposing every feature in the GUI does not replace that choice. Actual Discord/Teams/Meet use and reliable distant-face tracking remain unconfirmed.

This repository is now the explicitly designated home for VTuber implementation continuity. The older KardboardCode OBS store remains a read-only origin reference, not the destination for new runtime updates.

## Mandatory context routing

Before starting or resuming VTuber work, read all four context files (`README.md`, `STATE.md`, `MEMORY.md`, `JOURNAL.md`) in both stores:

- **Read only:** `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context`.
- **Read and write all new VTuber updates here only:** `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`.

This is the user's explicit 2026-10-11 instruction. The older store is required context, not optional background. Keep it unchanged and reconcile its historical notes against later verified decisions here.

## Threads

### Native desktop studio - delivered; awaiting owner review

- Follow-up native-camera workstream: `TODO\06_NATIVE_CAMERA_SELECTION.todo`. Choose Camera -> This computer's camera -> Refresh -> named laptop/USB device -> Start camera. Windows startup performs metadata-only listing when this input type is active.
- `camera.devices` uses the optional `cv2-enumerate-cameras` Windows adapter through the existing owned subprocess job lifecycle. Explicit MSMF/DSHOW enumeration avoids cross-backend index mismatch. Device paths/serials are not exposed or persisted.
- Source modes remember their separate source/backend pairs in session memory only. Named selections set both together; loading presets retains source-free semantics. Refresh/reselect after hardware changes; a missing previous selection is cleared.
- Current follow-up validation: 236 tests and Ruff passed, including actual asynchronous metadata discovery. This machine reported Integrated Camera under MSMF and DSHOW and OBS Virtual Camera under DSHOW. These are backend entries, not three physical cameras. No capture stream or frame probe was used.
- The Studio was refreshed on its idle Camera page and verified responding. Windows local-camera mode lists metadata on startup; the user still must choose a device and press Start. The native-selector screenshot uses illustrative device names, not captured camera imagery.

- Entry points: `python -m kardboard_vtuber.gui` and the optional `kardboard-studio` GUI launcher. PySide6-Essentials is an optional dependency; normal CLI imports do not import Qt.
- Research, complete control inventory, layout rationale, runtime architecture and tutorial live in `docs\09-desktop-studio`. Numbered workstreams/evidence live under `TODO`.
- Native settings cover all 45 current camera flags plus model verification/force download and existing private guided/free recording. The nine-part tutorial navigates to the matching page.
- `cli.main(runtime=RuntimeBridge(...))` reuses the actual pipeline on a QThread. Widget updates use one owned preview slot and bounded logs, not per-frame queued signals. Resource cleanup uses ExitStack, including partial initialization failure.
- `tracking.eyes.EyeSensitivity` is shared by actions and both renderers. Left/right blink overrides, relative wink parameters, brightness and debounce intervals are live; resource topology/settings unlock after Stop.
- Source URLs and raw-preview consent are excluded from presets. Local raw modes require acknowledgement. Model/source file inspection is deferred from slider callbacks to the worker.
- Recorded-footage integration exercised the actual native GUI, MediaPipe and GPU path: 55 displayed packets, 54 effective detections, exit 0. No imagery was saved and this is not privacy/accuracy qualification.
- The final full suite passed 224 cases and Ruff, including cancellation during model initialization, preservation of zero-duration CLI probes, literal-source argument binding, parser-exit reporting and quoted/malformed endpoint redaction. Refreshed synthetic dark/light/compact/tutorial screenshots show the complete avatar. A six-second recorded-input run applied live tuning successfully; 359 post-warmup Qt heartbeat intervals had p95 31 ms/max 47 ms. These are local UI service intervals, not video latency; startup/theme/capture runs had larger transients.
- The final illustrated handbook rendered 245 pages with 97 diagrams, zero Mermaid failures and `PAGES_WITH_OVERFLOW=0`. README/book links and fences passed. All four installed models passed their existing checksum helpers without downloads.
- Local milestone commits: `c84e6d7` research/design, `f233d09` runtime/calibration, `93a1fb1` native studio. The documentation/delivery commit includes the final evidence, authored book builders and compatibility safeguards. Current branch observed at delivery is `workDesk/agentic_GUI`; no branch switch is attributed to this agent and no push was performed.
- The final studio review window was verified open/responding on 2026-11-02. Treat that as a dated observation, not a guarantee it remains running in a later session. Launch via `.venv312\Scripts\kardboard-studio.exe` or `python -m kardboard_vtuber.gui`; `--demo` never opens capture/output.
- User visual approval, real camera qualification and calling-app confirmation remain pending. Do not equate synthetic demo evidence with those outcomes.

### Preferred face-only workflow

- Keep `--physics`, `--mirror`, and face tracking; omit `--hood-marker-tracking`, `--body-head-fallback`, and `--full-body` unless the user explicitly revisits those experiments.
- The user liked close-range face rotation but reported loss/freeze farther from the camera. `--tracking-width 1280` was suggested; it is not a proven distance fix.
- The latest requested processing brightness was `80`; this is a chosen setting, not a calibrated recommendation. Brightness affects parsing only, not visible camera pixels.
- An unset `$env:KARDBOARD_CAMERA_URL` caused source errors. The CLI now reports an actionable input error and exits before opening resources. The source must be supplied in the same terminal.

Credential-free resume template; enter the currently valid source locally rather than recovering an old URL from memory:

```powershell
$env:KARDBOARD_CAMERA_URL = Read-Host "Paste your full camera stream URL"
.\.venv312\Scripts\python.exe -m kardboard_vtuber `
  --source $env:KARDBOARD_CAMERA_URL `
  --mirror `
  --physics `
  --tracking-width 1280 `
  --brightness 80 `
  --tracking-debug `
  --virtual-camera
```

`--tracking-debug` is local only; omit it for a clean preview. Add `--headless` for no preview windows. Do not add `--debug-face-preview` by default. Camera address and credentials are deliberately not retained.

### Direct camera output

- Optional installation: `.\.venv312\Scripts\python.exe -m pip install -e ".[tracking,virtual-camera]"`. Do not reinstall merely to hydrate context.
- Select **OBS Virtual Camera** in the consuming app. This is the installed OBS device, not a custom KardboardCode-named driver. OBS itself may remain closed; do not run another OBS virtual-camera producer concurrently.
- Default fixed output is 1280x720 at an advertised 30 FPS, aspect-fitted with black bars. It carries video only; select microphone audio separately.
- Export happens before local debug/raw-preview overlays. Startup is black; face-only tracking loss/staleness freezes the safe composite. Headless delivery still runs the renderer.
- Native synthetic DirectShow reception with OBS closed and synthetic no-face headless CLI output were demonstrated in the September session. Real calling-app permissions, compatibility, and motion quality were not tested.

### Body/hood-marker experiments - parked, not removed wholesale

- Calibrated shoulder fallback and hybrid marker tracking remain implemented but are not the chosen workflow.
- Only green (anatomical left) and blue (anatomical right) markers remain. Red was changed to pink temporarily, then both rear-colour approaches were removed.
- Reference sizing, freshness/history expiry, reacquisition, and pose plausibility gates were added after failures. The two optional fallback modes cannot be combined.
- Body pose without a face or side markers is used as a rear-facing heuristic after a short hold. It does not logically confirm that the subject is facing away.
- High offline head-state availability did not establish accurate box placement or privacy; subsequent live screenshots contradicted earlier confidence.
- `--full-body` currently opens a separate outline/numbered-skeleton diagnostic. It does not fill a skeletal avatar into the final cardboard-camera render.

### Avatar, documentation, and creator assets

- Default rendering is genuine textured ModernGL 3D, with a PS1-style hollow cardboard shell, corrugation, chunky headphones, K/C expressions, asymmetric aged labels, and five optional spring-driven flap/tab hinges.
- Keep the full-resolution camera sharp while the avatar uses a deliberately low-resolution render target. Do not regress to a flat rectangle to approximate the canonical model.
- The engineering book, synthetic visual galleries, and printable handbook already exist; use `docs\README.md` and the textured-renderer chapter instead of reconstructing the art decisions.
- `YTScript\README.md` indexes the existing local six-part development-video production package. No completed edit or publication is established.
- Some older docs/context remain inconsistent with runtime, notably the book status row describing synthetic full-body rendering and the old store describing visible brightness. Current CLI behavior takes precedence. No documentation cleanup was requested during this offload.

### Recording and throughput follow-ups

- Guided/free full-body recording and synchronized frame telemetry exist in `scripts\record_guided_regression.py`.
- Historical recordings showed fixed negotiated-FPS writing could accelerate playback when capture delivered fewer frames. Frame/CSV alignment alone does not fix elapsed-time mismatch; this remains unresolved.
- Latest-frame overwrites are expected. Negotiated FPS and local post-decode frame age are not measured end-to-end throughput/latency.
- A historical move from 2.4 GHz to 5 GHz improved capture; no new live network/camera measurement was made for this offload.

## Open questions

- Does the current clean output work in the user's actual calling app with its permissions and policies?
- What provides reliable distant-face acquisition in the intended framing? Do not promise that width or brightness alone solves it.
- Should recording preserve real elapsed time through timestamps or a different writer policy? Revisit only when requested.
- If body/rear tracking returns, what evidence establishes accurate coverage rather than merely an available pose?

## Next steps

Wait for the user's review of the desktop studio. Do not repeat completed implementation/build/tests or launch another window without a reason. Address actual feedback with focused changes, preserve CLI compatibility, keep new context here, and continue reading both stores. Do not connect a live source or publish output automatically. All earlier distant-tracking, calling-app and recording-timing uncertainties remain.

## Environment reminders

- Current base: `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber`.
- Pre-GUI recap snapshot on 2026-11-02: `Zanark/KardboardCode-VTuber`, then branch `workDesk/agentic_cameraSource`, HEAD `5d358a9` dated 2026-10-25 (`commiting local agent context`). That pre-GUI diff from `cd89d6b` contained only context files. The later GUI delivery is on the observed `workDesk/agentic_GUI` branch; use current Git history rather than treating the earlier snapshot as current.
- Python tracking workflow uses `.venv312`; the tracking extra is conditional on Python below 3.13. `pyproject.toml` uses `opencv-contrib-python` as the single OpenCV distribution.
- October source review covered `cli.py:288-620`, `virtual_camera.py:13-109`, `pyproject.toml:17-27`, and README direct-camera instructions. November reconciliation reread the current README, book index, and creator-package README; the commit comparison found no application changes since that review.
- Historical September validation: existing pytest/Ruff suites passed; native synthetic output was received with OBS closed; the synthetic no-face CLI sent black. These were not rerun for the October or November context tasks and do not establish live accuracy or actual calling-app success.
- The earlier November recap was context-only. The subsequent GUI request changed application code, optional dependencies, tests, TODOs, and documentation and was committed in milestones. No live camera, raw screenshot capture, or push was performed for the GUI request.
- Local session provenance: `C:\Users\mishrad\.copilot\session-state\5f0403d8-ec0e-4548-b7cd-c9120aeb3ec7`. Its checkpoints preserve earlier work. Raw artifacts are private; do not copy them into durable context or public docs.
- Read-only origin: `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context` (August snapshot with superseded runtime details).
- Latest cross-base receipt: `ep_834` (native camera selector, 236 tests), following source-boundary validation `ep_832` and GUI delivery `ep_829`. Earlier recap: `ep_823`; registration: `ep_780`; mandatory dual-store routing: `sem_074`.
