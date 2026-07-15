"""Skeleton overlay drawing.

``draw_skeleton`` renders pose landmarks onto an image. For a FRONT view it
draws the full COCO skeleton (magenta=left, cyan=right, yellow=center). For a
SIDE view it keeps ONLY the camera-facing side's chain (the 2D sagittal
skeleton), reusing ``angles_side.pick_side`` — no cross-body lines, no far-side
limbs.
"""
from __future__ import annotations

import numpy as np

from equipose.angles_side import pick_side
from equipose.schemas import Landmark

# BGR colors (OpenCV).
_M = (200, 0, 255)        # left limbs (magenta)
_C = (255, 200, 0)        # right limbs (cyan)
_Y = (0, 215, 255)        # center/torso (yellow)
_SIDE_BONE = (255, 220, 0)  # single color for the sagittal chain
_JOINT = (60, 60, 255)      # red
_JOINT_OUTLINE = (255, 255, 255)

_FRONT_EDGES = [
    ("nose", "left_eye", _M), ("nose", "right_eye", _C),
    ("left_eye", "left_ear", _M), ("right_eye", "right_ear", _C),
    ("left_shoulder", "right_shoulder", _Y),
    ("left_shoulder", "left_elbow", _M), ("left_elbow", "left_wrist", _M),
    ("right_shoulder", "right_elbow", _C), ("right_elbow", "right_wrist", _C),
    ("left_shoulder", "left_hip", _M), ("right_shoulder", "right_hip", _C),
    ("left_hip", "right_hip", _Y),
    ("left_hip", "left_knee", _M), ("left_knee", "left_ankle", _M),
    ("right_hip", "right_knee", _C), ("right_knee", "right_ankle", _C),
]


def _side_edges(side: str) -> list[tuple[str, str, tuple]]:
    chain = [
        ("nose", f"{side}_eye"),
        (f"{side}_eye", f"{side}_ear"),
        (f"{side}_ear", f"{side}_shoulder"),
        (f"{side}_shoulder", f"{side}_elbow"),
        (f"{side}_elbow", f"{side}_wrist"),
        (f"{side}_shoulder", f"{side}_hip"),
        (f"{side}_hip", f"{side}_knee"),
        (f"{side}_knee", f"{side}_ankle"),
    ]
    return [(a, b, _SIDE_BONE) for a, b in chain]


def draw_skeleton(image_bgr: np.ndarray, landmarks: list[Landmark], view: str,
                  vis_threshold: float = 0.3) -> np.ndarray:
    """Return a copy of ``image_bgr`` with the (view-appropriate) skeleton drawn."""
    import cv2

    out = image_bgr.copy()
    h, w = out.shape[:2]
    lw = max(2, round(w / 200))
    rad = max(3, round(w / 130))
    by = {lm.name: lm for lm in landmarks}

    if view == "side":
        side = pick_side(by)
        edges = _side_edges(side)
        kept = {"nose", f"{side}_eye", f"{side}_ear", f"{side}_shoulder",
                f"{side}_elbow", f"{side}_wrist", f"{side}_hip", f"{side}_knee", f"{side}_ankle"}
    else:
        edges = _FRONT_EDGES
        kept = set(by.keys())

    for a, b, col in edges:
        la, lb = by.get(a), by.get(b)
        if la and lb and la.confidence >= vis_threshold and lb.confidence >= vis_threshold:
            cv2.line(out, (int(la.x_px), int(la.y_px)), (int(lb.x_px), int(lb.y_px)),
                     col, lw, cv2.LINE_AA)

    for name in kept:
        lm = by.get(name)
        if lm and lm.confidence >= vis_threshold:
            p = (int(lm.x_px), int(lm.y_px))
            cv2.circle(out, p, rad, _JOINT, -1, cv2.LINE_AA)
            cv2.circle(out, p, rad, _JOINT_OUTLINE, 1, cv2.LINE_AA)

    return out
