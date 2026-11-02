# Desktop GUI research and design

> Research date: 2026-11-02. Scope: a native, responsive, all-feature Python studio that retains
> the existing CLI and its privacy/output semantics. The user explicitly requested a tutorial.
> Confidence labels describe the evidence, not an assertion that the delivered GUI is fast.

## Iteration 1 - Structural survey

**HIGH, source-confirmed:** `cli.build_parser` owns the operational flags
(`src\kardboard_vtuber\cli.py:35-285` at research time). `cli.main` constructs tracking,
renderer and output resources, then performs a continuous capture/composition loop
(`cli.py:288-630`). The GUI must not run this loop on the widget thread.

**HIGH:** There are already two expression consumers: `FaceActionDetector._classify_eyes`
(`tracking\events.py`) and each renderer's eye logic (`renderer\ps1_cardboard.py`,
`renderer\textured_3d.py`). A slider connected only to the detector would change logs while
leaving the visible K/C expression unchanged. This is the most important calibration trap.

**HIGH:** Model downloads and guided/free regression recording are separate scripts
(`scripts\download_*_model.py`, `scripts\record_guided_regression.py:113-203`).
An all-feature GUI must expose these too, rather than equating "all" with camera preview.

**Next lens:** trace pixel, control, and telemetry ownership through the loop.

## Iteration 2 - Data flow and state

**HIGH:** The source camera and the adjusted tracking image are deliberately separate.
`cli.main` makes the brightness-adjusted processing frame before tracker submission but
starts composition from the original packet copy (`cli.py:431-465,500-548` at research time).
The GUI's brightness slider must retain this distinction.

**HIGH:** Virtual-camera output precedes local diagnostics and raw-face preview
(`cli.py:547-599`). `VirtualCameraOutput.send/repeat` owns the repeated output buffer
(`virtual_camera.py:68-104`). A GUI cannot forward a widget screenshot to virtual output.

**HIGH:** `LatestFrameCamera.read` waits on a condition and returns the newest packet;
`stop` joins the capture thread with a timeout (`camera\stream.py:99-143`).
Closing a window cannot synchronously wait for this on the event thread.

**Decision / engineering inference:** use one immutable live-settings snapshot and one latest
preview mailbox, plus a bounded log ring. The UI polls this mailbox at approximately 30 Hz.
This intentionally drops superseded previews; the sender still receives its own full-size
clean frames. Boundedness is established structurally; achieved responsiveness needs measurement.

**Next lens:** compare toolkit integration and dependency costs.

## Iteration 3 - Toolkit and external contracts

| Candidate | Verified capabilities | Project-specific tradeoff |
|---|---|---|
| PySide6 / Qt Widgets | Native widgets, layouts, accessibility/keyboard controls, timers, threads, image buffers, dialogs | Extra binary dependency; thread affinity must be respected; distribution licensing needs review |
| Tk/ttk | Standard Python GUI interface, themed controls, native dialogs, event-loop model | Viable smaller UI; richer split layouts, calibration controls, image display and styling require more project-owned work |
| Dear PyGui | GPU-driven UI and explicit render loop | Strong tool/debug UI; introduces a second graphics/render-loop abstraction beside ModernGL; not evidence of faster end-to-end video |

Primary sources, read on the research date:

1. [Qt QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html):
   a `QThread` object lives in its creator thread; `run()` executes separately. Queued
   slots on a subclass are not automatically worker-thread commands. Forced termination is discouraged.
2. [Qt QTimer](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html):
   timers belong to their event-loop thread; deadlines can slip under load. A nominal 33 ms
   timer does not guarantee 30 displayed frames per second.
3. [Qt QImage](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html):
   direct pixel access and image ownership differ from screen-oriented QPixmap.
4. [Qt QPlainTextEdit](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QPlainTextEdit.html):
   simplified layout and `maximumBlockCount` suit a bounded plain-text log.
