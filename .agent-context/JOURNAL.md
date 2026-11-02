# KardboardCode-VTuber Journal

> Activity for the KardboardCode VTuber engineering and streaming-output partner. Resume with STATE and MEMORY; this journal explains how decisions changed.
>
> Newest at top. This repository-local store began on 2026-10-11. Earlier work below is retrospective continuity, not evidence that this store existed then.

## 2026-11-02 - Project recap and stale-context reconciliation

- User asked for a summary of everything completed so far. Reread README, STATE, MEMORY, and JOURNAL in both mandatory stores, the full current mesh digest, and relevant project/creator-package documentation.
- Reconciled the history: existing OBS/PNGTuber setup and research; Python/OpenCV latest-frame capture; MediaPipe face/expression tracking and smoothing; textured ModernGL PS1 avatar; privacy loss handling; optional hand/green-screen diagnostics; recording workflows; direct OBS camera-component output; engineering book and local YouTube production package.
- Preserved the distinction between completed features and rejected/parked experiments. The chosen workflow remains face-only with safe-frame freeze, not body/hood fallback. Distance tracking, actual calling-app use, and recording elapsed-time mismatch remain unresolved.
- Found HEAD `5d358a9` (2026-10-25, `commiting local agent context`) on `workDesk/agentic_cameraSource`; the pre-refresh worktree was clean. Diff from September's `cd89d6b` contains only the four context files. Do not attribute the October commit to this assistant.
- Cross-session queries scoped to this repository returned no rows in seven-day and thirty-day windows; they do not prove absence of activity. The recap is grounded in the saved stores, current docs, and local Git evidence.
- The October full-offload marker was stale, so reconciled the current store without modifying the older store. No live camera, application tests, code edits, dependency installs, commit, or push was performed.
- Read the shared persona roster and current-day chat plus thirty-day direct mentions: no matching messages required a response. Created only this session's own persona file; no routine status post was added.
- Persisted the reconciled recap as zmem `ep_823`, then advanced the exact full-offload marker to `2026-11-02T11:24:57+05:30`. Runtime evidence remains explicitly historical.

## 2026-10-11 - 18:26 +05:30 - Mandatory dual-store reading; single update destination

- The user explicitly requested that future VTuber work go through both the older KardboardCode offload and this repository-local offload.
- Recorded mandatory reading of README, STATE, MEMORY, and JOURNAL from both stores before starting/resuming VTuber work. Older context is no longer an optional reference.
- All new VTuber context updates go only to `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`; `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context` remains unchanged/read-only.
- Updated the current store's resume contract, durable protocol, and live state. This is a routing-preference update, not a new full runtime reconciliation; the last full-offload timestamp remains unchanged.
- Persisted the routing convention in zmem as `sem_074` and in the VTuber persona registry entry so future sessions can discover the rule.

## 2026-10-11 - Repository base designated and context reconciled

- User requested an updated context offload. No Context Mesh base matched the current repository and no repo-local store existed.
- The user explicitly selected creation/registration of this repository's own `.agent-context`. The older OBS/PNGTuber base remains read-only.
- Read the mesh digest/index, relevant old Kardboard context, current CLI/virtual-camera source, dependency manifest, command documentation, book entry point, and local creator-package index.
- Confirmed the pre-offload worktree was clean and HEAD was the September direct-camera commit. No application behavior, dependencies, recordings, commits, or pushes were changed.
- Created README/STATE/MEMORY/JOURNAL for this base and registered its exact root/persona. Kept secrets, raw camera media, and personal calibration data out of the offload.
- Preserved the face-only preference, direct OBS device output, internal-only brightness, separate skeleton diagnostics, empty-source handling, and unresolved distance/calling-app/recording questions.
- Corrected the handoff's confidence boundaries: historical availability is not accuracy; no-face/no-side-marker is not confirmed rear orientation; older runtime/docs claims can be stale.
- Read relevant zmem entries before writing this new offload; existing search results were older August milestones, not a current virtual-camera handoff.
- Persisted the new cross-base episode as zmem `ep_780`, then set the successful store/zmem offload marker to `2026-10-11T17:36:12+05:30` before refreshing the generated mesh.

### September 14 implementation - historical, not rerun today

- Direct pyvirtualcam/OBS output, fixed-format letterboxing, startup black, owned repeated frames, clean export before local debug, headless rendering, and actionable output errors were implemented with tests/docs.
- The established Python 3.12 environment received the optional camera dependency. Native Windows DirectShow received synthetic BGR output with OBS closed; the headless CLI's synthetic no-face run remained black.
- Waiting for the CLI's virtual-camera readiness line was necessary before starting the native receiver.
- Existing pytest/Ruff validation succeeded in that session. Actual Discord/Teams/Meet calls and live distant-face accuracy were not established.
- Empty source parsing was changed from a traceback to an actionable error before resource creation. Source setup must happen in the current PowerShell terminal.
- A later repository inspection found these changes committed. Do not infer that this assistant created that commit.

### Late August and early September tracking decisions - retrospective

- Full-body calibration and guided/free recordings supported experiments with shoulder fallback and hood markers.
- Freshness, geometric plausibility, reacquisition, prediction provenance, and size retention were iteratively hardened. Recorded availability looked high but user screenshots exposed wrong orientation and size.
- Red background interference led to a temporary pink rear marker; the user subsequently requested removal of both. Green remains anatomical left and blue anatomical right.
- The final experiment used a body-only rear heuristic, stable recent reference dimensions, separate outline skeletons, and processing-only brightness.
- The user rejected this workflow for now and returned to face-only tracking with frame freeze on loss. They liked close-range rotation, but farther framing still froze.
- Suggested wider tracking input and higher brightness were not independently demonstrated to solve distant detection.
- Fixed negotiated-FPS MP4 writing produced shorter playback than telemetry elapsed time in historical recordings. This is still an open recording issue.

### Earlier foundation and creator work - retrospective

- Work began with OBS/PNGTuber setup, then a latest-frame Python/OpenCV camera pipeline, MediaPipe face tracking, privacy-first procedural geometry, and the canonical textured ModernGL PS1 avatar.
- Arbitrary monocular-depth foreground restoration was rejected after privacy failures. Conservative opt-in hand regions and fail-closed tracking loss were retained.
- Detailed avatar galleries, a chapter-based engineering book, printable handbook, and local development-video production package were created.
- Deep OBS inventory and original technology research remain with the read-only origin base; this store carries only the runtime continuation and relevant cross-references.
