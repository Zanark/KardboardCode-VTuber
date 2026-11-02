"""Shared anatomical eye calibration for action detection and rendering."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace

from kardboard_vtuber.tracking.models import FaceTrackingState


@dataclass(frozen=True, slots=True)
class EyeSensitivity:
    left_closed: float = 0.35
    right_closed: float = 0.35
    opened: float = 0.65
    wink: float = 0.70
    difference: float = 0.15

    def __post_init__(self) -> None:
        values = (self.left_closed, self.right_closed, self.opened, self.wink, self.difference)
        if not all(math.isfinite(value) and 0 <= value <= 1 for value in values):
            raise ValueError("eye thresholds must be finite and between 0 and 1")
        for side, closed in (("left", self.left_closed), ("right", self.right_closed)):
            if closed >= self.opened:
                raise ValueError(f"{side} blink threshold must be lower than eye-open threshold")
            if closed >= self.wink:
                raise ValueError(f"{side} blink threshold must be lower than wink threshold")

    def winked(self, openness: float, other_openness: float) -> bool:
        return (
            openness <= self.wink
            and other_openness >= self.opened
            and other_openness - openness >= self.difference
        )

    def closed(self, openness: float, other_openness: float, *, left_eye: bool) -> bool:
        threshold = self.left_closed if left_eye else self.right_closed
        return openness <= threshold or self.winked(openness, other_openness)


def render_eye_state(
    filtered: FaceTrackingState, raw: FaceTrackingState,
) -> FaceTrackingState:
    """Keep pose smoothing without low-pass filtering away brief eye closures."""
    if not filtered.detected or not raw.detected:
        return filtered
    return replace(
        filtered, left_eye_open=raw.left_eye_open, right_eye_open=raw.right_eye_open,
    )


def calibrate_eyes(
    opened: Sequence[tuple[float, float]], closed: Sequence[tuple[float, float]],
) -> EyeSensitivity:
    if len(opened) < 12 or len(closed) < 12:
        raise ValueError(
            "Collect at least 12 distinct face observations for each calibration step.",
        )
    if not all(math.isfinite(v) and 0 <= v <= 1 for row in (*opened, *closed) for v in row):
        raise ValueError("Calibration observations must be finite eye scores between 0 and 1.")
    thresholds = []
    gaps = []
    open_levels = []
    for side, name in ((0, "left"), (1, "right")):
        high = sorted(row[side] for row in opened)[len(opened) // 5]
        low = sorted(row[side] for row in closed)[len(closed) * 4 // 5]
        gap = high - low
        if gap < 0.10:
            raise ValueError(
                f"The {name} eye samples overlap. Face the camera, improve lighting, "
                "and repeat with relaxed open eyes and BOTH eyes fully closed.",
            )
        thresholds.append(low + gap * 0.45)
        gaps.append(gap)
        open_levels.append(high)
    maximum = max(thresholds)
    opposite_open = max(maximum + 0.025, min(open_levels) - min(gaps) * 0.12)
    if opposite_open >= 1 or opposite_open >= min(open_levels):
        raise ValueError(
            "Eye score ranges overlap too much for safe calibration. Repeat the steps.",
        )
    return EyeSensitivity(
        left_closed=thresholds[0], right_closed=thresholds[1],
        opened=opposite_open, wink=max(maximum + 0.02, opposite_open - 0.02),
        difference=min(0.20, max(0.05, min(gaps) * 0.35)),
    )
