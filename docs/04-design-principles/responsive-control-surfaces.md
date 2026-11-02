# Responsive control surfaces and progressive disclosure

> **TL;DR:** Separate interaction ownership from expensive work, and expose advanced features
> without allowing them to obscure the selected safe operating mode.

## Separation of responsibilities

The studio owns controls, validation presentation, tutorial and painting. The existing runtime
owns inference/composition/output. One optional bridge is a narrower maintenance boundary than
a second implementation of every privacy branch in Qt.

Qt widget access stays on the main thread. A session worker creates and closes the ModernGL
context on its own thread. The UI never waits synchronously for shutdown; it shows Stopping
until the owned worker actually finishes. Responsiveness is not a license to report false success.

## Progressive disclosure is not feature removal

The page selector groups tasks: input, eyes/avatar, output/effects, experiments, recording,
model setup and tutorial. Every CLI option remains reachable and a test checks that inventory.
The default mode stays face-only; exposing hood/body controls does not mean they are validated
replacements. Raw debugging has an explicit local privacy acknowledgement.

The Stop button stays in the same header position across pages because finding it should not
depend on remembering which settings panel is open. Per-eye values sit alongside a large
preview and persistent raw/filtered meters because calibration is an observe-adjust-compare task.

Numeric boxes accompany sliders for precise/repeatable calibration and keyboard access. Anatomical
LEFT/K and RIGHT/C labels resolve mirror ambiguity. A visible LIVE label distinguishes edits that
apply now from resource settings that require Stop. Invalid tuples keep the last valid snapshot;
the interface reports the rejected edit instead of silently clamping unrelated controls.

## Explicit consent and reversible state

Opening, loading a preset or reading help does not start capture. Presets do not persist a
source credential or raw-face consent. A synthetic demo teaches operation without a camera,
but its labels and unavailable real FPS values prevent it from masquerading as live evidence.

Theme is UI-only; it does not recolor output. The original KC-box icon identifies the application
without requiring a network icon service or a large asset dependency.

See [interface decisions](../09-desktop-studio/interface-specification.md) for individual
control-placement rationale and [runtime architecture](../09-desktop-studio/runtime-architecture.md)
for the implementation boundaries.
