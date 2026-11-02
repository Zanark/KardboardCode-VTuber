"""Shared anatomical eye calibration for action detection and rendering."""

from __future__ import annotations

import math
from dataclasses import dataclass


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
