> **Last updated:** 2026-11-02 (Asia/Kolkata) - Both context stores reread; project recap and repository snapshot reconciled.
> **Last context offload:** 2026-11-02T11:24:57+05:30

# KardboardCode-VTuber State

> Resume as the KardboardCode VTuber engineering and streaming-output partner. Read both context stores below before continuing; preserve the user's face-only choice and privacy requirements.

## Current focus

The user requested a summary of all work so far. All four files in both context stores were reread on 2026-11-02, together with current project documentation and repository history. No feature work or live capture is requested. The user chose **face mesh tracking with a frozen last-safe frame on face loss** after unreliable body/hood-marker experiments. Direct camera output is implemented through the installed **OBS Virtual Camera** component, without running OBS. Actual Discord/Teams/Meet use and reliable distant-face tracking remain unconfirmed.

This repository is now the explicitly designated home for VTuber implementation continuity. The older KardboardCode OBS store remains a read-only origin reference, not the destination for new runtime updates.

## Mandatory context routing

Before starting or resuming VTuber work, read all four context files (`README.md`, `STATE.md`, `MEMORY.md`, `JOURNAL.md`) in both stores:

- **Read only:** `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context`.
- **Read and write all new VTuber updates here only:** `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`.

This is the user's explicit 2026-10-11 instruction. The older store is required context, not optional background. Keep it unchanged and reconcile its historical notes against later verified decisions here.

## Threads

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

Wait for the user's next runtime request. For calling-app troubleshooting, first distinguish source acquisition, face detection, renderer coverage, virtual-camera registration/producer ownership, and consumer permissions. Do not start the live camera or revive marker experiments merely because the base was resumed.

## Environment reminders

- Current base: `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber`.
- Repository observed on 2026-11-02: `Zanark/KardboardCode-VTuber`, branch `workDesk/agentic_cameraSource`, HEAD `5d358a9` dated 2026-10-25 (`commiting local agent context`). The worktree was clean before this refresh. The diff from `cd89d6b` contains only the four context Markdown files; no later application changes appear in that checked-out commit range. These are snapshot facts, not permanent defaults.
- Python tracking workflow uses `.venv312`; the tracking extra is conditional on Python below 3.13. `pyproject.toml` uses `opencv-contrib-python` as the single OpenCV distribution.
- October source review covered `cli.py:288-620`, `virtual_camera.py:13-109`, `pyproject.toml:17-27`, and README direct-camera instructions. November reconciliation reread the current README, book index, and creator-package README; the commit comparison found no application changes since that review.
- Historical September validation: existing pytest/Ruff suites passed; native synthetic output was received with OBS closed; the synthetic no-face CLI sent black. These were not rerun for the October or November context tasks and do not establish live accuracy or actual calling-app success.
- The November summary task changes only this context store and its own session-persona file, plus zmem/generated mesh output. No application edits, live capture, dependency changes, commits, or pushes were performed.
- Local session provenance: `C:\Users\mishrad\.copilot\session-state\5f0403d8-ec0e-4548-b7cd-c9120aeb3ec7`. Its checkpoints preserve earlier work. Raw artifacts are private; do not copy them into durable context or public docs.
- Read-only origin: `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context` (August snapshot with superseded runtime details).
- Latest cross-base offload receipt: zmem episodic `ep_823` (`KardboardCode-VTuber November project recap and context reconciliation`). Earlier registration receipt: `ep_780`; mandatory dual-store routing: `sem_074`.
