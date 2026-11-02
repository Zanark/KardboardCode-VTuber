# KardboardCode-VTuber Journal

> Activity for the KardboardCode VTuber engineering and streaming-output partner. Resume with STATE and MEMORY; this journal explains how decisions changed.
>
> Newest at top. This repository-local store began on 2026-10-11. Earlier work below is retrospective continuity, not evidence that this store existed then.

## 2026-11-02 - Borderless README gallery completed

- User rejected table rows/borders around README images, while explicitly approving the
  original-background / green-screen two-GIF composition. Preserved that pair side by side,
  removed its table frame too, and stacked all other images at full content width.
- Actual browser checks at 1120px and 390px: 31 loaded images, zero tables/image borders,
  all 29 non-paired images full width, paired GIFs aligned and no horizontal overflow.
  Source inventory, order, captions and links retained; no image files or runtime code changed.
- Recorded the convention in branding docs and workstream 11. No handbook/application rebuild.
  Public source committed as `4590ca7e6a6fa4b05ac13e1a9dae866782990e56`; artifacts `a35f331`.
- Current v1.1.0 ZIP is 33,147,025 bytes, sourceModified=false, source fingerprint
  `05e322ac47665f43f619792bb0df6277f7974123c5d69725ce4c744f326baea3`.
  Export freshness and all six committed release-file bytes are checked. No remote publication.
- All new context stays here only; older KardboardCode context remains read-only.
- Read current shared chat/recent mentions; no new response obligation or useful hook required
  another post. Persisted the layout decision as zmem `ep_846`, then advanced the offload marker
  to `2026-11-02T20:19:41+05:30`.

## 2026-11-02 - Fifteen-point Studio feedback completed as v1.1.0

- User supplied actual-use screenshots and requested a coherent layout/workflow refinement.
  Raw-face/debug overlays obscure the preview, disabled and checked states are unclear,
  closed-eye output is unreliable, and the clean OBS-capturable output window is missing.
- Required two front-level modes: live camera and processing an existing video into a new
  cardboard-avatar output. Existing private raw capture is an advanced utility, not that mode.
- User selected both export formats with lossless MKV default; MP4 must be labelled high-quality
  but lossy. Preserve source dimensions/timing/audio where supported and reject unsupported
  quality conversions explicitly. No source/camera access is authorized automatically.
- README milestone cards should go; transparent SVG is preferred for decorative UI art.
  The runtime-avatar hero belongs directly below the top banner and should share its palette.
- Created workstream 10 and began direct source tracing. No private screenshots copied into
  public documentation; older context and sibling stores remain read-only.
- Implementation milestone: both banner-derived palettes, visible tick/lock states, separate
  diagnostic buffers, full-resolution clean output window, bottom CLI/log tabs, preset resolutions,
  clarified camera routes, guided eye calibration and raw-eye rendering are implemented.
- Added synchronous VIDEO processing with lossless MKV / optional high-quality MP4, preserved
  dimensions/PTS and copied compatible audio. No-overwrite publication, cancel cleanup, HDR/extra
  stream refusal and a Qt-free video CLI are included. Advanced RAW capture remains Live-only.
- Full suite passed 266 tests and Ruff. Real private 30-frame MediaPipe VIDEO + GPU export at
  1080x1920 completed with face detection; temporary files removed. Synthetic encoded tests cover
  lossless pixels, VFR spacing, PCM/AAC packet identity and concurrent destination safety.
- Refreshed/inspected eight native synthetic UI views, tighter icons and the fully framed hero.
  Fixed an actual missing checkbox-tick resource issue exposed by native review; pixel-level
  regression now checks it. Body-calibration text is also excluded from clean program output.
- UI demo service intervals after warm-up: 161 samples, p95 31ms/max 32ms on this machine.
  This is not end-to-end video latency or real-camera qualification. Finishing handbook/export.
- Completed handbook: 256 pages/99 diagrams, zero failures/overflow. Actual extracted v1.1.0
  source launches all three help entry points, renders Studio/clean output and opens VIDEO mode.
