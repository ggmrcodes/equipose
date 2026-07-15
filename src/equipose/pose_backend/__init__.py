"""Swappable pose-estimation backends behind a common Protocol."""
from equipose.pose_backend.base import CANONICAL_NAMES, PoseBackend, get_backend

__all__ = ["CANONICAL_NAMES", "PoseBackend", "get_backend"]
