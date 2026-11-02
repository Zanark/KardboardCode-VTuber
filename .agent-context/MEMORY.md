# KardboardCode-VTuber Memory

> Durable project decisions for the KardboardCode VTuber engineering and streaming-output partner. New sessions must preserve these boundaries while rechecking mutable runtime state in source.

## People

No personal identities, device credentials, face imagery, or personal calibration measurements are retained here. Continuity is about the project's behavior and the user's explicitly stated workflow choices.

## Conventions

- Build one fixed KardboardCode cardboard-head character over the real camera feed. The source-runnable Python prototype is not a general model importer or replacement full-body-avatar product.
- Face-only tracking with fail-closed loss handling is the selected workflow. Body/hood fallback remains experimental and must not become the default without a new user decision.
- Preserve the PS1 visual identity: real low-poly textured 3D, low-resolution avatar rendering, nearest-neighbor scaling, sharp source camera, corrugated edges, aged asymmetric labels, headphones, and hollow neck-safe silhouette. Canonical specification: `docs\02-architecture\textured-3d-renderer.md`; overview: `README.md:54-60,118-168`.
- Keep visible letters in K/C order; K corresponds to anatomical left-eye control and C to anatomical right. Preserve established pose conventions rather than guessing from mirrored screen coordinates.
- Skeleton diagnostics are separate outlines, not filled geometry on the final composite. Source: `src\kardboard_vtuber\cli.py:500-599`.
- `--brightness` is processing-only. Capture, tracking input, final composition, and local debug must remain separate. Source: `cli.py:431-465,500-566`.
- Commands must include usable source setup. A variable assigned in another PowerShell terminal is not initialized here. Use the latest source explicitly supplied in the active conversation when appropriate; never save credential-bearing commands or source URLs into files or memories.
- Documentation is a technical book: numbered chapters, beginner explanations, source citations, diagrams, separate algorithms/design-principles coverage, reading paths, and captioned visual assets. Distinguish implemented, measured, and planned behavior. Source: `docs\README.md:126-135`; read-only origin `MEMORY.md:188-203`.
- Be concise, honest, and evidence-grounded. Respond in English/Latin script and romanize Hindi. Never claim to hear audio from transcribed input.

## Privacy and frame ownership

- Face-only output must be black before safe acquisition and reuse a copied last-safe composite on face loss, never fresh raw camera pixels. This is a fail-closed design requirement, not proof that every detected pose masks every identifying pixel.
- Synthetic face-mesh/XYZ diagnostics are the normal inspection path. `--debug-face-preview` explicitly exposes raw face imagery locally and must remain opt-in.
- Never restore arbitrary foreground using inferred monocular depth. Earlier experiments exposed face regions and were removed; general object occlusion requires aligned real depth.
- Optional hand occlusion uses conservative anatomical regions rather than a whole-hand convex hull; gaps must not restore face pixels. On effective tracking loss, do not composite fresh hand pixels over the frozen frame.
- Direct-camera export must happen before all local debug text, insets, raw-face preview, and preview resizing. Source: `cli.py:500-599`.
- The virtual-camera sender owns its repeated buffer; later local mutation must not contaminate output. It initializes that buffer to black. Source: `virtual_camera.py:40-62,68-104`.
- Do not persist stream authentication, camera addresses, tokens, raw recordings, or face images in this store, zmem, documentation, or Git. Do not promote private regression footage into public artifacts without explicit user direction.

## Runtime boundaries

- Latest-frame capture avoids inference queues. Retain original-resolution source pixels for output and submit a separately adjusted/downscaled processing image.
- MediaPipe face tracking is asynchronous. Library-neutral `FaceTrackingState` separates tracking from the renderer; filtered geometry and raw action signals have different consumers.
- The default renderer is ModernGL textured 3D; the procedural renderer is a comparison/fallback, not the canonical visual target.
- `--virtual-camera` enables tracking and cardboard rendering automatically. `--headless` suppresses windows but must not bypass rendering when camera output is enabled. Source: `cli.py:290-299,345-387,500-599`.
- Face-only virtual-camera rendering treats face-result ages outside 0-500 ms as no-face. Optional body/marker resolvers have separate freshness logic; do not generalize this gate to all modes. Source: `cli.py:447-465`.
- Processing brightness feeds face, hand, segmentation, body, and marker analysis; visible output begins with the unadjusted frame copy. Source: `cli.py:431-465,500-548`.
- Source errors should be explicit, before opening resources; an empty camera variable is an input failure, not a driver failure. Source: `cli.py:322-343`.

## Direct camera transport

- `pyproject.toml:22-27` declares the optional tracking and virtual-camera extras. Use `.venv312` for the established MediaPipe workflow; tracking is conditional on Python below 3.13.
- `VirtualCameraOutput` requests pyvirtualcam's `obs` backend and BGR format. It relies on an installed/registered OBS Windows camera component; it does not install a custom driver or rename the device.
- OBS need not run. Only one producer can own the OBS virtual-camera output. Consumer applications still apply their own permissions and policy restrictions.
- Default format is 1280x720, advertised 30 FPS; dimensions must be positive/even and FPS finite in 1-60. Inputs are fitted with black bars without stretching/cropping, and the output dimensions stay fixed. Source: `virtual_camera.py:13-25,68-95`.
- `repeat()` republishes the owned frame on capture timeouts. There is no separate fixed-rate producer, so advertised FPS is not guaranteed motion throughput. Source: `cli.py:411-429`; `virtual_camera.py:97-104`.
- Initialization, dependency, backend, and delivery failures surface actionable errors; cleanup releases the device. Source: `virtual_camera.py:31-62,97-109`; `cli.py:606-615`.
- Video only: microphone selection is separate. Prefer direct output for a calling-app camera; OBS Window Capture remains a separate streaming workflow.

