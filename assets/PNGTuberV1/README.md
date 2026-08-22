# KardboardCode PNGTuber V1

This directory is the preserved first-generation KardboardCode avatar package used by PNGTuber Plus. It includes the original editable layer PNGs, the original `KCAvatar.save`, reference renders, and a machine-readable behavior manifest.

## Character appearance

KardboardCode is a seated character with:

- A large cardboard box as the head.
- Hand-drawn `KC` lettering on the front of the box.
- Black over-ear headphones on the character's right side.
- A dark hoodie with light drawstrings.
- White hands using a dark laptop.
- Cardboard flaps around the bottom of the head.

The character faces slightly toward screen-left while the headphones and right side of the box remain visible. The laptop occupies the lower-left foreground.

## Directory contents

| File | Role |
|---|---|
| `KCAvatar.save` | Original PNGTuber Plus model. JSON containing layer configuration and embedded base64 copies of every sprite. |
| `Full Body.png` | Permanent base illustration: box head, headphones, body, arms, hands, laptop, and cardboard base. |
| `Eyes Open.png` | Open-eye artwork: the `KC` lettering used as the normal eye state. |
| `Eyes Closed.png` | Closed curved eyes used during blinking. |
| `FrontFlap1-2.png` | Screen-left front flap in the idle/not-talking state. |
| `FrontFlap2-2.png` | Screen-right front flap in the idle/not-talking state. |
| `FrontFlap1.png` | Screen-left front flap in the talking state. |
| `FrontFlap2.png` | Screen-right front flap in the talking state. |
| `RightFlap1.png` | Small side flap with independent motion/physics. |
| `model-manifest.json` | Machine-readable summary of the layer hierarchy, state rules, and original PNGTuber Plus parameters. |
| `reference/*.png` | Reconstructed reference states generated from the source layers. These are documentation outputs, not additional runtime layers. |

## Canvas and alignment

- Every runtime layer is a `1920 x 1080` RGBA PNG.
- Artwork is positioned on a shared full-canvas coordinate system.
- Transparent padding is intentional and allows the PNG files to align by compositing each layer at `(0, 0)`.
- Do not trim, individually resize, or reposition a source PNG unless all alignment data is updated together.
- `Full Body.png` is the visual base. Other files contain only the pixels that change or move independently.

## Layer stack

The original PNGTuber Plus model uses this visual depth:

1. `Full Body.png` at z-index `-1`.
2. Front-flap and side-flap layers at z-index `0`.
3. Eye layer at z-index `1`.

All seven optional/moving layers are children of the full-body layer. Their original parent ID is `3452965169`.

## State machine

The microphone controls the front-flap pair, while automatic blinking controls the eye pair. These systems are independent, producing four valid visual states.

| State | Visible eye layer | Visible front-flap layers | Always visible |
|---|---|---|---|
| Idle, eyes open | `Eyes Open.png` | `FrontFlap1-2.png`, `FrontFlap2-2.png` | `Full Body.png`, `RightFlap1.png` |
| Talking, eyes open | `Eyes Open.png` | `FrontFlap1.png`, `FrontFlap2.png` | `Full Body.png`, `RightFlap1.png` |
| Idle, blinking | `Eyes Closed.png` | `FrontFlap1-2.png`, `FrontFlap2-2.png` | `Full Body.png`, `RightFlap1.png` |
| Talking, blinking | `Eyes Closed.png` | `FrontFlap1.png`, `FrontFlap2.png` | `Full Body.png`, `RightFlap1.png` |

In the save format:

- `showTalk: 0` means always available.
- `showTalk: 1` identifies the talking flap variant.
- `showTalk: 2` identifies the idle flap variant.
- `showBlink: 0` means unaffected by blinking.
- `showBlink: 1` identifies the normal/open-eye variant.
- `showBlink: 2` identifies the blink/closed-eye variant.

## Motion and physics

### Full body

- Acts as the root parent for all other layers.
- Original drag value: `18`.
- Original stretch amount: `1`.
- No configured sinusoidal x/y motion.

### Talking flaps

- `FrontFlap1.png` uses stretch `3.25`, y amplitude `4`, and y frequency `0.037`.
- `FrontFlap2.png` uses stretch `3.25`, y amplitude `2`, and y frequency `0.037`.
- The unequal amplitudes keep the two sides from moving as one rigid mirrored piece.

### Idle flaps

- `FrontFlap1-2.png` and `FrontFlap2-2.png` are static alternates.
- They replace the talking flap artwork when the voice threshold is inactive.

### Right-side flap

- `RightFlap1.png` remains visible in every state.
- Rotation is constrained to approximately `-4` through `+3` degrees.
- Rotation drag is `2`.
- Stretch amount is `3.75`.
- Y amplitude is `3`; y frequency is `0.038`.
- This creates subtle secondary motion independent of speaking and blinking.

