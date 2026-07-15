"""MoveNet SinglePose Thunder (ONNX) backend — the fallback.

Reimplements the proven ``sample/movenet_skeleton.py`` logic as a backend:
letterbox the input to a square, run ONNX inference, map the 17 normalized
COCO keypoints back to the input image's pixel space. Needs only
``onnxruntime`` + ``opencv`` — no MediaPipe — so it is the install-robust
fallback if MediaPipe wheels misbehave.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from equipose.schemas import Landmark

# MoveNet/COCO-17 output order.
_COCO_NAMES = (
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
)

_DEFAULT_ONNX = Path(__file__).resolve().parents[3] / "models" / "movenet_singlepose_thunder_4.onnx"
_INPUT_SIZE = 256


class MoveNetPoseBackend:
    def __init__(self, model_path: Optional[str | Path] = None) -> None:
        self._model_path = Path(model_path) if model_path else _DEFAULT_ONNX
        self._sess = None
        self._in_name: Optional[str] = None
        self._in_type: Optional[str] = None

    def _session(self):  # pragma: no cover - needs the model file
        import onnxruntime as ort

        if self._sess is None:
            self._sess = ort.InferenceSession(str(self._model_path), providers=["CPUExecutionProvider"])
            meta = self._sess.get_inputs()[0]
            self._in_name = meta.name
            self._in_type = meta.type
        return self._sess

    def _raw_process(self, square_rgb_uint8: np.ndarray) -> np.ndarray:  # pragma: no cover - mocked in tests
        """Input 256x256x3 uint8 RGB -> (17,3) array of (y, x, score) normalized."""
        sess = self._session()
        arr = square_rgb_uint8[None, ...]
        if "int32" in (self._in_type or ""):
            arr = arr.astype(np.int32)
        elif "uint8" in (self._in_type or ""):
            arr = arr.astype(np.uint8)
        else:
            arr = arr.astype(np.float32)
        out = sess.run(None, {self._in_name: arr})[0]
        return np.asarray(out)[0, 0]

    def detect(self, image_bgr: np.ndarray) -> list[Landmark]:
        import cv2

        h, w = image_bgr.shape[:2]
        side = max(h, w)
        oy, ox = (side - h) // 2, (side - w) // 2
        square = np.zeros((side, side, 3), dtype=np.uint8)
        square[oy:oy + h, ox:ox + w] = image_bgr[:, :, ::-1]  # BGR -> RGB
        inp = cv2.resize(square, (_INPUT_SIZE, _INPUT_SIZE), interpolation=cv2.INTER_LINEAR)
        kps = self._raw_process(inp)
        out: list[Landmark] = []
        for i, (ny, nx, score) in enumerate(kps):
            px = float(nx) * side - ox
            py = float(ny) * side - oy
            out.append(Landmark(name=_COCO_NAMES[i], x_px=px, y_px=py, confidence=float(score)))
        return out
