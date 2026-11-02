# KardboardCode-VTuber Memory

> Durable project decisions for the KardboardCode VTuber engineering and streaming-output partner. New sessions must preserve these boundaries while rechecking mutable runtime state in source.

## People

No personal identities, device credentials, face imagery, or personal calibration measurements are retained here. Continuity is about the project's behavior and the user's explicitly stated workflow choices.

## Conventions

- The exhaustive development documentary is a separate private package at
  `YTScript\DevelopmentJourney`, not the engineering handbook. Its narrative and unabridged
  source/task appendices are local/Git-ignored and must not enter public release exports.
- Documentary editions freeze their corpus/cutoff and original/sanitized hashes. Never silently
  re-collect from newer live context or collapse repeated historical tasks into a false final state.
  Preserve every source occurrence and distinguish topic associations from actual dependency/
  resolution evidence. The current edition covers through 2026-11-02T21:46:13.268+05:30.
- Documentary PDF verification compares complete source-record text inside each printed record
  span, alongside task/message presence, chapter order, links, figures, bounds and stable folios.
  An ID count or a PDF that merely opens is not a completeness check. Preserve privacy redactions.
- Keep the front README animation-first and minimal: branding banner, runtime hero, then all
  three existing GIFs immediately below them. Only dark/light Studio screenshots remain on
  the front. Detailed static imagery belongs in the linked `docs\visual-gallery.md`, organized
  with captions. Keep setup/features/camera/troubleshooting prose in `docs\guides`.
- README image galleries must not use table rows/cells or visible borders. Stack other images
  at full content width. Keep only the explicitly approved original-background / green-screen
  GIF comparison side by side, using borderless plain HTML rather than a table.
- README artwork uses Silkscreen and Barlow Condensed. The top banner/runtime hero use PNG;
  decorative section/footer lettering is transparent SVG with outlined fonts, not raster UI
  cards or a solid canvas. No milestone image cards. The runtime hero follows the top banner.
  `scripts\build_readme_art.py` owns this artwork; GitHub loads no custom stylesheet/web font.
  Preserve the bundled OFL licenses and unchanged logo master. Rebuild on package-version
  changes because the hero reads its version label from pyproject.
- Build one fixed KardboardCode cardboard-head character over the real camera feed. The source-runnable Python prototype is not a general model importer or replacement full-body-avatar product.
- Face-only tracking with fail-closed loss handling is the selected workflow. Body/hood fallback remains experimental and must not become the default without a new user decision.
- LIVE and VIDEO are distinct front-level modes. VIDEO means avatar-processing an existing
  recording, not collecting raw camera footage. Old private RAW capture is an advanced Live-only utility.
- Preserve the PS1 visual identity: real low-poly textured 3D, low-resolution avatar rendering, nearest-neighbor scaling, sharp source camera, corrugated edges, aged asymmetric labels, headphones, and hollow neck-safe silhouette. Canonical specification: `docs\02-architecture\textured-3d-renderer.md`; overview: `README.md:54-60,118-168`.
- Keep visible letters in K/C order; K corresponds to anatomical left-eye control and C to anatomical right. Preserve established pose conventions rather than guessing from mirrored screen coordinates.
- Skeleton diagnostics are separate outlines, not filled geometry on the final composite. Source: `src\kardboard_vtuber\cli.py:500-599`.
- `--brightness` is processing-only. Capture, tracking input, final composition, and local debug must remain separate. Source: `cli.py:431-465,500-566`.
- Commands must include usable source setup. A variable assigned in another PowerShell terminal is not initialized here. Use the latest source explicitly supplied in the active conversation when appropriate; never save credential-bearing commands or source URLs into files or memories.
- Documentation is a technical book: numbered chapters, beginner explanations, source citations, diagrams, separate algorithms/design-principles coverage, reading paths, and captioned visual assets. Distinguish implemented, measured, and planned behavior. Source: `docs\README.md:126-135`; read-only origin `MEMORY.md:188-203`.
- Be concise, honest, and evidence-grounded. Respond in English/Latin script and romanize Hindi. Never claim to hear audio from transcribed input.

## Privacy and frame ownership

- Face-only output must be black before safe acquisition and reuse a copied last-safe composite on face loss, never fresh raw camera pixels. This is a fail-closed design requirement, not proof that every detected pose masks every identifying pixel.
- Synthetic face-mesh/XYZ diagnostics are the normal inspection path. `--debug-face-preview`
  exposes raw face imagery locally and stays opt-in. Studio places raw face above face/pose
  or body in a right-hand diagnostic rail, never over the clean program image. Tools contains
  numeric Signals, not tiny image previews. CLI local overlays remain available.
- The separate clean output window is for OBS Window Capture and is independent of OBS Virtual
  Camera. It receives only owned clean frames, never raw/debug/body-calibration text. Unmasked
  camera modes do not populate that channel. Windows controls native icon-slot size.
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