## Experimental tracking gotchas

- Current hood markers are green on anatomical left and blue on anatomical right. Pink/red rear-marker logic was removed; do not restore it from old recordings or notes.
- Green/blue yaw signs and recent face/body size references were corrected after wrong-side and oversized-profile reports.
- No face plus no side marker is not a reliable rear-orientation sensor. The body-only rear mode is a requested heuristic with a short hold, not confirmation.
- Body/marker work required freshness bounds, history expiry, moved-marker reacquisition, and a torso plausibility gate. Review `tracking\hood_markers.py`, `tracking\body_head_fallback.py`, and `tracking\full_body.py` plus their tests before revisiting.
- A torso geometry gate only rejects some implausible estimates. Passing it does not establish ground-truth skeleton correctness.
- Tracking-state availability and retained-pose percentages must never be sold as visual accuracy, privacy coverage, or confidence that the live system works.
- Fixed-FPS recording can preserve frame/CSV counts while distorting elapsed-time playback when delivered capture FPS is lower. Recheck timestamps and duration, not only count alignment.
- Higher tracking width or processing brightness may help but has not been established as a reliable distance-tracking fix.
- Negotiated FPS is metadata; latest-frame overwrite counts can be healthy. Internal post-decode frame age excludes capture/encode/network/decode latency.

## Native studio conventions

- Keep the tracked root `release` folder synchronized with the latest public source/docs export.
  Run `python scripts\export_release.py` and `--check` after relevant changes; stage new public files first.
  `AGENTS.md` and `release\README.md` are the contributor contract.
- Release bundles are source-only unless packaging scope is explicitly expanded. Never include
  agent context, credentials/local config, raw media, downloaded models, environments or the
  generated archive inside itself. Commit public inputs and regenerate before manual publication.
- Native source selection uses Windows metadata in an owned subprocess, never VideoCapture frame probing. Always preserve the enumerated backend/index pair; CAP_ANY indices and explicit API indices are not interchangeable. Device paths/serials are not stored.
- Computer-camera and custom URL/file modes retain separate source/backend values in memory only. Numeric index 0 is a manual fallback, not a universal laptop-camera identity. Refresh/reselect after hardware changes; missing previous selections must not silently retarget.
- GUI scope is every existing operational feature, including experimental/raw modes, with a built-in tutorial; the selected default remains face-only. The user explicitly requested deep research, TODOs, layout/design rationale, and README screenshots.
- Keep PySide6 optional. Reuse the same CLI pipeline through toolkit-neutral runtime hooks; do not duplicate privacy/composition/export logic in widget code.
- Create, use and close the renderer/GL context on the session worker. Widgets stay on the main thread. Use a one-slot owned preview and bounded logs instead of queuing every video frame.
- Independent eye rules are shared by actions and both renderers. Live edits are one validated immutable tuple; invalid combinations retain the last applied valid configuration and display an error.
- Keep source/model filesystem inspection out of slider callbacks. Source URLs and raw consent are session-only, excluded from presets and command/log copies.
- Guided/free recording remains raw/private and uses the existing script. Its cooperative stop-file contract flushes the writer; it does not fix recording timing. Model helpers remain checksum-verifying explicit jobs.
- Synthetic demos/screenshots must say synthetic, never open a camera, and never publish virtual output. GUI appearance/heartbeat tests do not establish live accuracy or privacy.

## Gotchas

- The old `homeDesk\KardboardCode` store predates later changes: visible brightness, some flap decisions, body rendering, and original repository paths may be stale. Do not copy old values blindly.
- The root README and current CLI describe separate skeleton-only diagnostics; the engineering-book status table still contains an older synthetic-full-body description. Source wins until that documentation is deliberately reconciled.
- Published visual demos, a successful synthetic receiver, and historical tests do not prove current live hardware/app behavior.
- `YTScript` is a local production package, not evidence of a released video. Its README documents its private/ignored intent.

## Context-offload protocol

- Standing user instruction, 2026-10-11: before starting or resuming any VTuber work, read `README.md`, `STATE.md`, `MEMORY.md`, and `JOURNAL.md` in both `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context` and `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`. Neither store is optional.
- Write all new VTuber context updates only to `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`. The older store must remain read-only; do not mirror or backfill new updates into it.
- The required read-only origin at `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode` owns OBS/PNGTuber/Live2D history and original research. Reconcile overlap against newer verified decisions/current source; report an unavailable store rather than claiming complete hydration.
- `C:\devdesk\homedesk\ClipFarm` owns its separate editing workflow; do not treat it as the VTuber runtime store.
- Complete both-store reading before context-dependent VTuber work. Update only the repository-local STATE at milestones, MEMORY when durable facts change, and JOURNAL frequently/newest first.
- Full offloads require a non-sensitive zmem episodic entry, an exact successful-offload timestamp, and a refreshed Context Mesh. Reconcile whenever that marker is missing, invalid, or at least 12 hours old.
- All stale snapshots and historical measurements must remain explicitly labelled. Never fabricate fresh state to fill an offload.
