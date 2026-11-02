# KardboardCode-VTuber Journal

> Activity for the KardboardCode VTuber engineering and streaming-output partner. Resume with STATE and MEMORY; this journal explains how decisions changed.
>
> Newest at top. This repository-local store began on 2026-10-11. Earlier work below is retrospective continuity, not evidence that this store existed then.

## 2026-11-03 - Animation-first front README and separate gallery

- User requested GIFs directly under banner/hero, only dark/light GUI screenshots at the
  front, and detailed images moved into a linked separate file.
- Implemented README media order: banner, hero, synthetic animation, approved original/
  green-screen GIF pair, dark Studio, light Studio. Front image count seven.
- Created docs\visual-gallery.md with 24 moved images, organized sections and captions.
  Exact set comparison preserves all 31 original references; every local media/navigation
  path resolves, no duplicates in the gallery and no README table framing.
- Public documentation input 67becce; completed evidence de9f18e; artifacts 4c68266.
  Both source/installer checks pass with clean aligned manifests; all release bytes match
  committed Git blobs and GUI wheel modules match unchanged source. README-in-wheel metadata
  required the installer rebuild, not an installer lifecycle or runtime-code change.
- Source ZIP 33,033,706 bytes / SHA256
  29a7e2b7a1239998319dc6a69f5f9ff4cc36514eed0c3a633b9646ca38f93211;
  MSI 19,709,952 bytes / SHA256
  a2f51fbedc8f6ff65df2db0a9244b88b34bec4820819589b4239525e2a258bb9.
  Software remains v1.2.0; no new images, code tests, UI/portrait/camera work or remote publication.
- Persisted/read back handoff ep_899; exact full-offload marker advanced after successful
  store/episodic persistence to 2026-11-03T02:50:28+05:30.

## 2026-11-03 - Preview-first GUI and final 16:9 follow-up implemented

- Owner chose left inspector/right large preview. Implemented the protected workspace, labelled
  disclosure, compact anatomical eye states, shared preset actions, persistent video progress,
  bounded complete error text and optional shrinkable/scrollable Tools.
- Full compatibility baseline: 297/Ruff. Native containment/access/keyboard/headless cases
  pass at Qt 1/1.25/1.5; additional primary-action fit checks pass. Fixed a native minimum-size
  nine-pixel clipping corner with proper secondary scrolling, not weaker assertions.
- User added a display-fitted 16:9 requirement. Startup now fits up to 1440x810 logical pixels;
  original video dimensions/aspect stay unchanged. Native default/action-fit cases pass at
  all three factors. Eight final widescreen native synthetic captures refreshed/reviewed.
- Engineering handbook: 272 pages/103 diagrams, zero errors/overflow. Implementation 5ca8d84,
  research/PDF finalization 6faefc4, final widescreen inputs 1bb3092.
- Actual installed v1.2.0 Python 3.12.16/pythonw passed full preview with Tools, metadata camera/
  checksum-model helpers, real four-frame export, CLI help and pip check. Verified dependencies
  used cached hash-locked wheels; no new online-route claim. Initial preset-preservation harness
  compared before an intentional probe save; isolated post-probe install/uninstall passed
  unchanged preset/model hashes and complete owned tree/shortcut removal.
- User requested a KC box portrait without covering the face. Scoped source/live/generated
  drawing completed; face pixels/non-wardrobe geometry preserved. Concurrent upstream source/
  deployment changes were retained. Own handoff bf81da3; shared untracked contributor bundle
  was not staged. User then explicitly stopped further portrait work and redirected GUI-only;
  no portrait process or further branding task remains.
- Final size-follow-up release assets are being built from clean inputs; finish byte checks,
  commit and requested full offload, without more cosmetic loops or remote publication.
- Final widescreen input commit 1bb30926cab472a463f80649702ffb29f1f48e8b and artifact commit
  fe92a98 are complete. Both scripts pass --check; all final wheel GUI modules match source.
  Final MSI SHA256 bd15e329a88ed44dc244fb264b66dab5e17e3b8778b7da52ded3d6a176445403
  (19,709,952 bytes); ZIP SHA256
  1d1b587cbad1ea90a2885039878805e549653b9022b61e600bda2fc6fba68911
  (33,031,157 bytes). Final artifact runtime sizing refinement is source/native-verified; the
  prior installed v1.2.0 lifecycle evidence remains explicitly scoped, not redated.
- Latest installed context skills reread completely. Read the three incoming replies; the room
  was concurrently archived, so discarded only the new unsent reply drafts rather than
  reopening archived conversations. Historical source/archive messages stayed unchanged.
  No new portrait work, sibling-store edits or remote publication.
