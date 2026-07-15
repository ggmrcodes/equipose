"""Offline video reader. Yields (frame_idx, t_sec, frame_bgr) and exposes fps.

Front and side videos are read independently (no hardware sync).
"""
from __future__ import annotations

from typing import Iterator, Tuple

import numpy as np


class VideoSession:
    def __init__(self, path: str) -> None:
        self.path = str(path)
        self._fps: float | None = None

    @property
    def fps(self) -> float:
        if self._fps is None:
            import cv2

            cap = cv2.VideoCapture(self.path)
            self._fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
            cap.release()
        return self._fps

    def frames(self) -> Iterator[Tuple[int, float, np.ndarray]]:
        import cv2

        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            cap.release()
            raise FileNotFoundError(f"cannot open video: {self.path}")
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        self._fps = fps
        idx = 0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                yield idx, idx / fps, frame
                idx += 1
        finally:
            cap.release()
