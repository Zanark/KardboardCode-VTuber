# KardboardCode Studio

[![KardboardCode Studio: your camera, your cardboard. Native Python VTuber, v1.0.0 source edition.](docs/images/readme/hero.png)](docs/guides/getting-started.md)

*Official KC artwork, wrapped in pixel lettering and kraft-paper graphics.*

**A real 3D cardboard head for your real camera.**

[Get started](docs/guides/getting-started.md) ·
[Features & controls](docs/guides/features-and-controls.md) ·
[Camera setup](docs/guides/camera-and-virtual-output.md) ·
[Engineering book](docs/README.md) ·
[Release files](release/README.md)

![Actual KardboardCode Studio with live eye sliders and a synthetic avatar preview](docs/images/kardboardcode-studio-dark.png)

*The real Windows Studio, running a labelled synthetic demo. No camera or video output.*

## Current milestone

**v1.0.0 — first official source release.** [What's included →](release/RELEASE_NOTES.md)

![Three features: textured 3D and spring flaps, independent K/C eye controls, clean OBS Virtual Camera output](docs/images/readme/feature-cards.png)

*Real geometry, live anatomical eyes, and clean output through the installed OBS camera component.*

## Inside the Studio

![01: The control room. Real widgets, live sliders, your setup.](docs/images/readme/studio.png)

<table>
<tr>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-studio-light.png"><img src="docs/images/kardboardcode-studio-light.png" alt="Studio in its light theme" width="100%"></a>
<sub>Same controls. A lighter workbench.</sub>
</td>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-studio-native-camera.png"><img src="docs/images/kardboardcode-studio-native-camera.png" alt="Native laptop and USB camera selection with illustrative device names" width="100%"></a>
<sub>Your laptop camera, without memorizing device numbers. Illustrative names.</sub>
</td>
</tr>
<tr>
<td align="center">
<a href="docs/images/kardboardcode-studio-compact.png"><img src="docs/images/kardboardcode-studio-compact.png" alt="Compact Studio layout with anatomical eye calibration" width="100%"></a>
<sub>A smaller desk. The same live eye controls.</sub>
</td>
<td align="center">
<a href="docs/images/kardboardcode-studio-tutorial.png"><img src="docs/images/kardboardcode-studio-tutorial.png" alt="Built-in tutorial explaining left and right eye calibration" width="100%"></a>
<sub>A built-in walkthrough, before you connect a camera.</sub>
</td>
</tr>
</table>

[Open the Studio tutorial →](docs/09-desktop-studio/tutorial.md)

## Cardboard in motion

![02: Built to move. Real 3D, little pixels, big expressions.](docs/images/readme/motion.png)

![Animated cardboard avatar with head rotation, eye expressions and flap physics](docs/images/kardboardcode-live-demo.gif)

*Recorded motion telemetry, rendered on a synthetic stage. No camera pixels in this GIF.*

<table>
<tr>
<td width="50%" align="center">
<img src="docs/images/kardboardcode-real-life-demo.gif" alt="User-approved masked cardboard-camera example with the original background" width="100%">
<sub>User-approved masked camera example.</sub>
</td>
<td width="50%" align="center">
<img src="docs/images/kardboardcode-green-screen-demo.gif" alt="The same approved cardboard-camera performance over chroma green" width="100%">
<sub>The same performance, with person-segmentation green screen.</sub>
</td>
</tr>
</table>

![Open eyes, left wink, right wink and blink states of the K/C lettering](docs/images/kardboardcode-expression-states.png)

*K follows your left eye. C follows your right.*

<table>
<tr>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-flap-physics.png"><img src="docs/images/kardboardcode-flap-physics.png" alt="Left turn, neutral and right turn with spring-driven cardboard flaps" width="100%"></a>
<sub>Head turns tug at the spring-driven flaps.</sub>
</td>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-flap-motion-sequence.png"><img src="docs/images/kardboardcode-flap-motion-sequence.png" alt="Five rendered frames showing independent side-flap motion" width="100%"></a>
<sub>Five moments. Independent little hinges.</sub>
</td>
</tr>
</table>

## Every side has a story

![03: Every side has a story. Corrugation, shipping labels and headphones.](docs/images/readme/details.png)

![Face-free hero render of the textured cardboard character and chunky headphones](docs/images/kardboardcode-hero.png)

*The actual runtime character, rendered without camera imagery.*

<table>
<tr>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-six-sides.png"><img src="docs/images/kardboardcode-six-sides.png" alt="Front, rear, left, right, top and underside of the character" width="100%"></a>
<sub>A proper six-sided box, including its hollow underside.</sub>
</td>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-angle-gallery.png"><img src="docs/images/kardboardcode-angle-gallery.png" alt="Nine synthetic angles including profiles, rear quarters and roll" width="100%"></a>
<sub>Nine angles. No cardboard-flat shortcuts.</sub>
</td>
</tr>
<tr>
<td align="center">
<a href="docs/images/kardboardcode-cinematic-poses.png"><img src="docs/images/kardboardcode-cinematic-poses.png" alt="Curious, hero, side-eye, upward and leaning poses" width="100%"></a>
<sub>Small geometry. Plenty of attitude.</sub>
</td>
<td align="center">
<a href="docs/images/kardboardcode-performance-states.png"><img src="docs/images/kardboardcode-performance-states.png" alt="Expression and head-pose combinations rendered from the model" width="100%"></a>
<sub>Blinks, winks and turns in combination.</sub>
</td>
</tr>
<tr>
<td align="center">
<a href="docs/images/kardboardcode-surface-tour.png"><img src="docs/images/kardboardcode-surface-tour.png" alt="Shipping labels, worn surfaces, neck opening and headphone details" width="100%"></a>
<sub>Tape, labels, corrugation, and a little wear.</sub>
</td>
<td align="center">
<a href="docs/images/kardboardcode-detail-views.png"><img src="docs/images/kardboardcode-detail-views.png" alt="Close views of aged paper labels, top stamp and underside" width="100%"></a>
<sub>Shipping marks and deliberately scruffy details.</sub>
</td>
</tr>
</table>

[Explore the avatar's visual design →](docs/02-architecture/textured-3d-renderer.md)

## Under the cardboard

![04: Under the cardboard. Synthetic debug views, real geometry.](docs/images/readme/debug.png)

<table>
<tr>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-tracking-debug-window.png"><img src="docs/images/kardboardcode-tracking-debug-window.png" alt="Synthetic tracking debug view with face mesh and XYZ inset" width="100%"></a>
<sub>Synthetic face mesh and XYZ diagnostics. No camera pixels.</sub>
</td>
<td width="50%" align="center">
<a href="docs/images/kardboardcode-render-mesh-debug.png"><img src="docs/images/kardboardcode-render-mesh-debug.png" alt="Actual mesh wireframe, five hinge groups and internal privacy volume" width="100%"></a>
<sub>Real vertices, hinge groups and the internal privacy volume.</sub>
</td>
</tr>
</table>

<p align="center">
<a href="docs/images/kardboardcode-body-skeleton-debug-window.png"><img src="docs/images/kardboardcode-body-skeleton-debug-window.png" alt="Synthetic 33-point body skeleton diagnostic" width="270"></a>
</p>

*A separate line-skeleton diagnostic—not a full-body avatar.*

## Unbox your setup

![05: Unbox your setup. Quick start, camera output and the engineering book.](docs/images/readme/start.png)

**Already installed?**

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

*Source release, not an installer. Face-only loss freezes the last-safe frame; real calling-app
qualification remains unconfirmed. [Privacy and known limits →](docs/guides/camera-and-virtual-output.md#troubleshooting-and-known-limits)*

![Handle with character. Built in Python, wrapped in cardboard.](docs/images/readme/footer.png)

*Official supplied logo. Original banner compositions with licensed Silkscreen and Barlow
Condensed typography. [Artwork and font credits →](docs/branding/README.md)*