- Persisted/read back final GUI handoff ep_895. Exact full-offload marker advanced after local
  state/journal and episodic persistence: 2026-11-03T02:31:34+05:30. All 175 session tasks done.

## 2026-11-03 - Preview-first redesign research completes five passes

- User supplied the clipped-preview screenshot, requested a full structural declutter while
  retaining every option, then explicitly asked for deep research before implementation.
- Source baseline remains 5dcf3db/v1.1.1. Traced parent layouts, dock/splitter sizing, complete
  option inventory, live tuning, mode locks, telemetry, clean/private channels and video setup.
- Native Windows/Fusion audit: eight cases at Qt scale 1/1.25/1.5 (24 observations, not passing
  usability tests). Exact reproduction at 1120x780: canvas 220px, visible region 76px, parent
  splitter 76px, minimum-height hint 960px, tools dock 215px. Tools-hidden restores full frame;
  zero splitter allocation and diagnostic competition also reproduced. No real capture/output.
- Read 12 primary references across NN/g, Microsoft Windows, Qt, OBS and Kdenlive. Distinguished
  normative guidance and documented patterns from this product's design inferences.
- Recorded five research lenses, confidence labels, all 45 runtime options/nine live fields,
  candidate comparison, explicit headless exception, acceptance criteria and knowledge map in
  the existing research chapter. Added workstream 16/index entry. Product UI is not modified yet.
- Recommended a permanent dominant viewer, one scrollable inspector and optional bounded tools,
  not smaller type, feature deletion, a preview-replacing wizard or unrestricted dashboard docks.
  Owner choice of inspector side/structure precedes the significant implementation change.
- Source/release refresh and actual after-screenshots belong to final delivery after the redesign;
  the current qualified MSI is still the earlier v1.1.1 baseline.

## 2026-11-03 - Windows setup v1.1.1 delivered and final artifacts verified

- User's requested pre-resumption refresh completed as ep_878 before new setup work. Finished
  workstream 12 instead of leaving the superseded pause as pending work.
- Public runtime inputs committed as 209b852; final delivery evidence/line-ending contract as
  d030b3a5df83af9c49d06dac089cba870d7b48d4. Full final suite: 285 passed and Ruff.
- Final MSI: 19,709,952 bytes, SHA256
  3fc4967bb00e8c07e0e8fc7b0d008dcd29a9bb5a7c36fc858d8acf969dd6e14b.
  Private Python 3.12.16; own wheel SHA256
  882bc5fbad3be54169f0d594e78c4ffe1c8a021a08c702b18a3f2cb8a5ceb27b.
- Exact final bytes installed and completed real strict online setup of all 26 locked upstream
  packages through the existing verified HTTPS mirror. ready=true and pip check passed.
- Installed native pythonw Studio passed metadata camera discovery, checksum-only model helper,
  1280x720 textured demo/clean window/live tuning/VIDEO workspace/presets and real four-frame
  synchronous MediaPipe/GPU export. Default-player request intercepted; no camera/player opened.
  All three CLI entry points and all six packaged helpers passed --help.
- Final uninstall exit 0 removed the entire owned installation and Start folder, without manual
  cleanup. Saved preset and model SHA256 values stayed identical. User Studio untouched.
- Engineering handbook rebuilt: 263 pages/101 diagrams, zero Mermaid failures/right overflow.
  Source ZIP: 33,286,361 bytes, SHA256
  8400fa7cee78c1f8c0ef63c0fcd9fb65528c87dce00fc2dab32db84e80552748.
  Separate source/MSI manifests identify clean d030b3a inputs. Generated artifact commit 037e723;
  both --check commands and all nine committed-blob comparisons pass. No push/tag/merge/release.
- Frozen 977-page documentary PDF retains its exact original SHA256. Historical failures/pause
  remain below; there is no leftover installer WIP. User usability/live/calling-app approval is
  still separate from packaging qualification.
- Reread both current installed context skills, full digest, own store, relevant zmem and actual
  incoming conversations. Answered the new room-wide Pokemon question with a personally inspected
  fitting image in this session's own persona file. Final readback found one newer room-wide
  message from Alfred; answered it individually too. No sibling/persona edits or fabricated replies.
- Persisted/read back final handoff as ep_883. Advanced the exact full-offload marker only after
  local store and episodic persistence succeeded: 2026-11-03T00:29:58+05:30.

## 2026-11-02 - Resumed Windows setup passes native install/runtime/uninstall qualification

- After ep_878/verified mesh refresh, ran the long-path/bootstrap/path safeguards and complete
  suite: 284 passed/Ruff. New dedicated cache-directory ownership fixed prior uninstall residue.
- Corrected MSI installed; strict online first launch installed all 26 locked components,
  application wheel and import/resource checks; readiness marker published only afterward.
