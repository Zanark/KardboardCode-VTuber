# KardboardCode Studio

[![KardboardCode Studio: your camera, your cardboard. Native Python VTuber, v1.1.1.](docs/images/readme/hero.png)](docs/guides/getting-started.md)

![The actual textured 3D avatar, presented in the forest-green and kraft-paper banner palette](docs/images/kardboardcode-hero.png)

*Official KC identity above; the real runtime character directly below. No camera imagery.*

**A real 3D cardboard head for your real camera.**

[Get started](docs/guides/getting-started.md) ·
[Windows setup](release/KardboardCode-Studio-windows-x64.msi) ·
[Features & controls](docs/guides/features-and-controls.md) ·
[Camera setup](docs/guides/camera-and-virtual-output.md) ·
[Engineering book](docs/README.md) ·
[Release files](release/README.md)

![Actual KardboardCode Studio with live eye sliders and a synthetic avatar preview](docs/images/kardboardcode-studio-dark.png)

*Cardboard-brown sliders on forest green. Real Windows widgets on a labelled synthetic stage;
no camera input or published video.*

## Current milestone

**v1.1.1 — Windows setup, cardboard sliders and automatic video playback.** [What's included →](release/RELEASE_NOTES.md)

## Inside the Studio

![01: The control room. Real widgets, live sliders, your setup.](docs/images/readme/studio.svg)

<a href="docs/images/kardboardcode-studio-light.png"><img src="docs/images/kardboardcode-studio-light.png" alt="Studio in its light theme" width="100%"></a>

*Same controls, warm paper and contrasting green sliders. A lighter workbench.*

<a href="docs/images/kardboardcode-studio-native-camera.png"><img src="docs/images/kardboardcode-studio-native-camera.png" alt="Native laptop and USB camera selection with illustrative device names" width="100%"></a>

*Your laptop camera, without memorizing device numbers. Illustrative names.*

<a href="docs/images/kardboardcode-studio-compact.png"><img src="docs/images/kardboardcode-studio-compact.png" alt="Compact Studio layout with anatomical eye calibration" width="100%"></a>

*A smaller desk. The same cardboard-brown live eye controls.*

<a href="docs/images/kardboardcode-studio-tutorial.png"><img src="docs/images/kardboardcode-studio-tutorial.png" alt="Built-in tutorial explaining left and right eye calibration" width="100%"></a>

*A built-in walkthrough, before you connect a camera.*

<a href="docs/images/kardboardcode-studio-video.png"><img src="docs/images/kardboardcode-studio-video.png" alt="Video processing workspace with original-size lossless MKV and optional high-quality MP4" width="100%"></a>

*Process an existing video. Original size, every frame, compatible audio.*

<a href="docs/images/kardboardcode-studio-clean-output.png"><img src="docs/images/kardboardcode-studio-clean-output.png" alt="Separate clean output window for OBS Window Capture, without controls or diagnostics" width="100%"></a>

*A separate clean window for OBS. No debug panels in the feed.*

[Open the Studio tutorial →](docs/09-desktop-studio/tutorial.md)

## Cardboard in motion

![02: Built to move. Real 3D, little pixels, big expressions.](docs/images/readme/motion.svg)

<img src="docs/images/kardboardcode-live-demo.gif" alt="Animated cardboard avatar with head rotation, eye expressions and flap physics" width="100%">

*Recorded motion telemetry, rendered on a synthetic stage. No camera pixels in this GIF.*

<p align="center">
<img src="docs/images/kardboardcode-real-life-demo.gif" alt="User-approved masked cardboard-camera example with the original background" width="49%">
<img src="docs/images/kardboardcode-green-screen-demo.gif" alt="The same approved cardboard-camera performance over chroma green" width="49%">
</p>

*Left: user-approved masked camera example. Right: the same performance with person-segmentation green screen.*

![Open eyes, left wink, right wink and blink states of the K/C lettering](docs/images/kardboardcode-expression-states.png)

*K follows your left eye. C follows your right.*

<a href="docs/images/kardboardcode-flap-physics.png"><img src="docs/images/kardboardcode-flap-physics.png" alt="Left turn, neutral and right turn with spring-driven cardboard flaps" width="100%"></a>

*Head turns tug at the spring-driven flaps.*

<a href="docs/images/kardboardcode-flap-motion-sequence.png"><img src="docs/images/kardboardcode-flap-motion-sequence.png" alt="Five rendered frames showing independent side-flap motion" width="100%"></a>

*Five moments. Independent little hinges.*

## Every side has a story

![03: Every side has a story. Corrugation, shipping labels and headphones.](docs/images/readme/details.svg)

<a href="docs/images/kardboardcode-six-sides.png"><img src="docs/images/kardboardcode-six-sides.png" alt="Front, rear, left, right, top and underside of the character" width="100%"></a>

*A proper six-sided box, including its hollow underside.*

<a href="docs/images/kardboardcode-angle-gallery.png"><img src="docs/images/kardboardcode-angle-gallery.png" alt="Nine synthetic angles including profiles, rear quarters and roll" width="100%"></a>

*Nine angles. No cardboard-flat shortcuts.*

<a href="docs/images/kardboardcode-cinematic-poses.png"><img src="docs/images/kardboardcode-cinematic-poses.png" alt="Curious, hero, side-eye, upward and leaning poses" width="100%"></a>

*Small geometry. Plenty of attitude.*

<a href="docs/images/kardboardcode-performance-states.png"><img src="docs/images/kardboardcode-performance-states.png" alt="Expression and head-pose combinations rendered from the model" width="100%"></a>

*Blinks, winks and turns in combination.*

<a href="docs/images/kardboardcode-surface-tour.png"><img src="docs/images/kardboardcode-surface-tour.png" alt="Shipping labels, worn surfaces, neck opening and headphone details" width="100%"></a>

*Tape, labels, corrugation, and a little wear.*

<a href="docs/images/kardboardcode-detail-views.png"><img src="docs/images/kardboardcode-detail-views.png" alt="Close views of aged paper labels, top stamp and underside" width="100%"></a>

*Shipping marks and deliberately scruffy details.*

[Explore the avatar's visual design →](docs/02-architecture/textured-3d-renderer.md)

## Under the cardboard

![04: Under the cardboard. Synthetic debug views, real geometry.](docs/images/readme/debug.svg)

![Dedicated local diagnostic side panels leaving the central program image unobstructed](docs/images/kardboardcode-studio-diagnostics.png)

*Synthetic diagnostic layout. Private raw-face pixels stay in their own panel, not the output.*

<a href="docs/images/kardboardcode-tracking-debug-window.png"><img src="docs/images/kardboardcode-tracking-debug-window.png" alt="Synthetic tracking debug view with face mesh and XYZ inset" width="100%"></a>

*Synthetic face mesh and XYZ diagnostics. No camera pixels.*

<a href="docs/images/kardboardcode-render-mesh-debug.png"><img src="docs/images/kardboardcode-render-mesh-debug.png" alt="Actual mesh wireframe, five hinge groups and internal privacy volume" width="100%"></a>

*Real vertices, hinge groups and the internal privacy volume.*

<a href="docs/images/kardboardcode-body-skeleton-debug-window.png"><img src="docs/images/kardboardcode-body-skeleton-debug-window.png" alt="Synthetic 33-point body skeleton diagnostic" width="100%"></a>

*A separate line-skeleton diagnostic—not a full-body avatar.*

## Unbox your setup

![05: Unbox your setup. Quick start, camera output and the engineering book.](docs/images/readme/start.svg)

**Windows:** [Download setup](release/KardboardCode-Studio-windows-x64.msi), install, then open
**KardboardCode Studio** from Start. First launch offers verified component downloads; no Python setup.

**Source checkout:**

```powershell
.\.venv312\Scripts\kardboard-studio.exe
```

[Install & first launch](docs/guides/getting-started.md) ·
[All controls & CLI flags](docs/guides/features-and-controls.md) ·
[Phone / laptop / calling apps](docs/guides/camera-and-virtual-output.md) ·
[Troubleshooting](docs/guides/camera-and-virtual-output.md#troubleshooting-and-known-limits)

[Engineering book](docs/README.md) ·
[PDF handbook](docs/KardboardCode-VTuber-Engineering-Handbook.pdf) ·
[Original PNGTuber assets](assets/PNGTuberV1/README.md) ·
[Release package & notes](release/README.md)

*Online, unsigned Windows x64 setup; source ZIP also available. Face-only loss freezes the last-safe frame; real calling-app
qualification remains unconfirmed. [Privacy and known limits →](docs/guides/camera-and-virtual-output.md#troubleshooting-and-known-limits)*

![Handle with character. Built in Python, wrapped in cardboard.](docs/images/readme/footer.svg)

*Official supplied logo. Original banner compositions with licensed Silkscreen and Barlow
Condensed typography. [Artwork and font credits →](docs/branding/README.md)*
