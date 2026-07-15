"""Front-view (coronal-plane) posture metrics.

Each metric returns (value | None, confidence). ``None`` means required
landmarks were occluded/low-confidence and the metric is skipped for the frame.
PRIMARY metrics use head/shoulder/trunk (reliably visible above the saddle);
``pelvic_obliquity`` is BEST-EFFORT (occluded on the pony).

These are 2D in-image-plane approximations — see docs/ANGLE_DEFINITIONS.md.
"""
from __future__ import annotations

from typing import Optional

from equipose import geometry as geo
from equipose.schemas import Landmark

FRONT_METRICS = (
    "head_tilt",
    "shoulder_tilt",
    "trunk_lateral_lean",
    "pelvic_obliquity",
    "midline_deviation",
    "symmetry_score",
)


# Per-component "full deviation" scales: how far off each input has to be to count
# as fully asymmetric (1.0 penalty). Each input is normalized to [0,1] by its own
# scale so the composite is unit-consistent. Scales are provisional (tuned at pilot).
_SYM_SCALE = {"head_tilt": 15.0, "shoulder_tilt": 15.0, "midline_deviation": 0.25}


def _symmetry_score(values: dict[str, Optional[float]]) -> Optional[float]:
    """Composite 0-100 (100 = level & centered).

    Mean of each component's normalized deviation (|value| / its scale, clamped to
    1), inverted to a 0-100 score. Unit-consistent and bounded, so no single
    component (e.g. midline) can dominate. Averages over whatever is available.
    """
    pen: list[float] = []
    for name, scale in _SYM_SCALE.items():
        v = values.get(name)
        if v is not None:
            pen.append(min(1.0, abs(v) / scale))
    if not pen:
        return None
    return 100.0 * (1.0 - sum(pen) / len(pen))


def compute_front(landmarks: list[Landmark], vis_threshold: float = 0.3
                  ) -> tuple[dict[str, Optional[float]], dict[str, float]]:
    by = {lm.name: lm for lm in landmarks}
    values: dict[str, Optional[float]] = {}
    confidences: dict[str, float] = {}

    def vis(*names: str) -> bool:
        return all(n in by and by[n].confidence >= vis_threshold for n in names)

    def conf(*names: str) -> float:
        cs = [by[n].confidence for n in names if n in by]
        return min(cs) if len(cs) == len(names) else 0.0

    def emit(name: str, value: Optional[float], c: float) -> None:
        values[name] = value
        confidences[name] = c if value is not None else 0.0

    # 1. Head tilt — PRIMARY (ears, fallback eyes).
    if vis("left_ear", "right_ear"):
        emit("head_tilt", geo.line_angle_from_horizontal_deg(by["left_ear"], by["right_ear"]),
             conf("left_ear", "right_ear"))
    elif vis("left_eye", "right_eye"):
        emit("head_tilt", geo.line_angle_from_horizontal_deg(by["left_eye"], by["right_eye"]),
             conf("left_eye", "right_eye") * 0.8)
    else:
        emit("head_tilt", None, 0.0)

    # 2. Shoulder tilt — PRIMARY.
    if vis("left_shoulder", "right_shoulder"):
        emit("shoulder_tilt", geo.line_angle_from_horizontal_deg(by["left_shoulder"], by["right_shoulder"]),
             conf("left_shoulder", "right_shoulder"))
    else:
        emit("shoulder_tilt", None, 0.0)

    # 3. Trunk lateral lean — PRIMARY (shoulders->hips, fallback nose->shoulders).
    if vis("left_shoulder", "right_shoulder", "left_hip", "right_hip"):
        sh = geo.midpoint(by["left_shoulder"], by["right_shoulder"])
        hp = geo.midpoint(by["left_hip"], by["right_hip"])
        emit("trunk_lateral_lean", geo.line_angle_from_vertical_deg(sh, hp),
             conf("left_shoulder", "right_shoulder", "left_hip", "right_hip"))
    elif vis("left_shoulder", "right_shoulder", "nose"):
        sh = geo.midpoint(by["left_shoulder"], by["right_shoulder"])
        emit("trunk_lateral_lean", geo.line_angle_from_vertical_deg(by["nose"], sh),
             conf("left_shoulder", "right_shoulder", "nose") * 0.6)
    else:
        emit("trunk_lateral_lean", None, 0.0)

    # 4. Pelvic obliquity — BEST-EFFORT.
    if vis("left_hip", "right_hip"):
        emit("pelvic_obliquity", geo.line_angle_from_horizontal_deg(by["left_hip"], by["right_hip"]),
             conf("left_hip", "right_hip"))
    else:
        emit("pelvic_obliquity", None, 0.0)

    # 5. Midline deviation — PRIMARY (nose off the shoulder-hip axis, normalized).
    if vis("nose", "left_shoulder", "right_shoulder", "left_hip", "right_hip"):
        sh = geo.midpoint(by["left_shoulder"], by["right_shoulder"])
        hp = geo.midpoint(by["left_hip"], by["right_hip"])
        dev_px = geo.perpendicular_distance(by["nose"], sh, hp)
        shoulder_w = geo.euclidean(by["left_shoulder"], by["right_shoulder"])
        emit("midline_deviation", (dev_px / shoulder_w) if shoulder_w > 0 else None,
             conf("nose", "left_shoulder", "right_shoulder", "left_hip", "right_hip"))
    else:
        emit("midline_deviation", None, 0.0)

    # 6. Symmetry score — PRIMARY composite.
    sym = _symmetry_score(values)
    comp = [confidences[k] for k in ("head_tilt", "shoulder_tilt", "midline_deviation")
            if values.get(k) is not None]
    emit("symmetry_score", sym, min(comp) if comp else 0.0)

    return values, confidences
