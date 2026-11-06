# KardboardCode visual gallery

[Back to the animated front page](../README.md) ·
[Getting started](guides/getting-started.md) ·
[Studio tutorial](09-desktop-studio/tutorial.md) ·
[Avatar design](02-architecture/textured-3d-renderer.md)

The full visual tour lives here so the front page can focus on the animations and two theme
showcases. Native Studio captures use synthetic imagery; camera names and video paths are
illustrative. No raw camera footage or private face imagery is included.

For the complete interface rather than selected examples, use the
[single-file GUI visual reference](KardboardCode-Studio-GUI-Visual-Reference.html):
204 embedded native screenshots covering 102 named views/scroll parts in both themes.
Download/open the HTML in a browser; it needs no server, internet or external image folder.

## Inside the Studio

![The control room: real widgets and live sliders](images/readme/studio.svg)

### Current Studio in motion

![Dark native Studio walkthrough with animated synthetic preview, eye and output controls, and Logs](images/kardboardcode-studio-walkthrough-dark.gif)

*Fresh dark-theme capture of the actual synthetic demo. The inspector changes pages and the
optional Logs drawer opens without hiding the preview. No camera or desktop was captured.*

![Light native Studio walkthrough showing the same protected preview and progressively disclosed controls](images/kardboardcode-studio-walkthrough-light.gif)

*The same current workflow on warm paper. Diagnostics use explicitly synthetic example data.
These are real widget captures, not interface mockups or live-camera qualification.*

### Camera selection

![Native laptop and USB camera selection with illustrative device names](images/kardboardcode-studio-native-camera.png)

*Named capture routes without memorizing device numbers. The illustrated list does not open a camera.*

### Compact widescreen workspace

![Compact 16:9 Studio with a protected preview, stacked diagnostics and anatomical eye controls](images/kardboardcode-studio-compact.png)

*The preview, selected diagnostics and compact metric cards stay visible on a smaller desk; settings remain in labelled sections.*

### Built-in tutorial

![Native tutorial explaining left and right eye calibration](images/kardboardcode-studio-tutorial.png)

*A walkthrough before camera access, including numeric OPEN/CLOSED calibration.*

### Prerecorded video

![Video file inspector with lossless MKV and optional high-quality MP4](images/kardboardcode-studio-video.png)

*Process every frame at the original dimensions, with compatible audio. The displayed paths are examples.*

### Clean output for OBS

![Separate clean output window without Studio controls or diagnostics](images/kardboardcode-studio-clean-output.png)

*A controls-free synthetic output window for OBS Window Capture, distinct from OBS Virtual Camera.
The persistent Show clean output button reopens it after closing; Auto-open is a separate preference.*

The [dark and light theme showcases](../README.md#studio-dark-and-light) remain on the front page.
See the [complete operating guide](guides/features-and-controls.md) for all settings.

## Expressions and moving cardboard

![Built to move: real 3D and expressive pixels](images/readme/motion.svg)

### Recorded-motion avatar showcase

![Animated cardboard avatar with tracked head turns, eye expressions and flap physics](images/kardboardcode-live-demo.gif)

*The former front-page animation remains here unchanged: recorded numeric motion telemetry
rendered on a synthetic stage. No camera pixels are stored in this GIF.*

### Anatomical eye expressions

![Open eyes, left wink, right wink and blink states of the K/C lettering](images/kardboardcode-expression-states.png)

*K follows anatomical left; C follows anatomical right. These are rendered expression examples.*

### Spring-driven flaps

![Left turn, neutral and right turn with spring-driven cardboard flaps](images/kardboardcode-flap-physics.png)

*Head turns tug at the cardboard's independent spring-driven hinges.*

![Five rendered moments showing independent side-flap motion](images/kardboardcode-flap-motion-sequence.png)

*Five synthetic frames reveal the little hinges in motion. Watch the animations on the front page.*

## Every side has a story

![Corrugation, shipping labels and headphones](images/readme/details.svg)

### Six-sided geometry

![Front, rear, left, right, top and underside of the cardboard character](images/kardboardcode-six-sides.png)

*A proper six-sided box, including the hollow neck-safe underside.*

![Nine synthetic views including profiles, rear quarters and roll](images/kardboardcode-angle-gallery.png)

*Real depth from nine angles, not a flat replacement image.*

### Character and performance

![Curious, hero, side-eye, upward and leaning poses](images/kardboardcode-cinematic-poses.png)

*Synthetic poses show the character's geometry, silhouette and expression.*

![Rendered expression and head-pose combinations](images/kardboardcode-performance-states.png)

*Blinks, winks and turns in combination.*

### Material details

![Shipping labels, worn surfaces, neck opening and headphone details](images/kardboardcode-surface-tour.png)

*Tape, corrugation, asymmetric labels and deliberately worn material.*

![Close views of paper labels, top stamp and underside](images/kardboardcode-detail-views.png)

*Shipping marks, scruffy edges and the interior structure.*

Read the [renderer chapter](02-architecture/textured-3d-renderer.md) for geometry, materials and hinges.

## Under the cardboard

![Synthetic diagnostics and real geometry](images/readme/debug.svg)

### Readable Studio diagnostics

![Raw face above face-pose or body diagnostics beside the program preview](images/kardboardcode-studio-diagnostics.png)

*The right-hand rail keeps raw and tracking image areas readable together without opening Tools.
Its dividers resize the panels; disabled channels return space to the main preview. The raw
pattern is synthetic, explicitly not a face, and never enters clean output.*

*The preferred metric cards stay beside Tools. Its open Logs drawer sits below the viewer,
not under the full-height settings column.*

### Face mesh and pose

![Synthetic tracking diagnostic with face mesh and XYZ inset](images/kardboardcode-tracking-debug-window.png)

*Synthetic face-mesh and XYZ diagnostics; no camera pixels.*

### Renderer construction

![Actual mesh wireframe, hinge groups and internal privacy volume](images/kardboardcode-render-mesh-debug.png)

*Real vertices, five hinge groups and the interior privacy volume.*

### Body diagnostic

![Synthetic 33-point body skeleton diagnostic](images/kardboardcode-body-skeleton-debug-window.png)

*A separate line-skeleton inspection view, not a full-body avatar composited into camera video.*

## Setup and artwork

![Quick start, camera output and engineering documentation](images/readme/start.svg)

[Install & first launch](guides/getting-started.md) ·
[Camera and output](guides/camera-and-virtual-output.md) ·
[Engineering book](README.md) ·
[Original PNGTuber assets](../assets/PNGTuberV1/README.md)

The supplied KC voxel-box logo remains unchanged. The banner compositions use licensed
Silkscreen and Barlow Condensed typography; decorative lettering is transparent SVG.
See [artwork and font credits](branding/README.md).

![Handle with character: built in Python, wrapped in cardboard](images/readme/footer.svg)

*Original pixel/industrial artwork. [Return to the animations →](../README.md)*
