"""Debounced facial action detection from normalized tracking controls."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from kardboard_vtuber.tracking.models import FaceTrackingState


class FaceAction(StrEnum):
    FACE_DETECTED = "face_detected"
    FACE_LOST = "face_lost"
    EYES_OPEN = "eyes_open"
    EYES_CLOSED = "eyes_closed"
    BLINK = "blink"
    LEFT_WINK = "left_wink"
    RIGHT_WINK = "right_wink"
    MOUTH_OPEN = "mouth_open"
    MOUTH_CLOSED = "mouth_closed"


@dataclass(frozen=True, slots=True)
class ActionThresholds:
    eye_closed: float = 0.35
    eye_open: float = 0.65
    mouth_open: float = 0.25
    mouth_closed: float = 0.12
    hold_ms: int = 100
    maximum_blink_ms: int = 500

    def __post_init__(self) -> None:
        if not 0.0 <= self.eye_closed < self.eye_open <= 1.0:
            raise ValueError("eye thresholds must satisfy 0 <= closed < open <= 1")
        if not 0.0 <= self.mouth_closed < self.mouth_open <= 1.0:
            raise ValueError("mouth thresholds must satisfy 0 <= closed < open <= 1")
        if self.hold_ms < 0:
            raise ValueError("hold_ms cannot be negative")
        if self.maximum_blink_ms < 0:
            raise ValueError("maximum_blink_ms cannot be negative")


@dataclass(frozen=True, slots=True)
class FaceActionEvent:
    action: FaceAction
    timestamp_ms: int
    left_eye_open: float
    right_eye_open: float
    mouth_open: float
    duration_ms: int | None = None

    def format_log(self) -> str:
        fields = [
            "[ACTION]",
            f"timestamp_ms={self.timestamp_ms}",
            f"action={self.action.value}",
            f"left_eye={self.left_eye_open:.2f}",
            f"right_eye={self.right_eye_open:.2f}",
            f"mouth={self.mouth_open:.2f}",
        ]
        if self.duration_ms is not None:
            fields.append(f"duration_ms={self.duration_ms}")
        return " ".join(fields)


@dataclass(slots=True)
class _ChannelState:
    stable: FaceAction | None = None
    candidate: FaceAction | None = None
    candidate_since_ms: int = 0


class FaceActionDetector:
    """Converts continuous controls into low-noise transition events."""

    def __init__(self, thresholds: ActionThresholds | None = None) -> None:
        self._thresholds = thresholds or ActionThresholds()
        self._face = _ChannelState()
        self._eyes = _ChannelState()
        self._mouth = _ChannelState()
        self._last_timestamp_ms = -1
        self._eyes_closed_since_ms: int | None = None

    def update(self, state: FaceTrackingState) -> tuple[FaceActionEvent, ...]:
        if state.timestamp_ms <= self._last_timestamp_ms:
            return ()
        self._last_timestamp_ms = state.timestamp_ms
        events: list[FaceActionEvent] = []

        face_action = FaceAction.FACE_DETECTED if state.detected else FaceAction.FACE_LOST
        face_transition = self._transition(self._face, face_action, state.timestamp_ms)
        if face_transition is not None:
            events.append(self._event(face_transition, state))

        if not state.detected:
            if face_transition is FaceAction.FACE_LOST:
                self._eyes = _ChannelState()
                self._mouth = _ChannelState()
                self._eyes_closed_since_ms = None
            return tuple(events)

        eyes_action = self._classify_eyes(state)
        if eyes_action is not None:
            previous_eyes = self._eyes.stable
            eyes_transition = self._transition(self._eyes, eyes_action, state.timestamp_ms)
            if eyes_transition is not None:
                if eyes_transition is FaceAction.EYES_CLOSED:
                    self._eyes_closed_since_ms = state.timestamp_ms
                elif (
                    eyes_transition is FaceAction.EYES_OPEN
                    and previous_eyes is FaceAction.EYES_CLOSED
                    and self._eyes_closed_since_ms is not None
                ):
                    duration_ms = state.timestamp_ms - self._eyes_closed_since_ms
                    if duration_ms <= self._thresholds.maximum_blink_ms:
                        events.append(self._event(FaceAction.BLINK, state, duration_ms))
                    self._eyes_closed_since_ms = None
                events.append(self._event(eyes_transition, state))

        mouth_action = self._classify_mouth(state)
        if mouth_action is not None:
            mouth_transition = self._transition(self._mouth, mouth_action, state.timestamp_ms)
            if mouth_transition is not None:
                events.append(self._event(mouth_transition, state))

        return tuple(events)

    def _classify_eyes(self, state: FaceTrackingState) -> FaceAction | None:
        left_closed = state.left_eye_open <= self._thresholds.eye_closed
        right_closed = state.right_eye_open <= self._thresholds.eye_closed
        left_open = state.left_eye_open >= self._thresholds.eye_open
        right_open = state.right_eye_open >= self._thresholds.eye_open
        if left_closed and right_closed:
            return FaceAction.EYES_CLOSED
        if left_closed and right_open:
            return FaceAction.LEFT_WINK
        if right_closed and left_open:
            return FaceAction.RIGHT_WINK
        if left_open and right_open:
            return FaceAction.EYES_OPEN
        return None

    def _classify_mouth(self, state: FaceTrackingState) -> FaceAction | None:
        if state.mouth_open >= self._thresholds.mouth_open:
            return FaceAction.MOUTH_OPEN
        if state.mouth_open <= self._thresholds.mouth_closed:
            return FaceAction.MOUTH_CLOSED
        return None

    def _transition(
        self,
        channel: _ChannelState,
        action: FaceAction,
        timestamp_ms: int,
    ) -> FaceAction | None:
        if channel.stable is action:
            channel.candidate = None
            return None
        if channel.candidate is not action:
            channel.candidate = action
            channel.candidate_since_ms = timestamp_ms
        if timestamp_ms - channel.candidate_since_ms < self._thresholds.hold_ms:
            return None
        channel.stable = action
        channel.candidate = None
        return action

    @staticmethod
    def _event(
        action: FaceAction,
        state: FaceTrackingState,
        duration_ms: int | None = None,
    ) -> FaceActionEvent:
        return FaceActionEvent(
            action=action,
            timestamp_ms=state.timestamp_ms,
            left_eye_open=state.left_eye_open,
            right_eye_open=state.right_eye_open,
            mouth_open=state.mouth_open,
            duration_ms=duration_ms,
        )