- Actual installed private pythonw Studio passed metadata camera/helper/model checksum jobs,
  native textured demo/clean output/live tuning/presets, VIDEO workspace and real four-frame
  MediaPipe/GPU export. Default-player launch intercepted; no camera/real player opened.
- Installed CLI/GUI/video help passed. Uninstall exit 0 removed the full installed tree/shortcut,
  preserving both user sentinel and preset. Built MSI Welcome binds Escape to Cancel.
- Rebuilt engineering handbook: 263 pages/101 diagrams, zero diagram failures/right overflow.
  Final documented-source MSI rebuild, exact-payload smoke/provenance/source export still pending.

## 2026-11-02 - Context refresh before explicitly resumed Windows setup

- User requested a context refresh FIRST, then continuation of installer work. Pause superseded.
- Reread current installed offload/mesh instructions and reconciled current/old KardboardCode
  stores, task prerequisites and retained source. Older/sibling stores remain read-only.
- Public HEAD is 34cc9a3 after completed/pushed brown screenshots and default-player feature.
  Remaining 16 modified tracked +13 untracked files are the retained installer/version/docs draft.
- No new installer tests/builds yet at this checkpoint. Next: long-path regression, cleanup
  ownership fix, rebuild/install/installed pythonw/helpers/CLI/video/uninstall qualification,
  final handbook/docs/source export and installer provenance. Existing MSI is still stale.
- Frozen 977-page documentary remains unchanged. No live camera, system Python/PATH changes,
  security bypass, user-process termination or automatic release/tag/merge.
- Persisted/readable episode ep_878; advanced marker after store/episode persistence to
  2026-11-02T23:36:26+05:30.

## 2026-11-02 - Brown dark theme and README captures completed and pushed

- User explicitly requested finishing brown accents, refreshed README screenshots, commit/push.
- Enabled dark slider tracks/handles use #d5a568; mint semantic states and green light sliders
  are preserved. New actual pixel tests cover both track/handle and disabled states.
  35 focused theme/GUI/branding tests and Ruff passed.
- Regenerated all eight native synthetic views; seven PNGs changed, tutorial image was identical.
  Reviewed dark/light/compact/video contact sheet and updated brown/light README captions.
- Staged theme/docs/screenshots only. Overlapping installer README/version/banner and runtime
  edits remain local and unstaged. Frozen documentary PDF hash remains identical.
- gh reported READ, but the normal Git push succeeded without any account/security change.
  Remote workDesk/agentic_GUI matches 9938ac258d628759247019a757a36509001d03ec exactly.
  Do not repeat the earlier assumption that publishing/push is necessarily blocked.
- No live camera, user process termination, installer build/test, merge/tag or remote release.
- Persisted/readable handoff ep_876; advanced the exact marker only after store/episode
  persistence to 2026-11-02T23:25:25+05:30.

## 2026-11-02 - Default media-player opening added to Studio VIDEO

- User clarified the request applies to KardboardCode, not a global assistant preference.
- Worker retains its typed completed export result. On successful thread finish, Studio uses
  QDesktopServices/QUrl.fromLocalFile for that actual path on the main thread, after cleanup.
  It does not read mutable output controls or hardcode/install a player.
- Failure/cancellation opens nothing. A declined OS launch retains VIDEO SAVED and displays
  a clear error with the saved filename. Player codec support is an OS/application boundary.
- Extended real encoded synthetic export test for both launch outcomes, cleanup/thread/path
  binding and spaces/# handling; added failed/cancelled-job regressions. 46 focused tests and
  Ruff pass. No real player, live camera, paused installer tests or user process touched.
- Updated source/in-app tutorials and workstream 14. CLI remains noninteractive. The frozen
  documentary PDF is byte-identical; this feature is after its recorded cutoff. Release files
  remain explicitly stale/draft while installer work is paused.
- Persisted/readable handoff `ep_869`; marker advanced after store/episode persistence to
  `2026-11-02T23:12:03+05:30`. Feature staging excludes overlapping unfinished installer hunks.

## 2026-11-02 - Exhaustive development documentary completed

- Delivered The Box That Learned to Follow as a private local PDF under
  YTScript\DevelopmentJourney. Final 977 pages/31 chronological chapters/62 diagrams/12 figures;
  ~17,000 original narrative words followed by complete visible evidence appendices.
- Scope: 117 textual files, 6,560 records, 158 historical tasks/66 dependencies, 245 checklist
  occurrences, 199 human messages +16 delegated instructions, 203 responses, four form decisions,
  80 Git milestones. Eight documentary work orders/nine dependencies are indexed separately.
- Three print/audit rounds fixed SVG XML breaks, duplicate IDs, repeated chapter headings and
  one border-only empty page. The final PDF preserves every complete record occurrence, task
  and message; 31,252 links resolve; 51 bookmarks and stable printed folios are present.
  Zero blank pages, horizontal margin overflow, missing images or omitted source lines.
