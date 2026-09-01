"""Library-neutral face-tracking contracts and MediaPipe adapter."""

from kardboard_vtuber.tracking.body_head_fallback import (
    BodyHeadFallback,
    BodyHeadFallbackConfig,
)
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
from kardboard_vtuber.tracking.full_body import (
    FullBodyPoseState,
    FullBodyTrackerConfig,
    MediaPipeFullBodyTracker,
    PoseLandmark,
)
from kardboard_vtuber.tracking.green_screen import (
    GreenScreenConfig,
    MediaPipePersonSegmenter,
    PersonSegmentationState,
    apply_green_screen,
)
from kardboard_vtuber.tracking.hood_markers import (
    HoodMarkerColor,
    HoodMarkerHeadTracker,
    HoodMarkerObservation,
    HoodMarkerSnapshot,
    HoodMarkerTrackerConfig,
    HoodTrackingSource,
)
from kardboard_vtuber.tracking.models import (
    FaceTrackingState,
    HeadPose,
    NormalizedLandmark,
    TrackingSnapshot,
)

__all__ = [
    "ActionThresholds",
    "BodyHeadFallback",
    "BodyHeadFallbackConfig",
    "FaceTrackingState",
    "FaceAction",
    "FaceActionDetector",
    "FaceActionEvent",
    "FaceMotionFilter",
    "FaceMotionFilterConfig",
    "FullBodyPoseState",
    "FullBodyTrackerConfig",
    "GreenScreenConfig",
    "HeadPose",
    "HoodMarkerColor",
    "HoodMarkerHeadTracker",
    "HoodMarkerObservation",
    "HoodMarkerSnapshot",
    "HoodMarkerTrackerConfig",
    "HoodTrackingSource",
    "MediaPipeFullBodyTracker",
    "MediaPipePersonSegmenter",
    "NormalizedLandmark",
    "OneEuroFilter",
    "OneEuroParameters",
    "PoseLandmark",
    "PersonSegmentationState",
    "TrackingSnapshot",
    "apply_green_screen",
]
