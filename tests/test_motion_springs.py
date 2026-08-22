from __future__ import annotations

import pytest

from kardboard_vtuber.motion import DampedSpring, SpringParameters


def simulate(
    spring: DampedSpring,
    *,
    target: float,
    seconds: float,
    fps: int,
) -> list[float]:
    return [spring.step(target, 1 / fps) for _ in range(round(seconds * fps))]


def test_critically_damped_spring_converges_without_overshoot() -> None:
    spring = DampedSpring(
        parameters=SpringParameters(frequency_hz=3.0, damping_ratio=1.0)
    )

    values = simulate(spring, target=1.0, seconds=1.0, fps=60)

    assert all(0.0 <= value <= 1.0 for value in values)
    assert values[-1] == pytest.approx(1.0, abs=1e-5)


def test_underdamped_spring_produces_secondary_overshoot() -> None:
    spring = DampedSpring(
        parameters=SpringParameters(frequency_hz=3.0, damping_ratio=0.35)
    )

    values = simulate(spring, target=1.0, seconds=1.0, fps=60)

    assert max(values) > 1.05
    assert values[-1] == pytest.approx(1.0, abs=0.01)


def test_bounded_substeps_reduce_frame_rate_dependence() -> None:
    parameters = SpringParameters(frequency_hz=4.0, damping_ratio=0.7)
    at_30_fps = simulate(
        DampedSpring(parameters=parameters),
        target=1.0,
        seconds=0.5,
        fps=30,
    )[-1]
    at_120_fps = simulate(
        DampedSpring(parameters=parameters),
        target=1.0,
        seconds=0.5,
        fps=120,
    )[-1]

    assert at_30_fps == pytest.approx(at_120_fps, abs=0.02)


def test_spring_reset_and_settled_state() -> None:
    spring = DampedSpring()
    spring.reset(2.0)

    assert spring.value == 2.0
    assert spring.velocity == 0.0
    assert spring.is_settled(2.0)


def test_spring_rejects_negative_delta_time() -> None:
    spring = DampedSpring()

    with pytest.raises(ValueError, match="cannot be negative"):
        spring.step(1.0, -0.1)
