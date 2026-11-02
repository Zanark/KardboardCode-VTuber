"""The in-app tutorial; no camera is needed to read or navigate it."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

LESSONS = (
    (
        "Welcome: a control surface, not a second pipeline",
        "Camera",
        "The studio uses the existing tracking and cardboard pipeline. Opening it does not start "
        "a camera, record, or publish video.<br><br><b>Try demo</b> renders the real avatar on an "
        "explicitly synthetic stage. It needs no camera and does not send virtual-camera video. "
        "Use it to explore the layout and live eye sliders.<br><br>"
        "<b>LIVE</b> controls apply to the next processed frame. "
        "Other settings are available after Stop.",
    ),
    (
        "1. Models and source",
        "Models",
        "Open Models. <b>Verify / download</b> runs the official-model downloader and checksum "
        "verification. An existing file is only 'present' until verified.<br><br>"
        "In Camera, choose <b>This computer's camera</b>, press <b>Refresh</b>, "
        "select the laptop/USB camera by name, then Start camera. Listing reads Windows "
        "metadata only; it does not open streams. The same device may appear under two APIs. "
        "Refresh after device changes.<br><br>"
        "Choose <b>Phone stream / video file / manual source</b> "
        "for a URL, recording or index (0). "
        "Use the environment-source button only if KARDBOARD_CAMERA_URL is set in this process. "
        "The masked source is kept in memory, not saved in presets or copied logs.",
    ),
    (
        "2. Framing and a safe start",
        "Camera",
        "Choose backend, rotation, mirroring and optional resolution/FPS. These are capture "
        "requests, not guaranteed negotiated settings. Already mirrored recordings use their own "
        "checkbox; avoid flipping twice.<br><br>Click <b>Start camera</b>. With cardboard enabled, "
        "startup is black before face acquisition; face loss freezes the last safe composite. "
        "This behavior does not prove perfect face coverage at every detected angle.<br><br>"
        "Brightness boosts tracking input only. Frame age is internal, "
        "not phone-to-screen latency.",
    ),
    (
        "3. Calibrate your LEFT / K and RIGHT / C eyes",
        "Avatar & eyes",
        "Your anatomical LEFT eye controls K; RIGHT controls C, regardless of mirroring. "
        "Watch the live raw/filtered meters, blink each eye, then enable each independent Override "
        "and move its slider. Numeric boxes allow precise values.<br><br>"
        "An eye at or below its blink threshold closes. A relative wink can also close it when the "
        "opposite eye exceeds the open threshold and their difference is large enough. "
        "<b>Lower thresholds are less sensitive.</b> Both per-eye blink values must remain lower "
        "than the open and wink thresholds.<br><br>"
        "Invalid combinations are not applied. The last valid configuration stays active. "
        "Eye debounce controls how long a state must hold before logging, not preview frame rate.",
    ),
    (
        "4. Avatar, physics and diagnostics",
        "Avatar & eyes",
        "Textured 3D is the canonical model. Procedural 2D is the fallback/comparison renderer; "
        "disable flap physics before selecting it. Depth offset changes perspective placement. "
        "Motion smoothing reduces jitter; turning it off requires a restart.<br><br>"
        "Local tracking diagnostics are in Tracking labs. Raw-face debugging requires confirmation "
        "on every real start; presets never restore it. Unmasked camera mode also requires "
        "explicit acknowledgement. The GUI cannot make unsafe modes safe by changing their labels.",
    ),
    (
        "5. Calling apps and output effects",
        "Output & effects",
        "Install OBS Studio's camera component and the project's virtual-camera extra. Enable the "
        "output, choose even dimensions and advertised FPS, then select <b>OBS Virtual Camera</b> "
        "in Discord, Teams or Meet. OBS can remain closed. Only one producer may use it.<br><br>"
        "Output is video-only, aspect-fitted with black bars. Preview resize and local debugging "
        "do not affect exported pixels. Actual motion speed follows capture/processing.<br><br>"
        "Green screen replaces the background. Hand foreground is an RGB anatomical approximation; "
        "it does not track arbitrary held objects or prove physical depth.",
    ),
    (
        "6. Experimental tracking",
        "Tracking labs",
        "Face-only is the selected default. Skeleton diagnostics open in their own tab, not as a "
        "filled avatar on the output. Shoulder fallback requires calibration. Hood tracking uses "
        "green on your left and blue on your right. Red/pink markers are unsupported.<br><br>"
        "Body fallback and hood-marker mode cannot run together. Body-only/no-face/no-side-marker "
        "rear estimation is a heuristic, not confirmation. These experiments were unreliable "
        "in prior live use; do not treat availability numbers as accuracy or privacy evidence.",
    ),
    (
        "7. Private recording and replay",
        "Recording",
        "Stop the camera/demo first. Select guided or free recording, body telemetry, duration, "
        "countdown, model/input widths, folder and filename. Confirm the raw warning.<br><br>"
        "The existing recorder opens a raw preview and writes MP4 + CSV. This is NOT a masked "
        "recording. The header Stop button requests a cooperative end so the writer can flush. "
        "Camera-driver blocking can delay shutdown; the UI remains available.<br><br>"
        "Guided routines set their own stage durations; the duration control applies to free mode. "
        "The existing fixed-FPS writer can compress elapsed playback when capture FPS drops. "
        "Keep raw footage private. Browse it later as a camera source for offline testing.",
    ),
    (
        "8. Presets, logs and troubleshooting",
        "Camera",
        "Save/load stores validated controls, not your source URL or raw-preview consent. Loading "
        "does not start capture. The CLI-equivalent tab substitutes a local environment variable "
        "so copying a command does not copy credentials.<br><br>"
        "The bottom console remains selectable and bounded; Copy includes redacted text only. "
        "Missing model? Open Models. No image? Check source, backend and face visibility. "
        "Virtual output unavailable? Check installation and competing producer. "
        "Distant detection remains a known limitation, not a solved slider setting.<br><br>"
        "Stop stays in the header across every page. Closing during work requests shutdown instead "
        "of killing the rendering thread. User visual approval and real calling-app qualification "
        "are separate from automated/synthetic evidence.",
    ),
)


class TutorialDialog(QDialog):
    navigate = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("KardboardCode Studio - Tutorial")
        self.resize(700, 530)
        layout = QVBoxLayout(self)
        self.selector = QComboBox()
        self.selector.addItems([lesson[0] for lesson in LESSONS])
        layout.addWidget(QLabel("CAMERA-FREE WALKTHROUGH"))
        layout.addWidget(self.selector)
        self.text = QTextBrowser()
        layout.addWidget(self.text, 1)
        row = QHBoxLayout()
        self.back = QPushButton("Back")
        self.next = QPushButton("Next")
        jump = QPushButton("Open these settings")
        close = QPushButton("Done")
        for button in (self.back, self.next, jump, close):
            row.addWidget(button)
        layout.addLayout(row)
        self.selector.currentIndexChanged.connect(self._show_lesson)
        self.back.clicked.connect(
            lambda: self.selector.setCurrentIndex(
                max(0, self.selector.currentIndex() - 1),
            )
        )
        self.next.clicked.connect(
            lambda: self.selector.setCurrentIndex(
                min(len(LESSONS) - 1, self.selector.currentIndex() + 1),
            )
        )
        jump.clicked.connect(lambda: self.navigate.emit(LESSONS[self.selector.currentIndex()][1]))
        close.clicked.connect(self.close)
        self._show_lesson(0)

    def _show_lesson(self, index: int) -> None:
        title, _, body = LESSONS[index]
        self.text.setHtml(f"<h2>{title}</h2><p>{body}</p>")
        self.back.setEnabled(index > 0)
        self.next.setEnabled(index < len(LESSONS) - 1)
