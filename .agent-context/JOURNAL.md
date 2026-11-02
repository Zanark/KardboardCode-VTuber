# KardboardCode-VTuber Journal

> Activity for the KardboardCode VTuber engineering and streaming-output partner. Resume with STATE and MEMORY; this journal explains how decisions changed.
>
> Newest at top. This repository-local store began on 2026-10-11. Earlier work below is retrospective continuity, not evidence that this store existed then.

## 2026-11-02 - README layout and local source release preparation

- User requested moving GUI text/gallery below Current milestone while leaving one tool screenshot above it. Reordered the existing sections without discarding the other avatar/demo images.
- GitHub reported read-only repository authorization and no existing releases. User explicitly redirected to a separate tracked local release folder that remains current with the latest tool export. No account switch or publishing workaround was attempted.
- Prepared v0.2.0 package/version alignment, release notes, manual setup/publication context, and a standard-library public-source ZIP exporter. Added AGENTS release-freshness guidance and workstream 07.
- Export excludes private context, local credentials/config, recordings, models, environments, caches and generated self-recursion. Authored release instructions/notes stay inside source packages so README links work.
- Full suite passed 241 tests and Ruff. Verified stale/tampered detection, staged-file gating, repeatability and clean-commit provenance refresh. README order has exactly one tool image before the milestone.
- A candidate archive was extracted privately and launched both help entry points and the real synthetic GUI preview from its extracted root. No camera capture, model download or private imagery was used.
- Final handoff uses a public-input commit followed by a clean-provenance archive/export commit. Remote publication remains the owner's action; no tag, release, merge or push has been created.
- Public inputs were committed as `e5e2db3`; the final v0.2.0 export passed freshness/content/checksum checks with `sourceModified=false`. The tracked handoff ZIP is about 30 MB.
- Persisted the release handoff as zmem `ep_836` and set the full-offload marker to `2026-11-02T17:06:20+05:30`. Repository-memory API was unavailable; the durable rule remains in AGENTS.md, release instructions, this store and zmem.

## 2026-11-02 - Explicit native machine camera selection

- User requested a native machine/laptop camera option. Existing capture already accepted numeric devices; added a discoverable computer-camera input mode and named selector instead of requiring a masked index.
- Reused the existing asynchronous subprocess lifecycle for metadata discovery. Reviewed the adapter's Windows source: Media Foundation attributes and DirectShow property bags are enumerated without capture/activation calls. No vendor client/driver was installed.
- Named selections route matching API/index pairs. Custom phone/file/manual sources remain available, with separate in-memory source/backend restoration. A disappeared named choice is cleared on refresh, not silently replaced.
- Actual metadata listed Integrated Camera through MSMF and DSHOW plus an OBS Virtual Camera entry. No streams or frame probes were opened. The full suite passed 236 tests and Ruff.
- Added the native-source tutorial/README image using illustrative device names; inspected it with native Windows font rendering. Updated architecture, in-app help and handbook without claiming physical camera capture qualification.
- Refreshed the Studio on its idle Camera setup page and verified its native window responds. Handbook remains 245 pages/97 diagrams with zero diagram failures and zero overflow.
- Persisted the native-camera handoff as zmem `ep_834`; successful offload marker is `2026-11-02T14:33:17+05:30`. Shared chat and new incoming replies were read; no direct response obligation remained.

## 2026-11-02 - Native studio delivered and opened for review

- Completed all GUI workstreams: all 45 runtime controls plus model verification/force download and private recording, live per-eye calibration, source-free presets, native KC-box identity, themes, logs and the nine-step tutorial.
- Final validation: 224 tests and Ruff passed. Added explicit startup-cancellation coverage so a cancelled model initialization does not then acquire a camera/output, preserved zero-duration CLI probes, bound literal sources so they cannot become flags, and reported unexpected parser exits as failures.
- Captured/inspected actual synthetic dark/light/compact/tutorial widgets; updated README, book architecture/data contracts, algorithm/design-principle chapters, control rationale and operational tutorial.
- Final PDF: 245 pages and 97 diagrams, zero Mermaid errors and zero overflowing pages. All four existing models verified offline. Authored handbook builders are now versioned independently of ignored generated output.
- Recorded-input integration and live tuning succeeded. The measured post-warmup UI heartbeat p95/max were 31/47 ms on this machine; these do not establish end-to-end video latency, privacy coverage, or performance for every feature combination.
- Three completed milestone commits are c84e6d7 (research), f233d09 (runtime), and 93a1fb1 (GUI); final delivery evidence belongs to the documentation commit. Commits ran on the observed `workDesk/agentic_GUI` branch; no push was performed.
- Opened the final app in synthetic-demo mode and verified its actual native window is open/responding. Closed the earlier owned demo cooperatively before refreshing it. No live capture, real calling-app test, or private screenshot export occurred.
- User appearance/usability acceptance is still pending. Existing distance tracking, real calling-app qualification and recording timing issues were not claimed solved.
- Final source/log-boundary checks also cover quoted credentials, malformed source text, and already userinfo-redacted endpoints before they reach GUI log copies. The review demo was refreshed normally after these checks; no live source was opened by this agent.
- Persisted delivery as zmem `ep_829` and final 224-test follow-up as `ep_832`; advanced the successful full-offload marker to `2026-11-02T13:48:33+05:30`. Read the day's shared chat and recent direct mentions before refreshing; none required a reply from this persona.

## 2026-11-02 - Native desktop studio research and implementation

- User requested a native GUI, live left/right blink sliders, a KC-box icon, deep design research, numbered implementation TODOs, README screenshots, and complete architecture/design rationale. They selected all existing features and explicitly added a tutorial.
- Traced parser, composition/export order, both renderers' eye logic, action thresholds, capture shutdown, recorder and download helpers. Compared Qt Widgets, Tk/ttk and Dear PyGui using primary documentation before implementing.
- Created the optional PySide6 studio, shared runtime hooks, bounded preview/log bridge, common per-eye rules, live tuning, source-free presets, seven task pages and a nine-part tutorial. Model and private recording actions use owned asynchronous subprocesses.
- Preserved default face-only loss freeze and clean output before local debug. Raw modes require acknowledgement; experimental controls remain clearly marked.
- The initial full suite passed 220 tests and Ruff. Native widget captures covered dark/light/compact/tutorial; initial demo framing was visibly too large, then corrected without changing the real camera renderer.
- Offline integration on the private canonical recording used the real GUI, MediaPipe and GPU, displayed 55 packets with 54 effective detections, and exited 0. No private imagery was saved or published.
- Deferred source/model inspection out of live slider validation, avoiding repeated filesystem work on the Qt event thread. Final rerun, refreshed screenshots, book generation, milestone commits and user review remain in progress.
- Read the current shared chat and recent direct mentions before updating context; none targeted this persona. The older KardboardCode store remains unchanged.
- Final code validation passed 220 tests and Ruff after moving live-validation file inspection off the UI thread. A six-second private replay applied a live edit and recorded 359 post-warmup UI heartbeat samples: p95 31 ms, maximum 47 ms. No latency/accuracy generalization is justified.
- Refreshed and inspected the synthetic dark/compact screenshots after the framing correction. All four screenshot variants are present. The first handbook render produced 242 pages/97 diagrams with zero diagram failures; final screenshot/evidence inclusion and overflow checks remain.

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