- Final cover/content/diagram/screenshot/source-appendix contact sheets inspected. PDF is
  30,570,619 bytes; SHA256 2891a853af0e7553b3156196e4286091e16b490adb2fcde15b79772f7dd972d4.
  edition-receipt.json and SHA256SUMS.txt seal the final audited files. Package remains ignored.
- User explicitly requested rereading current installed context skills before final offload.
  Read both complete current SKILL.md files; acknowledged Alfred's room-wide introduction
  only in own persona file. No sibling store, camera, installer implementation or publication.
- Completed evidence is separate from owner reading approval. Live accuracy/privacy/calling-app
  and installer/recording limitations remain as previously recorded.
- Persisted/readable final handoff as zmem `ep_868`; advanced the exact marker only after
  store/episode persistence, to `2026-11-02T22:51:42+05:30`. Source release remains the older
  completed v1.1.0 baseline while installer/source work is paused; the private book is not exported.

## 2026-11-02 - Development documentary drafted; print review in progress

- User requested a proper chronological documentary PDF with every task/detail, research,
  diagrams, repeated review and final context refresh. Installer remains paused.
- Froze 117 sanitized textual sources, 6,560 records, 158 historical task rows, 66 dependencies,
  245 checklist occurrences, 215 human/delegated requests, 203 responses, four form choices
  and 80 Git milestones. Sources include original research and both context stores.
- Built an original 31-chapter narrative, 62 diagrams and 12 captioned figures, with historical
  synthetic UI captures from specific Git revisions rather than mislabelling current UI as old.
- First complete PDF was 1,050 pages/~30.7 MB. Actual PDF text audit recovered every complete
  source-record occurrence, task and conversation entry; links resolve and horizontal bounds pass.
  Visual review found duplicate chapter headings and one blank border-only page; fixes are
  applied but final rendering, page-map, visual review and delivery remain pending.
- Local private production folder is YTScript\DevelopmentJourney; no raw camera imagery,
  credentials, publication or installer work. User explicitly requested rereading current
  installed context skills before the final offload.

## 2026-11-02 - Windows installer paused at the user's request

- User asked to pause unless almost finished. Final corrected MSI and actual installed
  application/helper verification remain, so paused instead of claiming a ready deliverable.
- Last full suite: 278 passed/Ruff; focused slice: 48 passed. Those predate the final
  extended-prefix/retry source change and its new unrun real-wheel regression.
- Genuine per-user MSI installation succeeded. All 26 component downloads worked through
  the configured verified HTTPS mirror, but Qt wheel extraction hit Windows MAX_PATH.
  A locked-wheel reinstall using a canonical extended-length private prefix succeeded.
  Added that source fix and forced exact-wheel reinstall on retry; did not rebuild after pause.
- Draft MSI is 19,697,664 bytes and stale against source. Existing ZIP remains completed
  v1.1.0, not v1.1.1. Added clear paused/draft warnings; no artifacts were published.
- Uninstalled only the owned test MSI (exit 0), removed its Start shortcut and confirmed
  user-data sentinel preservation. It left 23 empty directories; removed only the exact empty
  test installation tree after verifying zero files. No running task shell remains.
- Retained ignored build/runtime/wheelhouse/download cache, logs and the unrun camera-free
  installed-runtime probe for resumption. Do not resume setup until asked. All unfinished
  source/docs/theme changes remain uncommitted; brown sliders and native screenshots retained.
- No live camera, user Studio termination, system Python/PATH or security-setting changes.
- Persisted/readable handoff episode: `ep_856`. Advanced the full-offload marker only after
  store/episode persistence, to `2026-11-02T21:42:29+05:30`.

## 2026-11-02 - Online Windows setup requested; initial MSI built

- User requested a Windows setup in the existing release folder and selected the smaller
  online bootstrap. Adopted per-user x64 MSI with patched private Python 3.12.16, own wheel
  and first-launch Tk component wizard; no frozen runtime/system Python/PATH modifications.
- Added install-aware models/data/helper paths and packaged the six fixed helper scripts.
  The user's brown-slider refinement is included in dirty v1.1.1 inputs.
- Initial installed-path/Studio slice: 38 passed and Ruff passed. Downloaded all 26 dependency
  wheels through the configured verified HTTPS mirror and checked each against PyPI hashes.
  Direct public package-CDN TLS is blocked here; no TLS verification was disabled.
- Initial MSI is 19,689,472 bytes. Installation, installed helper/GUI checks, uninstall/data
  preservation, release documentation and final artifacts/provenance are still pending.
  Existing v1.1.0 source export is stale. No camera or remote publication was performed.

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