5. [Python Tkinter](https://docs.python.org/3/library/tkinter.html):
   Tcl/Tk event queues and threading rules still require work outside the event callback.
6. [Dear PyGui render loop](https://dearpygui.readthedocs.io/en/latest/documentation/render-loop.html):
   expensive work in the render loop reduces UI frame rate.
7. [Qt for Python licensing](https://doc.qt.io/qtforpython-6/commercial/index.html):
   community and commercial distributions have different licensing terms. Adding the
   community dependency is not a legal determination about a future packaged distribution.

**Decision:** optional `PySide6-Essentials` (QtCore/QtGui/QtWidgets and image/icon loading),
not a browser server and not a mandatory CLI dependency. Widgets provide the
sliders, numeric editing, splitter, logs, dialogs and tutorial without an HTML bridge or
per-frame JavaScript encoding. This is a fit decision, not an unmeasured speed ranking.

**Next lens:** failure containment, interaction risks, and maintainability.

## Iteration 4 - Patterns, risks, and anti-patterns

**Avoid a second pipeline:** reuse `cli.main` through optional runtime hooks. Keep ordinary
CLI behavior when hooks are absent. Do not copy segmentation, hand restoration, freeze,
fallback resolution or clean-export ordering into a separate Qt compositor.

**Avoid one queued signal per frame:** even a responsive producer can accumulate stale events
in a slow UI. Publish only the latest resized preview. Copy the QImage before the NumPy owner
can be replaced. Bound worker logs and displayed text independently.

**Avoid implicit capture:** opening the GUI, loading a preset or opening a tutorial must not
start a camera. The demo must use synthetic imagery and say so visibly.

**Avoid hidden live/restart mismatch:** independent eye thresholds and internal brightness
are live. Resource topology, source, resolution, models, mirroring, output format and tracking
modes are restart settings. Keep live widgets enabled during work; lock or clearly mark
restart-only settings instead of silently deferring them.

**Avoid unsafe persistence:** source URLs and raw-preview consent are session-only. Save only
an allowlisted settings schema. Imported presets are data, not commands; do not evaluate
arbitrary Python or spawn an imported command. Commands/logs redact URLs before display/export.

**Keep known limitations visible:** body/hood modes are experimental; no-face/no-marker does
not prove rear orientation. Raw debug/recordings are privacy-breaking local operations.
The existing fixed-FPS recorder's elapsed-time limitation is not resolved by adding a button.

**Remaining qualification:** native camera-driver stop latency, high-DPI appearance on other
monitors, actual calling apps, and difficult distant-face lighting need owner-environment evidence.

## Iteration 5 - Synthesis

Think of the studio as a control surface beside the existing machine, not a replacement machine.
Qt owns interaction and display. The worker owns capture orchestration, inference consumers,
the OpenGL context, composition, and camera delivery.

What that mental model hides: MediaPipe and OpenCV already have their own asynchronous/native
work; a Python thread is not process-level crash isolation. A stuck native driver cannot be
made safely cancellable by `QThread.terminate`. During shutdown the window must remain responsive
and honestly show "Stopping" rather than destroy the thread or claim resources are released.

Key findings:

1. **HIGH:** tuning must reach both actions and rendering, not only logs
   (`FaceActionDetector`, `PS1CardboardRenderer`, `Textured3DCardboardRenderer`).
2. **HIGH:** export-before-debug is a required privacy boundary (`cli.main`,
   `VirtualCameraOutput`), independent of the UI layout.
3. **HIGH:** all-feature coverage includes the recorder/model scripts, not just parser flags.
4. **Design decision:** progressive disclosure by task keeps the default face-only workflow
   obvious without removing advanced flags requested by the user.
5. **Design decision:** a fixed-location Stop button, explicit raw consent, named anatomical
   eyes and nearby live meters reduce operational ambiguity.
6. **Unknown until measured:** actual UI heartbeat under inference, platform-specific widget
   sizing, and native-runtime cleanup. Tests/screenshots must record evidence, not aspirations.

## Knowledge map after research

- **Explored:** parser, main loop, per-eye consumers, frame ownership, native toolkit contracts,
  recorder interface, capture stop, export ordering, documentation structure.
- **Partially explored:** native-driver cancellation and distribution packaging; no universal
  camera cancellation or installer behavior is claimed.
- **Unexplored / deliberately deferred:** alternate inference engines, new body-tracking fixes,
  a separately named Windows camera driver, and changes to recording timing.
- **Implementation direction:** one bounded runtime bridge, shared eye tuning, native widget
  controls, optional GUI extra, source-free presets, explicit private recording, and a synthetic
  demo/tutorial that works without a camera.
