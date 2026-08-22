"""Library-neutral face-tracking contracts and MediaPipe adapter."""

from kardboard_vtuber.tracking.events import (
    ActionThresholds,
    FaceAction,
    FaceActionDetector,
    FaceActionEvent,
)
from kardboard_vtuber.tracking.filters import (
    FaceMotionFilter,
    FaceMotionFilterConfig,
    OneEuroFilter,
    OneEuroParameters,
)
from kardboard_vtuber.tracking.models import (
    FaceTrackingState,
    HeadPose,
    NormalizedLandmark,
    TrackingSnapshot,
)

__all__ = [
    "ActionThresholds",
    "FaceTrackingState",
    "FaceAction",
    "FaceActionDetector",
    "FaceActionEvent",
    "FaceMotionFilter",
    "FaceMotionFilterConfig",
    "HeadPose",
    "NormalizedLandmark",
    "OneEuroFilter",
    "OneEuroParameters",
    "TrackingSnapshot",
]
