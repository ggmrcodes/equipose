"""Per-frame quality control + the occlusion (visibility) gate.

``run_qc`` reimplements the BART_LAB ``capture.run_qc`` Laplacian-variance blur
and luma checks (ArUco dropped — no calibration markers here).
``frame_visibility_ok`` is the occlusion gate that decides whether a metric's
required landmarks are reliably visible.
"""
from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict

from equipose.schemas import Landmark

DEFAULT_VIS_THRESHOLD = 0.3


class QCReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blur_var: float
    luma_mean: float
    ok: bool
    reasons: list[str]


def run_qc(frame_bgr: np.ndarray, min_blur_var: float = 40.0,
           luma_range: tuple[float, float] = (30.0, 235.0)) -> QCReport:
    import cv2

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    luma_mean = float(gray.mean())
    reasons: list[str] = []
    if blur_var < min_blur_var:
        reasons.append("blurry")
    if not (luma_range[0] <= luma_mean <= luma_range[1]):
        reasons.append("bad_luma")
    return QCReport(blur_var=blur_var, luma_mean=luma_mean, ok=not reasons, reasons=reasons)


def frame_visibility_ok(landmarks: list[Landmark], required_names,
                        vis_threshold: float = DEFAULT_VIS_THRESHOLD) -> bool:
    by = {lm.name: lm for lm in landmarks}
    return all(n in by and by[n].confidence >= vis_threshold for n in required_names)
