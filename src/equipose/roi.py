"""Region-of-interest tracker — locks pose estimation onto the child rider.

MediaPipe/MoveNet return a single person, so in a scene with side-walkers we
must feed the model only the child. The operator picks the child's bbox on the
first frame (dashboard ``roi_select``); thereafter the box re-centers on the
torso centroid each frame.

The crop/letterbox/map-back math mirrors ``sample/movenet_skeleton.py`` so the
pose backend always sees a clean square containing one person.
"""
from __future__ import annotations

import numpy as np

from equipose.schemas import Landmark

Bbox = tuple[int, int, int, int]  # (left, top, right, bottom)
_CENTROID_NAMES = ("left_shoulder", "right_shoulder", "left_hip", "right_hip", "nose")


class RoiTracker:
    def __init__(self, init_bbox: Bbox, pad: float = 0.15, smooth: float = 0.5) -> None:
        l, t, r, b = init_bbox
        self._bbox: Bbox = (int(l), int(t), int(r), int(b))
        self._pad = pad
        self._smooth = smooth

    @property
    def bbox(self) -> Bbox:
        return self._bbox

    def crop(self, frame: np.ndarray) -> tuple[np.ndarray, dict]:
        """Return (square_bgr_crop, transform) for the current padded bbox."""
        h, w = frame.shape[:2]
        l, t, r, b = self._bbox
        bw, bh = r - l, b - t
        l2 = max(0, int(l - bw * self._pad))
        t2 = max(0, int(t - bh * self._pad))
        r2 = min(w, int(r + bw * self._pad))
        b2 = min(h, int(b + bh * self._pad))
        crop = frame[t2:b2, l2:r2]
        ch, cw = crop.shape[:2]
        side = max(ch, cw, 1)
        ox, oy = (side - cw) // 2, (side - ch) // 2
        square = np.zeros((side, side, 3), dtype=frame.dtype)
        if ch > 0 and cw > 0:
            square[oy:oy + ch, ox:ox + cw] = crop
        return square, {"l": l2, "t": t2, "ox": ox, "oy": oy, "side": side}

    @staticmethod
    def map_back(landmarks: list[Landmark], transform: dict) -> list[Landmark]:
        """Map landmarks from square-crop pixel space back to full-frame pixels."""
        dl = transform["l"] - transform["ox"]
        dt = transform["t"] - transform["oy"]
        return [
            Landmark(name=lm.name, x_px=lm.x_px + dl, y_px=lm.y_px + dt, confidence=lm.confidence)
            for lm in landmarks
        ]

    def update_from_landmarks(self, landmarks_full: list[Landmark], conf_min: float = 0.3) -> None:
        """Re-center the (fixed-size) bbox on the torso centroid, smoothed."""
        pts = [(lm.x_px, lm.y_px) for lm in landmarks_full
                if lm.name in _CENTROID_NAMES and lm.confidence >= conf_min]
        if len(pts) < 2:
            return
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        l, t, r, b = self._bbox
        bw, bh = r - l, b - t
        ccx, ccy = (l + r) / 2.0, (t + b) / 2.0
        sx = self._smooth * cx + (1 - self._smooth) * ccx
        sy = self._smooth * cy + (1 - self._smooth) * ccy
        self._bbox = (int(sx - bw / 2), int(sy - bh / 2), int(sx + bw / 2), int(sy + bh / 2))
