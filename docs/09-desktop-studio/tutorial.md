# Studio tutorial

> **TL;DR:** Launch the GUI, explore the synthetic demo, verify models, enter a source, and
> start face-only cardboard. Tune each anatomical eye live, then enable output if needed.
> Nothing connects or records automatically.

## 1. Install and launch

From `C:\devdesk\homedesk\KardboardCode\KardboardCode-VTuber`:

```powershell
.\.venv312\Scripts\python.exe -m pip install -e ".[dev,tracking,virtual-camera,gui]"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

Or use `.\.venv312\Scripts\kardboard-studio.exe` after editable installation.
The CLI remains available unchanged. The GUI package is optional for CLI-only users.

Click **Tutorial** in the header whenever you need the nine-step in-app guide. Its **Open these
settings** button navigates to the matching page without opening a camera.

## 2. Explore without a camera

Click **Try demo**, or launch with:

```powershell
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui --demo
```

This uses the real renderer and simulated signals on a visibly labelled synthetic stage.
It does not connect to your source, run live inference, record, or publish virtual-camera output.
Demo camera/tracker FPS metrics are explicitly unavailable, not invented measurements.

The page selector in the left control room exposes **Camera**, **Avatar & eyes**, **Output &
effects**, **Tracking labs**, **Recording**, **Models**, and **Tutorial**. Scroll within a page
for its complete controls; every runtime CLI option is represented.

## 3. Verify models and enter a source

Stop the demo. In **Models**, choose the model paths. **Verify / download** checks the existing
file's expected SHA-256 or downloads the official file if missing. Use the explicit force option
to replace a corrupt/outdated file. "Present" alone does not establish a correct checksum.

In **Camera**, enter a local index such as `0`, your current phone stream, or browse a recorded
video. The source is masked by default. **Show** reveals it locally; presets and CLI copies still
exclude it. The environment button reads only this process's `KARDBOARD_CAMERA_URL`.

If you prefer setting it before launch:

```powershell
$env:KARDBOARD_CAMERA_URL = Read-Host "Paste your current camera source"
.\.venv312\Scripts\python.exe -m kardboard_vtuber.gui
```

An assignment in another terminal does not populate this process. Do not recover old credentials
or guess an address from saved history.

Choose rotation/mirroring to match the current placement. An already mirrored recording has its
own flag; do not mirror it twice. Requested capture width/height/FPS may negotiate differently.
Tracking width changes inference input, not final camera resolution.

## 4. Start and calibrate

![Built-in eye-calibration tutorial](../images/kardboardcode-studio-tutorial.png)

*The same calibration explanation is available inside the app, before opening a camera.*

Click **Start camera**. Initialization happens off the UI thread. Face-only cardboard starts
black before acquisition and freezes the last-safe composite on face loss. This is a failure
policy, not a guarantee of perfect coverage for every detected angle.

In **Avatar & eyes**, watch the raw/filtered eye meters:

1. Relax both eyes and observe the normal open values.
2. Blink or wink your **anatomical left** eye (K). Enable its **Override**, then tune its slider
   or numeric value. Repeat with the **anatomical right** eye (C).
3. Lower a closure threshold if ordinary open-eye movement closes the avatar too easily.
4. Consider relative wink settings too: the opposite eye must pass the open threshold and
   the left/right difference must be large enough. A wink can close an eye even above its
   direct blink threshold.
5. Keep each blink threshold lower than both the open and wink thresholds. Invalid combinations
   display **Not applied**; the last valid snapshot remains active.

The shared blink slider is the baseline only for eyes with Override off. **LIVE** fields update
the current session without rebuilding the renderer. Other controls unlock after Stop.
Debounce changes action logging stability, not the camera FPS.

Internal brightness helps analysis but does not brighten the final video. More tracking width
or brightness is not an established fix for distant-face acquisition.

## 5. Avatar and optional effects

Textured 3D is the canonical renderer. Physics animates its flap hinges. Disable physics before
choosing procedural 2D for comparison. Perspective depth offset has direct numeric entry, with
a minimum of -1 and no extra GUI positive cap.

Green screen replaces the background while preserving the camera-visible body. Hand foreground
restores conservative anatomical regions over the box; RGB landmarks do not prove physical depth
and cannot restore arbitrary held objects. Inferred-depth foreground restoration was removed.

**Preview**, **Skeleton**, and **CLI equivalent** are separate right-side tabs. Skeleton diagnostics
do not fill a body avatar into the camera image. Preview resizing is display-only.

## 6. Use as a camera

Install OBS Studio's Windows camera component once and enable **Send clean video to OBS Virtual
Camera** in **Output & effects**. Choose positive even output dimensions and an advertised FPS
from 1 to 60. Stop/restart to change output topology.

Select **OBS Virtual Camera** in your calling app. OBS itself may stay closed, but do not start a
second producer, including OBS's own camera output. No custom KardboardCode-named driver is installed.

Export uses the clean full-size composite before local debug panels/raw preview. It aspect-fits
with black bars. Advertised FPS is not guaranteed motion throughput. Select microphone audio
separately. Actual calling-app permissions and compatibility still require local confirmation.

The GUI's **Suppress preview** maps to CLI headless behavior: the studio/logs remain usable and
rendering/output continue when required, but the preview images are not transferred.

## 7. Advanced tracking and raw debug

**Tracking labs** deliberately labels shoulder and hood modes experimental. They remain available
because the requested UI includes every feature, not because they replaced the face-only default.
Shoulder fallback needs calibration; hood mode uses green on your left and blue on your right.
The two fallback modes cannot be combined. Missing face/side markers does not confirm a rear view.

Local tracking debug is synthetic geometry. **Raw face preview** and running without cardboard
can display your actual face; the studio asks for acknowledgement on each real start. Screen
capture can still expose that local window. Presets never retain raw-preview consent.

## 8. Record privately and replay

Stop camera/demo, open **Recording**, and choose the existing guided face/full-body routine or a
free recording. The free duration applies only to free mode; guided stages have their own timing.
Set countdown, pose width/rate, raw-preview height, destination folder and filename stem.

Source/transforms/brightness/face width and model paths are reused from the other pages.
Confirm **Start PRIVATE recording** only when ready: it saves **unmasked MP4 + CSV**, not the
safe avatar output, and opens the recorder's own raw preview.

The header Stop requests a cooperative finish so the writer and telemetry can close. Native
camera blocking can delay it; do not force-close the process just to make the button seem faster.
The existing fixed-FPS writer may compress playback time if actual delivery is slower. This
limitation remains unresolved.

Keep raw recordings private. Browse a recording later as a camera source for offline testing.

## 9. Presets, logs, stopping and troubleshooting

Save/load remembers validated setup controls, not your source or raw consent. Loading does not
start anything. The CLI-equivalent tab substitutes a same-terminal environment setup, not real
credentials. The log clipboard is redacted too; native libraries may separately write stderr.

| Symptom | First checks |
|---|---|
| Empty/invalid source | Enter it here or set the variable before launching this process |
| Missing model | Select a valid file in Models; verify/download explicitly |
| No face / frozen image | Visibility, lighting, framing, processing width; do not disable privacy loss handling |
| Virtual camera unavailable | Installed component, competing sender, calling-app permissions |
| Rejected eye edit | Each blink threshold must be lower than open/wink; inspect the Not applied banner |
| Source/settings disabled | Stop first; only LIVE controls remain editable during a session |
| Slow shutdown | Native camera initialization/read/release may still be pending; the UI is cooperative |

Stop remains in the header across all pages. Closing during work requests shutdown, keeps the
event loop alive, and closes after the worker finishes. It does not forcibly kill a Qt thread.
