"""Face-blur for any exported media. Reimplements BART_LAB io_export._blur_face.

Pediatric medical data: every frame written to disk or shown in an export must
have the child's face obscured.
"""
from __future__ import annotations

import numpy as np

from equipose.schemas import Landmark


def blur_faces(frame_bgr: np.ndarray, landmarks: list[Landmark],
               radius_scale: float = 0.6, min_conf: float = 0.2) -> np.ndarray:
    """Gaussian-blur a circular region around the nose. Returns a new array."""
    import cv2

    by = {lm.name: lm for lm in landmarks}
    nose = by.get("nose")
    if nose is None or nose.confidence < min_conf:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    if "left_shoulder" in by and "right_shoulder" in by:
        shoulder_w = abs(by["left_shoulder"].x_px - by["right_shoulder"].x_px)
        radius = int(max(20, shoulder_w * radius_scale))
    else:
        radius = int(max(20, 0.08 * w))
    cx, cy = int(round(nose.x_px)), int(round(nose.y_px))
    if not (0 <= cx < w and 0 <= cy < h):
        return frame_bgr
    out = frame_bgr.copy()
    k = max(11, (radius // 2) * 2 + 1)  # odd kernel
    blurred = cv2.GaussianBlur(out, (k, k), 0)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (cx, cy), radius, 255, -1)
    out[mask == 255] = blurred[mask == 255]
    return out
