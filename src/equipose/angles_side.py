"""Side-view (sagittal-plane) posture metrics.

The camera-facing side is auto-selected by mean landmark confidence. Each
metric returns (value | None, confidence). ``forward_trunk_lean`` and
``neck_forward_angle`` are PRIMARY; ``hip_flexion`` and ``knee_angle`` are
BEST-EFFORT (occluded by the saddle/horse). 2D approximations — see
docs/ANGLE_DEFINITIONS.md.
"""
from __future__ import annotations

from typing import Optional

from equipose import geometry as geo
from equipose.schemas import Landmark

SIDE_METRICS = (
    "forward_trunk_lean",
    "neck_forward_angle",
    "hip_flexion",
    "knee_angle",
)


def pick_side(by: dict[str, Landmark]) -> str:
    """Choose the camera-facing side by mean landmark confidence."""
    def side_conf(side: str) -> float:
        names = [f"{side}_shoulder", f"{side}_hip", f"{side}_ear", f"{side}_knee", f"{side}_ankle"]
        cs = [by[n].confidence for n in names if n in by]
        return sum(cs) / len(cs) if cs else 0.0

    return "left" if side_conf("left") >= side_conf("right") else "right"


def facing_direction(landmarks: list[Landmark], vis_threshold: float = 0.3) -> str:
    """Which way the subject faces in the image: ``"left"`` or ``"right"``.

    Image x grows rightward. On the camera-facing side (:func:`pick_side`), an
    anterior landmark sits ahead of a posterior one in the facing direction. The
    knee-vs-hip offset is the strongest cue for a seated rider (the femur points
    forward); nose-vs-ear and ear-vs-shoulder are fallbacks when the lower body is
    occluded. Purely cosmetic — used to orient the body-chart schematic to match
    the photo; the angle metrics themselves are orientation-invariant. Defaults to
    ``"right"`` (the schematic's base orientation) when no cue is available.
    """
    by = {lm.name: lm for lm in landmarks}
    side = pick_side(by)

    def x_of(name: str) -> Optional[float]:
        lm = by.get(name)
        return lm.x_px if lm is not None and lm.confidence >= vis_threshold else None

    # (anterior, posterior) pairs, strongest cue first.
    pairs = (
        (x_of(f"{side}_knee"), x_of(f"{side}_hip")),
        (x_of("nose"), x_of(f"{side}_ear")),
        (x_of(f"{side}_ear"), x_of(f"{side}_shoulder")),
    )
    for anterior, posterior in pairs:
        if anterior is not None and posterior is not None and abs(anterior - posterior) > 2.0:
            return "right" if anterior > posterior else "left"
    return "right"


def compute_side(landmarks: list[Landmark], vis_threshold: float = 0.3
                 ) -> tuple[dict[str, Optional[float]], dict[str, float]]:
    by = {lm.name: lm for lm in landmarks}
    side = pick_side(by)
    sh = by.get(f"{side}_shoulder")
    hp = by.get(f"{side}_hip")
    ear = by.get(f"{side}_ear")
    kn = by.get(f"{side}_knee")
    an = by.get(f"{side}_ankle")

    values: dict[str, Optional[float]] = {}
    confidences: dict[str, float] = {}

    def c(lm: Optional[Landmark]) -> float:
        return lm.confidence if lm is not None else 0.0

    def vis(*lms: Optional[Landmark]) -> bool:
        return all(lm is not None and lm.confidence >= vis_threshold for lm in lms)

    def emit(name: str, value: Optional[float], cf: float) -> None:
        values[name] = value
        confidences[name] = cf if value is not None else 0.0

    # 7. Forward trunk lean — PRIMARY (shoulder->hip, fallback ear->shoulder).
    if vis(sh, hp):
        emit("forward_trunk_lean", geo.line_angle_from_vertical_deg(sh, hp), min(c(sh), c(hp)))
    elif vis(sh, ear):
        emit("forward_trunk_lean", geo.line_angle_from_vertical_deg(ear, sh), min(c(sh), c(ear)) * 0.6)
    else:
        emit("forward_trunk_lean", None, 0.0)

    # 8. Neck forward angle — PRIMARY (ear-shoulder-hip).
    if vis(ear, sh, hp):
        emit("neck_forward_angle", geo.joint_angle_deg(ear, sh, hp), min(c(ear), c(sh), c(hp)))
    else:
        emit("neck_forward_angle", None, 0.0)

    # 9. Hip flexion — BEST-EFFORT (shoulder-hip-knee).
    if vis(sh, hp, kn):
        emit("hip_flexion", geo.joint_angle_deg(sh, hp, kn), min(c(sh), c(hp), c(kn)))
    else:
        emit("hip_flexion", None, 0.0)

    # 10. Knee angle — BEST-EFFORT (hip-knee-ankle).
    if vis(hp, kn, an):
        emit("knee_angle", geo.joint_angle_deg(hp, kn, an), min(c(hp), c(kn), c(an)))
    else:
        emit("knee_angle", None, 0.0)

    # NB: thoracic rounding is NOT computed here — the ear/shoulder/hip skeleton is
    # blind to it. It is measured from the silhouette in equipose.rounding
    # (back_roundness), injected by the pipeline for side photos.

    return values, confidences