### Eyes

- The open and closed eye layers are static alternates.
- They sit above the cardboard flap layers at z-index `1`.
- The `KC` lettering is therefore part of the eye-expression system, not baked into the full-body layer.

## Original PNGTuber Plus hierarchy

| Layer | ID | Parent ID | Position | Offset | Talk | Blink | Z |
|---|---:|---:|---|---|---:|---:|---:|
| Full Body | `3452965169` | none | `(15, 226)` | `(-15, -226)` | 0 | 0 | -1 |
| Eyes Open | `2668782109` | `3452965169` | `(-114, -294)` | `(27, -10)` | 0 | 1 | 1 |
| FrontFlap1-2 | `3839644171` | `3452965169` | `(-208, -59)` | `(193, -167)` | 2 | 0 | 0 |
| FrontFlap2-2 | `1956358513` | `3452965169` | `(82, -34)` | `(-97, -192)` | 2 | 0 | 0 |
| FrontFlap1 | `573431133` | `3452965169` | `(-201, -60)` | `(186, -166)` | 1 | 0 | 0 |
| FrontFlap2 | `3444366280` | `3452965169` | `(77, -42)` | `(-95, -189)` | 1 | 0 | 0 |
| RightFlap1 | `162753989` | `3452965169` | `(262, -87)` | `(-277, -139)` | 0 | 0 | 0 |
| Eyes Closed | `3531045988` | `3452965169` | `(-97, -278)` | `(45, -28)` | 0 | 2 | 1 |

Positions and offsets above are PNGTuber Plus/Godot model values, not replacements for the shared-canvas alignment in the PNG files.

## Loading the original model

1. Keep `KCAvatar.save` and the external PNG files together.
2. Open/import `KCAvatar.save` in PNGTuber Plus.
3. If PNGTuber Plus asks for missing images, point it to this directory.
4. The save references historical paths under `user://KC Sprites/`, but it also embeds each image in `imageData`.
5. Select the intended microphone and tune the application's talking threshold for the current environment.

The external PNG files do not have byte-identical hashes to the embedded PNG data. Preserve both the save and external files rather than replacing embedded data automatically.

## OBS integration from the original setup

The inspected OBS collections captured:

`PNGTuberPlus:Engine:PNGTUBER PLUS 1.4.5 WINDOWS.exe`

The capture was a Windows window-capture source named `PNGTuber+`. An enabled OBS chroma-key filter removed the PNGTuber Plus background. Different scenes reused the same source with different crops, scales, and positions.

The original stream composition used a mint-green theme. Because the model was chroma-keyed, avoid clothing or avatar colors too close to the selected key color when modifying the artwork.

## Reference renders

`reference/state-sheet.png` shows all four state combinations. The individual files preserve transparency:

- `reference/idle-open.png`
- `reference/talking-open.png`
- `reference/idle-blink.png`
- `reference/talking-blink.png`

The reference renders were reconstructed by compositing the shared-canvas layers. They demonstrate expected appearance but do not encode PNGTuber Plus timing, thresholds, or live physics.

## Guidance for another model or developer

When changing or porting this avatar:

1. Treat the source PNGs and `KCAvatar.save` as the canonical V1 input.
2. Preserve the seated laptop silhouette and cardboard-box identity unless redesign is explicitly requested.
3. Keep blinking and speaking independent.
4. Do not display both members of an eye pair or both idle/talking variants of the same flap simultaneously.
5. Preserve asymmetric flap motion; it is intentional.
6. Do not bake the `KC` eye lettering into the body if expression switching must remain possible.
7. Validate every change in all four state combinations.
8. For OBS, test the chroma key around cardboard edges, headphones, hoodie, hands, and laptop.
9. Distinguish source artwork from generated previews.
10. Never assume these PNGTuber layers are sufficient for a production Live2D rig.

## Live2D / VTube Studio porting notes

This package is useful reference material, but it is not yet a complete Live2D model. A proper port should separate and redraw occluded regions for deformation. Likely additional parts include:

- Front, side, and top planes of the cardboard head.
- Headphones, ear cup, headband, highlights, and shadows.
- Separate `K` and `C` eye/expression artwork plus closed-eye lines.
- Each cardboard flap with artwork extending behind its current visible boundary.
- Hoodie torso, hood, sleeves, drawstrings, hands, laptop screen/back/base, and cardboard seat.
- Shadow and highlight layers that can deform without exposing transparent gaps.

Live2D Cubism Editor is required to create meshes, deformers, parameters, physics, and the final `.moc3` export used by VTube Studio.

## Provenance

Copied without modification from:

`C:\devdesk\KardboardCode\OBS-Setup-Profiles\KardboardCode\KC Assets\KC_PNGTuberPlus`

Repository destination:

`C:\devdesk\KardboardCode\KardboardCode-VTuber\assets\PNGTuberV1`
