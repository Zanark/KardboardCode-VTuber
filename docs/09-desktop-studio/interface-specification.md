# Interface specification and placement rationale

> The first release exposes **all existing features**, including experimental flags and private
> recording, as requested. Face-only cardboard remains the default; visibility is not endorsement.

## Spatial model

The top header contains identity, theme, tutorial, and the stable Start/Stop actions. The left
settings notebook contains task-oriented pages. The right workspace contains preview/skeleton
views, live telemetry, and a redacted CLI equivalent. A bounded bottom console preserves the
CLI's inspectable logs.

Why these positions:

- **Start/Stop stay in the header:** changing settings pages must not hide the emergency stop.
  Stop is visually distinct from Start, never a destructive "kill thread" action.
- **Source is first:** most startup failures are source/model/output setup, not eye calibration.
- **Avatar/eyes sit next to the preview:** compare a left/right slider edit with the K/C result,
  using anatomical names rather than ambiguous mirrored screen-side labels.
- **Output is separate from input:** capture requests and virtual-camera dimensions are different
  contracts; changing one must not look like changing the other.
- **Experimental tracking gets its own page and warnings:** all features remain accessible without
  presenting hood/body estimates as the normal or privacy-certified path.
- **Recording gets its own task:** the recorder saves raw pixels, not the safe rendered preview.
  Explicit consent and a distinct action prevent accidental capture.
- **Model setup is discoverable:** missing files need actionable setup, not a cryptic traceback.
- **Tutorial is a persistent header action and a full page:** it is available before camera access,
  not a first-run modal that blocks the interface or disappears forever.
- **Logs remain selectable plain text:** no HTML interpretation, bounded history, explicit clearing
  and safe copying. Rich styling is reserved for status, not log formatting.

## Complete runtime control inventory

| Page | CLI fields / feature | Interaction |
|---|---|---|
| Camera | `source` | Computer-camera chooser with names/Refresh, or masked URL/file/manual-index entry |
| Camera | `backend`, `width`, `height`, `fps` | Choice and numeric requests; automatic values clearly labelled |
| Camera | `rotate`, `mirror`, `input_already_mirrored` | Rotation choice and separate checkboxes |
| Camera | `brightness` | Live internal-only slider with numeric value |
| Camera | `duration`, `preview_height`, `headless` | Optional duration, display-only height, preview suppression |
| Avatar / eyes | `render_cardboard`, `track_face`, `cardboard_renderer`, `physics` | Independent features and renderer selection |
| Avatar / eyes | `box_depth_offset` | Numeric perspective depth offset; no artificial positive cap |
| Avatar / eyes | `blink_threshold`, independent left/right overrides | Shared baseline plus live per-eye sliders/numeric editing |
| Avatar / eyes | `wink_threshold`, `eye_open_threshold`, `wink_min_difference` | Live calibrated controls with validation |
| Avatar / eyes | `action_hold_ms`, `eye_action_hold_ms` | Live debounce values |
| Avatar / eyes | `no_motion_filter` | Explicit smoothing toggle, restart-only |
| Output | `virtual_camera`, `virtual_camera_width`, `virtual_camera_height`, `virtual_camera_fps` | Enable and fixed-format numeric controls |
| Output | `green_screen`, `segmentation_width`, `segmentation_model` | Feature toggle, input width, model file |
| Output | `hand_occlusion`, `hand_tracking_width`, `hand_model` | Anatomical foreground toggle, width, model file |
| Tracking labs | `full_body`, `pose_tracking_width`, `pose_model` | Separate skeleton diagnostics and pose configuration |
| Tracking labs | `body_head_fallback`, `hood_marker_tracking` | Explicit experimental toggles; reject their invalid combination |
| Tracking labs | `tracking_debug`, `debug_face_preview` | Local diagnostics and explicit raw-face consent |
| Models | `face_model`, optional model paths | Browse fields, existence indicators and checksum-verifying download actions |

The new independent-eye CLI overrides preserve the original shared `--blink-threshold` default.
They do not change anatomical K-left/C-right mapping.

## Recorder control inventory

Source/backend/rotation/mirror/brightness and face/pose model selections are reused from the
current setup. The recording page exposes `full_body`, `free_recording`, `duration`, `tracking_width`,
`pose_tracking_width`, `pose_tracking_fps`, `output_dir`, `name`, `countdown`, and `preview_height`.
These map to `scripts\record_guided_regression.py`, not to an invented output format.

Recording is mutually exclusive with the GUI's live/demo pipeline. Its raw preview remains the
existing recorder window; the native studio remains available for logs and lifecycle control.
The interface does not silently record the safe preview instead of the documented raw regression data.

## State and validation

- Opening: no source connection, no output, no raw consent. Synthetic demo is explicit.
- Starting: disable duplicate starts, show initialization, retain Stop.
- Running: enable live tuning; restart-only settings are disabled until stopped.
- Stopping: request cooperative shutdown; keep the window event loop running.
- Stopped/error: clear live video to an explicit idle/error state, release owned resources, enable setup.
- Invalid tuning: show the exact invariant; retain the last applied valid snapshot.
- Raw debug or unmasked-camera mode: acknowledgement before a real camera run, never stored in presets.
- Imported preset: source excluded; raw-preview consent always resets off.

## Tutorial requirements

The in-app guide must explain first launch/model setup, source input, transformations, safe preview,
anatomical eye calibration, live/restart badges, virtual-camera selection/single-producer constraints,
green screen/hands, experimental tracking, recording privacy, source-free presets, logs, and Stop.
The same narrative must be readable in [the book tutorial](tutorial.md).

## Visual identity

Dark graphite/mint studio styling echoes the creator setup without recoloring source video. The
light theme has the same layout and controls. The theme button includes both a sun and a moon icon.
The window/application icon is original vector artwork: a cardboard box with **KC on its top face**.
Actual screenshots must be generated from the running widgets, not a design mockup.
