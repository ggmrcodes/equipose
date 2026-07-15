"""PoseBackend protocol + factory so downstream code is backend-agnostic.

Every backend takes a BGR image and returns landmarks in THAT image's pixel
space, named with the shared ``CANONICAL_NAMES`` vocabulary. ``confidence``
carries the backend's visibility/score (the occlusion signal).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np

from equipose.schemas import Landmark

# COCO-17-style canonical vocabulary, extended with eyes/ears (needed for head tilt).
CANONICAL_NAMES = (
    "nose",
    "left_eye", "right_eye",
    "left_ear", "right_ear",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
)


@runtime_checkable
class PoseBackend(Protocol):
    def detect(self, image_bgr: np.ndarray) -> list[Landmark]:
        """Return canonical landmarks in ``image_bgr`` pixel space ([] if none)."""
        ...


def get_backend(name: str = "mediapipe", **kwargs) -> PoseBackend:
    name = name.lower()
    if name == "mediapipe":
        from equipose.pose_backend.mediapipe_backend import MediaPipePoseBackend

        return MediaPipePoseBackend(**kwargs)
    if name == "movenet":
        from equipose.pose_backend.movenet_backend import MoveNetPoseBackend

        return MoveNetPoseBackend(**kwargs)
    raise ValueError(f"unknown pose backend: {name!r}")
