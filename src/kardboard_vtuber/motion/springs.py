"""Fixed-step damped spring integration for secondary avatar motion."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpringParameters:
    """Physical tuning for a unit-mass damped harmonic oscillator."""

    frequency_hz: float = 4.0
    damping_ratio: float = 0.7
    maximum_step_seconds: float = 1.0 / 120.0

    def __post_init__(self) -> None:
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")
        if self.damping_ratio < 0:
            raise ValueError("damping_ratio cannot be negative")
        if self.maximum_step_seconds <= 0:
            raise ValueError("maximum_step_seconds must be positive")


class DampedSpring:
    """Semi-implicit Euler spring with bounded internal integration steps."""

    def __init__(
        self,
        value: float = 0.0,
        parameters: SpringParameters | None = None,
    ) -> None:
        if not math.isfinite(value):
            raise ValueError("initial spring value must be finite")
        self._parameters = parameters or SpringParameters()
        self._value = value
        self._velocity = 0.0

    @property
    def value(self) -> float:
        return self._value

    @property
    def velocity(self) -> float:
        return self._velocity

    def step(self, target: float, delta_seconds: float) -> float:
        if not math.isfinite(target) or not math.isfinite(delta_seconds):
            raise ValueError("spring inputs must be finite")
        if delta_seconds < 0:
            raise ValueError("delta_seconds cannot be negative")
        if delta_seconds == 0:
            return self._value

        steps = max(
            1,
            math.ceil(delta_seconds / self._parameters.maximum_step_seconds),
        )
        step_seconds = delta_seconds / steps
        angular_frequency = 2.0 * math.pi * self._parameters.frequency_hz
        stiffness = angular_frequency * angular_frequency
        damping = 2.0 * self._parameters.damping_ratio * angular_frequency
        for _ in range(steps):
            acceleration = stiffness * (target - self._value) - damping * self._velocity
            self._velocity += acceleration * step_seconds
            self._value += self._velocity * step_seconds
        return self._value

    def reset(self, value: float, velocity: float = 0.0) -> None:
        if not math.isfinite(value) or not math.isfinite(velocity):
            raise ValueError("spring reset values must be finite")
        self._value = value
        self._velocity = velocity

    def is_settled(
        self,
        target: float,
        *,
        position_tolerance: float = 1e-3,
        velocity_tolerance: float = 1e-3,
    ) -> bool:
        if position_tolerance < 0 or velocity_tolerance < 0:
            raise ValueError("spring tolerances cannot be negative")
        return (
            abs(target - self._value) <= position_tolerance
            and abs(self._velocity) <= velocity_tolerance
        )