- Numeric steps use explicit packaged plus/minus SVGs with contrast and muted disabled/boundary
  states. Qt's native PlusMinus setting alone painted empty slots through this custom stylesheet.
  Verify actual glyph pixels/shapes and click behaviour, not only a button-symbol property.
  The Live/Video QTabBar disables drawBase so no baseline extends beyond its buttons.
- Apply numeric padding to the embedded spin-box QLineEdit after theme styling, not only the
  outer QSS box. Current text margins are6px left/3px right; native ink-inset tests cover both
  palettes, disabled states and integer/decimal controls without shrinking the step targets.
- Custom CLI numeric parser types need an explicit numeric GUI field kind. preview_height uses
  the integer kind; a generic QLineEdit returned text that could not pass numeric validation.
  Verify real nondefault control-to-parser forwarding, not only the option inventory.
- Video availability/CLI copying reuse canonical VIDEO_FIELDS. Already-mirrored Video input
  is owned by its Video file checkbox; the separate Camera field stays Live-only. Video always
  tracks/renders; ignored Live controls must not look like effective Video knobs.
- The owner chose the left settings inspector, main preview directly beside it and optional
  right-hand stacked visual diagnostics. Raw face belongs above Face / pose or Body, with both
  requested images visible without opening Tools. Reclaim the rail when channels are off;
  protect actual visible and fitted image area, not only isVisible or declared minima.
  Default startup is a
  display-fitted 16:9 workbench; resizing stays responsive and never changes source/output
  video dimensions or stretches/crops pixels. Keep all operating options reachable through
  labelled sections rather than expanding every advanced field permanently.
- Preview containment must be checked against actual ancestor-clipped visible regions, not
  only isVisible or the canvas minimum size. Prevent splitter collapse; secondary Tools must
  shrink/scroll rather than force a fixed-height dock to clip the viewer. Keep Stop, true
  state, privacy warnings, errors and video progress visible outside optional details.
- Tools / Ctrl+J contains Logs, CLI and numeric Signals, closed by default. Hidden tools still
  collect bounded logs and owned diagnostic data. Keep compact eye decisions near tuning,
  detailed numeric signals in Tools, and the separate clean-output window independent.
- Preserve the owner's preferred rounded camera-FPS/tracking-FPS/internal-frame-age/output
  cards below the preview beside Tools. Keep them visible outside the drawer; do not flatten
  them into Signals text. The drawer belongs under the viewer only, keeping settings full-height.
- Propagate the selected diagnostic rail's real minimum height into its horizontal splitter;
  otherwise footer content can override nested minimum-size hints and clip diagnostic pixels.
  Native text-fit checks require a real font backend: offscreen Qt without Segoe UI returns
  placeholder metrics, not proof of Windows caption/value readability.
- Keep Show clean output visible beside the Live preview, sharing the View-menu action.
  Auto-open is a separate startup preference. Closing hides the same window without stopping
  its worker; manual reopening works with Auto-open off and displays current owned clean pixels.
  Idle opening is black/no capture; raw/headless/Video states cannot display clean output.
- Qt's zero QScrollArea minimum retains its 70px minimum hint. Tools uses an explicit 1px
  minimum so secondary content can yield space. Error details may shrink within 48-68px while
  keeping all text scrollable. Neither may clip the main or diagnostic canvases at compact sizes.
- Successful Studio VIDEO exports open the actual completed worker result in the OS default
  player, on the UI thread after cleanup. Never use editable output text to choose playback.
  Cancellation/failure must not launch. Launch refusal preserves the saved file and displays
  an actionable path/error. CLI exports stay noninteractive and Qt-free.
- Windows setup is the explicitly chosen online, per-user x64 bootstrap, not an offline
  PyInstaller bundle. Include patched private Python and the application wheel; first launch
  offers hash-locked upstream wheels. Models remain explicit; OBS's camera component is separate.
  Keep installed resources/helper scripts separate from writable AppData models/presets/recordings.
  Never change system Python/PATH or disable TLS, app-control or agent protections.
- Package downloads may use an existing verified HTTPS mirror. Copy network-only pip settings
  into a cleaned child environment, reject trusted-host/HTTP indexes, and ignore user-target/prefix
  overrides. Validate wheel hashes against authoritative PyPI metadata when creating the lock.
  Never embed feed configuration/credentials in public artifacts or print credential-bearing URLs.
- Dark-theme sliders use cardboard brown while mint continues to distinguish live/checked states.
  This is the user's KardboardCode theme refinement, not a new global palette preference.
- Both GUI palettes follow the banner: forest/mint dark and kraft/cream light. Checkboxes need
  visible contrasting ticks and distinct unchecked/disabled states; lock/live-only badges explain
  unavailable controls. Native OS title colors are per-window, not global Windows settings.
- Eye rendering uses raw closure signals with filtered geometry. Guided OPEN/BOTH-CLOSED samples
  derive the whole compatible threshold tuple; overlapping ranges fail explicitly. Raise blink
  thresholds for missed closures, lower for false closures. No face images are saved by calibration.
