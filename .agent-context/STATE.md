> **Last updated:** 2026-11-02 (Asia/Kolkata) - Native desktop studio requested and implemented; final delivery checks in progress.
> **Last context offload:** 2026-11-02T11:24:57+05:30

# KardboardCode-VTuber State

> Resume as the KardboardCode VTuber engineering and streaming-output partner. Read both context stores below before continuing; preserve the user's face-only choice and privacy requirements.

## Current focus

After the recap, the user requested deep GUI research/design documentation, numbered implementation TODOs, and an actual fast native Python GUI with independent eye sliders, a KC cardboard icon, README screenshots, architecture/design rationale, and a tutorial. They explicitly selected **all existing features**, including experiments and raw debugging. An optional PySide6 desktop studio is now implemented; final documentation, screenshot refresh and delivery checks are in progress. No live camera has been opened.

The user still chose **face mesh tracking with a frozen last-safe frame on face loss** as the default after unreliable body/hood-marker experiments. Exposing every feature in the GUI does not replace that choice. Actual Discord/Teams/Meet use and reliable distant-face tracking remain unconfirmed.

This repository is now the explicitly designated home for VTuber implementation continuity. The older KardboardCode OBS store remains a read-only origin reference, not the destination for new runtime updates.

## Mandatory context routing

Before starting or resuming VTuber work, read all four context files (`README.md`, `STATE.md`, `MEMORY.md`, `JOURNAL.md`) in both stores:

- **Read only:** `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context`.
- **Read and write all new VTuber updates here only:** `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`.

This is the user's explicit 2026-10-11 instruction. The older store is required context, not optional background. Keep it unchanged and reconcile its historical notes against later verified decisions here.

## Threads

### Native desktop studio - delivery in progress

- Entry points: `python -m kardboard_vtuber.gui` and the optional `kardboard-studio` GUI launcher. PySide6-Essentials is an optional dependency; normal CLI imports do not import Qt.
- Research, complete control inventory, layout rationale, runtime architecture and tutorial live in `docs\09-desktop-studio`. Numbered workstreams/evidence live under `TODO`.
- Native settings cover all 45 current camera flags plus model verification/force download and existing private guided/free recording. The nine-part tutorial navigates to the matching page.
- `cli.main(runtime=RuntimeBridge(...))` reuses the actual pipeline on a QThread. Widget updates use one owned preview slot and bounded logs, not per-frame queued signals. Resource cleanup uses ExitStack, including partial initialization failure.
- `tracking.eyes.EyeSensitivity` is shared by actions and both renderers. Left/right blink overrides, relative wink parameters, brightness and debounce intervals are live; resource topology/settings unlock after Stop.
- Source URLs and raw-preview consent are excluded from presets. Local raw modes require acknowledgement. Model/source file inspection is deferred from slider callbacks to the worker.
- Recorded-footage integration exercised the actual native GUI, MediaPipe and GPU path: 55 displayed packets, 54 effective detections, exit 0. No imagery was saved and this is not privacy/accuracy qualification.
- The final full suite passed 220 cases and Ruff after the responsive-validation refinements. Refreshed synthetic dark/light/compact/tutorial screenshots show the complete avatar. A six-second recorded-input run applied live tuning successfully; 359 post-warmup Qt heartbeat intervals had p95 31 ms/max 47 ms. These are local UI service intervals, not video latency.
- Handbook source built and the first updated PDF rendered with 242 pages/97 diagrams and no diagram failures. The final edition is being refreshed with GUI screenshots and measured evidence; overflow checking and milestone commits remain.
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

Finish the desktop studio delivery workstream: final checks/screenshots, handbook generation, TODO evidence, milestone commits, context/mesh refresh, and opening a synthetic-only GUI for review. Do not connect a live source or publish output automatically. Preserve all earlier tracking/calling-app uncertainties.

## Environment reminders

- Current base: `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber`.
- Repository observed on 2026-11-02: `Zanark/KardboardCode-VTuber`, branch `workDesk/agentic_cameraSource`, HEAD `5d358a9` dated 2026-10-25 (`commiting local agent context`). The worktree was clean before this refresh. The diff from `cd89d6b` contains only the four context Markdown files; no later application changes appear in that checked-out commit range. These are snapshot facts, not permanent defaults.
- Python tracking workflow uses `.venv312`; the tracking extra is conditional on Python below 3.13. `pyproject.toml` uses `opencv-contrib-python` as the single OpenCV distribution.
- October source review covered `cli.py:288-620`, `virtual_camera.py:13-109`, `pyproject.toml:17-27`, and README direct-camera instructions. November reconciliation reread the current README, book index, and creator-package README; the commit comparison found no application changes since that review.
- Historical September validation: existing pytest/Ruff suites passed; native synthetic output was received with OBS closed; the synthetic no-face CLI sent black. These were not rerun for the October or November context tasks and do not establish live accuracy or actual calling-app success.
- The earlier November recap was context-only. The subsequent GUI request now changes application code, optional dependencies, tests, TODOs, and documentation. No live camera, raw screenshot capture, or push has been performed for the GUI request.
- Local session provenance: `C:\Users\mishrad\.copilot\session-state\5f0403d8-ec0e-4548-b7cd-c9120aeb3ec7`. Its checkpoints preserve earlier work. Raw artifacts are private; do not copy them into durable context or public docs.
- Read-only origin: `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context` (August snapshot with superseded runtime details).
- Latest cross-base offload receipt: zmem episodic `ep_823` (`KardboardCode-VTuber November project recap and context reconciliation`). Earlier registration receipt: `ep_780`; mandatory dual-store routing: `sem_074`.
