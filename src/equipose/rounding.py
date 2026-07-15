"""Back-roundness (thoracic kyphosis proxy) from the rider's silhouette.

The skeleton (ear/shoulder/hip) is blind to thoracic rounding — the curve lives
*between* those surface points. This measures the **bow of the back silhouette off
its own top->bottom chord**, normalized by the chord length: it captures the curve
directly and isolates it from torso thickness (validated in the 2026-07-14 spike).

Split for testability: ``back_roundness_from_mask`` is pure (unit-tested on synthetic
masks); ``_segment_person`` is the model seam (bundled offline selfie segmenter);
``back_roundness_index`` orchestrates. Returns ``None`` when it can't segment/measure —
never a false "good".
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import numpy as np

from equipose.schemas import Landmark

# repo_root/models/...  (src/equipose/rounding.py -> parents[2] == repo root)
_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "selfie_segmenter.tflite"
_SEGMENTER = None  # built lazily on first real inference


def back_roundness_from_mask(mask: np.ndarray, shoulder: tuple[float, float],
                             hip: tuple[float, float], facing: str,
                             min_points: int = 5) -> Optional[float]:
    """Bow of the posterior torso contour off its own chord / chord length (>= 0).

    ``mask`` is a person mask (nonzero = person) at the same pixel scale as the
    shoulder/hip points. ``facing`` in {"left","right"} decides which silhouette edge
    is the back (facing left -> back is the right edge). ``None`` if too few contour
    points to trust."""
    person = np.asarray(mask) > 0
    if person.ndim == 3:
        person = person[..., 0]
    h = person.shape[0]
    S = (float(shoulder[0]), float(shoulder[1]))
    H = (float(hip[0]), float(hip[1]))
    trunk = math.hypot(S[0] - H[0], S[1] - H[1])
    if trunk <= 0:
        return None
    posterior_right = facing == "left"     # facing left -> back is the right edge

    pts: list[tuple[float, float]] = []
    y0, y1 = int(min(S[1], H[1])), int(max(S[1], H[1]))
    for y in range(max(0, y0), min(h, y1)):
        cx = S[0] + (H[0] - S[0]) * (y - S[1]) / ((H[1] - S[1]) or 1)
        row = np.where(person[y])[0]
        if row.size == 0:
            continue
        row = row[(row > cx - 1.2 * trunk) & (row < cx + 1.2 * trunk)]  # trunk only
        if row.size == 0:
            continue
        bx = float(row.max()) if posterior_right else float(row.min())
        pts.append((bx, float(y)))
    if len(pts) < min_points:
        return None

    top = (float(np.mean([p[0] for p in pts[:3]])), float(np.mean([p[1] for p in pts[:3]])))
    bot = (float(np.mean([p[0] for p in pts[-3:]])), float(np.mean([p[1] for p in pts[-3:]])))
    back_len = math.hypot(top[0] - bot[0], top[1] - bot[1]) or 1.0

    def perp(p: tuple[float, float]) -> float:  # signed perpendicular distance to top->bot
        num = ((bot[1] - top[1]) * p[0] - (bot[0] - top[0]) * p[1]
               + bot[0] * top[1] - bot[1] * top[0])
        return num / back_len

    devs = [perp(p) if posterior_right else -perp(p) for p in pts]  # posterior bulge positive
    return max(0.0, max(devs) / back_len)


def _segment_person(crop_bgr: np.ndarray) -> np.ndarray:  # pragma: no cover - needs model
    """Binary person mask for the crop via the bundled offline selfie segmenter.

    Uses the uint8 *category* mask (the float PoseLandmarker mask read hard-crashes)."""
    global _SEGMENTER
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    if _SEGMENTER is None:
        _SEGMENTER = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(_MODEL_PATH)),
            running_mode=vision.RunningMode.IMAGE, output_category_mask=True))
    rgb = np.ascontiguousarray(crop_bgr[:, :, ::-1])
    res = _SEGMENTER.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    cat = np.asarray(res.category_mask.numpy_view())
    if cat.ndim == 3:
        cat = cat[..., 0]
    dom = int(np.bincount(cat.ravel()).argmax())   # dominant class = background
    return (cat != dom).astype(np.uint8)


def back_roundness_index(crop_bgr: np.ndarray, landmarks: list[Landmark],
                         vis_threshold: float = 0.3) -> Optional[float]:
    """Orchestrate: segment the crop, then measure the back bow. Landmarks must be in
    CROP pixel space (same frame as the crop image). ``None`` on any failure."""
    from equipose.angles_side import facing_direction, pick_side

    by = {lm.name: lm for lm in landmarks}
    side = pick_side(by)
    sh, hp = by.get(f"{side}_shoulder"), by.get(f"{side}_hip")
    if sh is None or hp is None or sh.confidence < vis_threshold or hp.confidence < vis_threshold:
        return None
    try:
        mask = _segment_person(crop_bgr)
    except Exception:
        return None
    return back_roundness_from_mask(mask, (sh.x_px, sh.y_px), (hp.x_px, hp.y_px),
                                    facing_direction(landmarks, vis_threshold))