- VIDEO defaults to lossless FFV1/MKV; user explicitly chose optional high-quality H.264/MP4
  CRF17 as a lossy alternative. Preserve every frame, source dimensions/timing within container
  precision and compatible audio packets. Never silently downconvert unsupported inputs or
  overwrite input/existing output. Synchronous MediaPipe VIDEO mode, not live/latest-frame capture.
- Current video support is opaque progressive square-pixel 8-bit SDR; HDR/alpha/rotation/interlaced/
  invalid timing and extra stream cases fail visibly. Lossless means processed RGB pixels, not
  byte-identical modified source. Hard-link publication needs a supporting destination filesystem.
- Output dimensions in Studio use standard/monitor presets. Offline exports always inherit input
  dimensions; moving monitors does not change an active virtual stream. CLI width/height remain.
- Official tool branding is the supplied voxel KC box PNG at
  `src\kardboard_vtuber\gui\assets\kardboardcode-logo.png`, retained byte-for-byte. Derive its
  transparent application PNG and seven-size Windows ICO using `scripts\build_branding.py`.
  Do not redraw it or modify the avatar mesh merely to change tool branding.
- v1.0.0 is the first official source-release version. Earlier v0.2.0 packages were unpublished
  local staging; designation of an official version is not evidence of remote publication.
- Keep the tracked root `release` folder synchronized with the latest public source/docs export.
  Run `python scripts\export_release.py` and `--check` after relevant changes; stage new public files first.
  `AGENTS.md` and `release\README.md` are the contributor contract.
- The source ZIP remains source-only; the separate online MSI intentionally includes patched
  private Python and the own wheel. Keep their receipts/checksums separate. Never include agent
  context, credentials/local config, raw media, downloaded models, development environments or
  generated-artifact recursion. Commit public inputs and regenerate before manual publication.
- Installer fingerprints include README because it is embedded in wheel metadata. Rebuild
  after README/runtime-input changes; --refresh-provenance only updates a matching external
  receipt, never a stale MSI. Installer configuration and release text use canonical LF.
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

- A gh viewerPermission READ report did not predict the configured Git transport's outcome:
  a normal user-authorized push succeeded on 2026-11-02. When authorized, verify the actual
  push/remote hash rather than assume denial or invent an identity explanation. Never switch
  accounts, extract credentials, force-push or bypass repository policy to resolve a mismatch.
- Windows Qt wheels contain deeply nested resource paths. A normal private prefix failed at
  MAX_PATH in the real MSI test; a canonical extended-length prefix successfully installed
  all exact locked wheels without changing machine-wide settings. Pass it to both dependency
  and own-wheel installs, and force-reinstall exact locked wheels on retry. The corrected final
  MSI has passed actual online setup, native application/helpers/video and complete uninstall.
- MSI bytecode-cache cleanup requires each named __pycache__ directory to have its own stable
  component, null/directory keypath and CreateFolder ownership. Remove only its *.pyc files;
  let RemoveFolders remove the directory afterward. Attaching directory removal to parent file
  components left empty directories in real uninstall tests. Do not remove arbitrary user data.
- The old `homeDesk\KardboardCode` store predates later changes: visible brightness, some flap decisions, body rendering, and original repository paths may be stale. Do not copy old values blindly.
- The root README and current CLI describe separate skeleton-only diagnostics; the engineering-book status table still contains an older synthetic-full-body description. Source wins until that documentation is deliberately reconciled.
- Published visual demos, a successful synthetic receiver, and historical tests do not prove current live hardware/app behavior.
- `YTScript` is a local production package, not evidence of a released video. Its README documents its private/ignored intent.

## Context-offload protocol

- When the mesh exposes social.archive, routine refreshes read only the active messages,
  threads, attention and generated profiles in context-index.json. Do not proactively read
  archived chats or historical source arrays, revive their obligations or reset identity.
  Archived conversations require explicit user opt-in and remain read-only.
- Standing user instruction, 2026-10-11: before starting or resuming any VTuber work, read `README.md`, `STATE.md`, `MEMORY.md`, and `JOURNAL.md` in both `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode\.agent-context` and `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`. Neither store is optional.
- Write all new VTuber context updates only to `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber\.agent-context`. The older store must remain read-only; do not mirror or backfill new updates into it.
- The required read-only origin at `C:\devdesk\Copilot\CopilotSessions\homeDesk\KardboardCode` owns OBS/PNGTuber/Live2D history and original research. Reconcile overlap against newer verified decisions/current source; report an unavailable store rather than claiming complete hydration.
- `C:\devdesk\homedesk\ClipFarm` owns its separate editing workflow; do not treat it as the VTuber runtime store.
- Complete both-store reading before context-dependent VTuber work. Update only the repository-local STATE at milestones, MEMORY when durable facts change, and JOURNAL frequently/newest first.
- Full offloads require a non-sensitive zmem episodic entry, an exact successful-offload timestamp, and a refreshed Context Mesh. Reconcile whenever that marker is missing, invalid, or at least 12 hours old.
- All stale snapshots and historical measurements must remain explicitly labelled. Never fabricate fresh state to fill an offload.