- Public inputs committed as `11a0e2b2aa261875f89534612194137584fd67fe`; final artifacts as
  `c803653`. ZIP 33,145,546 bytes, sourceModified=false, fingerprint
  `34f7fd0e9bddea186631cf296612a38e7fc8c641654ea548a0fecdde7c7bf1bd`.
  Export freshness and all six committed release-file bytes are verified.
- No live camera or user Studio process was touched; no remote tag/push/merge/publication.
  Owner must restart Studio to load changes and calibrate actual open/closed eye scores.
  Unsupported video formats remain explicit limitations; real calling-app/privacy qualification
  and the old private recorder's fixed-FPS duration issue are not claimed solved.
- Read the current-day shared chat, latest general history and recent mentions; acknowledged
  the new reply to this persona with an emoji in its own file only. No routine work post.
- Persisted the completed handoff as zmem `ep_844`; after store/episode persistence, advanced
  the exact full-offload marker to `2026-11-02T20:07:23+05:30`.

## 2026-11-02 - Explicit post-delivery context refresh

- User requested a fresh offload after the visual README delivery. Reconciled current state,
  durable conventions, prior handoff episode, clean Git history and unchanged v1.0.0 manifest.
- Public inputs remain `4b85fad`, release artifacts `f607adc`, and the preceding delivery context
  was committed as `4219b61`. No application/source/artwork/release regeneration was requested.
- Preserved the completed 29-image/eight-graphic README, three named guides, font licenses,
  first-official source-release designation, manual-publication boundary and unresolved limits.
- Added exact local preview/contact-sheet paths so a resumed session can review existing results
  without regenerating or reopening a camera. Prior validation remains dated evidence, not new tests.
- Read the current day's chat, latest general messages and recent mentions. No new incoming
  obligation or natural new contribution required another social post.
- Updated only this repository's current context. The older KardboardCode store and all sibling
  stores remain read-only; no live capture, model download, publication, tag, merge or push.
- Persisted this requested refresh as zmem `ep_841`, then advanced the successful-offload marker
  to `2026-11-02T18:12:06+05:30` after store/episode persistence.

## 2026-11-02 - Visual README redesign completed

- User requested fewer front-page words, many pretty images/banners, matching typography and
  named files for extra text. Rebuilt the README as an image-first showcase, retaining all
  existing public imagery and one actual Studio screenshot above Current milestone.
- Created eight reproducible kraft-paper/deep-green/mint graphics using the unchanged supplied
  logo. Pinned Silkscreen and Barlow Condensed font files from Google Fonts; included both OFL
  licenses. Fonts are baked into PNGs, without viewer-installed fonts or custom GitHub CSS.
- Moved setup, features/flags and camera/virtual-output/troubleshooting into three named guides.
  Preserved all original README CLI flags through those guides and linked release instructions.
- Browser previews at 1120px and 390px load all 29 images with no page/table overflow; visible
  text is 324 words. Approximate source prose is 75% lower. All six new guide diagrams parse.
- Ruff and 11 targeted branding/export tests passed; master preservation, banner repeatability,
  87 relative references, alt text and screenshot ordering are checked. All six guide diagrams
  were also rendered to SVG. All 16 prior front-page public images remain.
- Public source committed as `4b85fad7d6e6682342eecbff83002db701f77cd3`; generated source handoff
  committed as `f607adc`. v1.0.0 remains the first official version, with latest local source
  fingerprint `defd8552ba1d1557e4b1a49b239faad7ae44ed6054b9c8ffc32a5521f344e70e`.
  ZIP: 32,592,509 bytes; sourceModified=false. All six release files match committed Git bytes.
- Canonical app logo, runtime behavior and GUI fonts are unchanged. No new camera capture,
  model download, private imagery, remote tag/push/merge/publication or installer was introduced.
- Read the day's shared chat, latest general messages and recent mentions before refreshing.
  No incoming reply obligation remained; joined the new calculator joke from this session's own
  persona file only. The older KardboardCode store and all sibling stores remain read-only.
- Persisted the completed redesign as zmem `ep_840`; after store/episode persistence, advanced
  the exact full-offload marker to `2026-11-02T18:05:02+05:30`.

## 2026-11-02 - Supplied logo and first official v1.0.0 release completed

- User supplied voxel KC cardboard-box artwork for the tool logo and asked that the post-logo
  version count as the first official release. Preparing v1.0.0; GitHub currently lists no releases.
- Preserved the original 1345x1169 RGBA PNG byte-for-byte. Derived a transparent PNG and seven-size
  Windows ICO using existing OpenCV/NumPy dependencies, without modifying the avatar mesh.
  Master SHA256: `9cefba6bc42ad8da9ac6b49c1d3543fba86cd8832bbc93059e8969419378e852`.
- Updated package versions, README branding/design/architecture, and five real Windows screenshot
  variants. Contact-sheet inspection confirmed the new header identity; native-camera controls use
  illustrative names and no capture. One tool screenshot remains above Current milestone.
- Full suite passed 245 tests and Ruff. Native Qt decodes all seven ICO sizes. The engineering
  handbook was rebuilt to 247 pages/97 diagrams with zero Mermaid failures and zero overflow.
- Extracted the v1.0.0 source ZIP privately: CLI/GUI help and a real synthetic GUI preview loaded
  the extracted modules/resources and exited normally. The temporary extraction was removed.
- Public inputs committed as `92c32b93039b35942de63ff57273feb149a05e95`; final generated artifacts
  committed as `e7ac0e3`. ZIP is 32,097,090 bytes, manifest `sourceModified=false`, fingerprint
  `0d046cfd359d2b5dbb93f464cadea0feef2433322a64a75dbd0b21ce0201bec7`.
  Export freshness and all six committed release-file bytes were verified after artifact commit.
- No tag, release, merge, push, live camera or model download was performed. Publication is still
  manual; logo/UI visual acceptance, distant tracking, calling-app qualification and recording
  timing remain distinct/unverified.
- User explicitly requested a context refresh after the current work. Updated only this current
  store; mandatory older KardboardCode context remains read-only. Read the day's shared chat,
  latest general messages and recent mentions; no unacknowledged incoming obligation remained.
- Persisted the completed handoff as zmem `ep_838` and advanced the exact full-offload marker
  to `2026-11-02T17:35:11+05:30` after store/episode persistence succeeded.

## 2026-11-02 - README layout and local source release preparation

- User requested moving GUI text/gallery below Current milestone while leaving one tool screenshot above it. Reordered the existing sections without discarding the other avatar/demo images.
- GitHub reported read-only repository authorization and no existing releases. User explicitly redirected to a separate tracked local release folder that remains current with the latest tool export. No account switch or publishing workaround was attempted.
- Prepared v0.2.0 package/version alignment, release notes, manual setup/publication context, and a standard-library public-source ZIP exporter. Added AGENTS release-freshness guidance and workstream 07.
- Export excludes private context, local credentials/config, recordings, models, environments, caches and generated self-recursion. Authored release instructions/notes stay inside source packages so README links work.
- Full suite passed 241 tests and Ruff. Verified stale/tampered detection, staged-file gating, repeatability and clean-commit provenance refresh. README order has exactly one tool image before the milestone.
- A candidate archive was extracted privately and launched both help entry points and the real synthetic GUI preview from its extracted root. No camera capture, model download or private imagery was used.
- Final handoff uses a public-input commit followed by a clean-provenance archive/export commit. Remote publication remains the owner's action; no tag, release, merge or push has been created.
- Public inputs were committed as `e5e2db3`; the final v0.2.0 export passed freshness/content/checksum checks with `sourceModified=false`. The tracked handoff ZIP is about 30 MB.
- A Git line-ending warning exposed a checksum portability risk. Pinned release text to LF,
  kept ZIPs binary, and added committed-byte verification to the exporter tests. Final clean
  source commit is `1067ade`, final asset commit `dc72392`; all six Git blobs match the verified
  files exactly. Final archive is 29,909,091 bytes and `--check` passes after artifact commit.
- Persisted the release handoff as zmem `ep_836` and set the full-offload marker to `2026-11-02T17:06:20+05:30`. Repository-memory API was unavailable; the durable rule remains in AGENTS.md, release instructions, this store and zmem.
- Final byte-stable provenance is persisted as `ep_837`; successful offload marker advanced to
  `2026-11-02T17:13:00+05:30`. No public inputs changed during this private-context update.

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
