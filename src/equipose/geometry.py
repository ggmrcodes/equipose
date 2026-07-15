"""Pure 2D geometry primitives. No I/O, no model deps — only numpy.

Reimplements the BART_LAB ``flags.py`` helpers (``_joint_angle_deg``,
``_perpendicular_distance``, ``_midpoint``, ``_by_name``) and adds the
line-tilt helpers needed for coronal/sagittal posture metrics.

This module is the backbone of the unit-test strategy: synthetic landmarks of
known geometry -> known angles.
"""
from __future__ import annotations

import math
from typing import Union

import numpy as np

from equipose.schemas import Landmark

# Default confidence gate (mirrors BART_LAB flags.CONF_MIN).
CONF_MIN = 0.5

Point = tuple[float, float]
PointLike = Union[Landmark, Point]


def _xy(p: PointLike) -> Point:
    if isinstance(p, Landmark):
        return (p.x_px, p.y_px)
    return (float(p[0]), float(p[1]))


def by_name(landmarks: list[Landmark], conf_min: float = CONF_MIN) -> dict[str, Landmark]:
    """Index landmarks by name, dropping any below the confidence gate."""
    return {lm.name: lm for lm in landmarks if lm.confidence >= conf_min}


def midpoint(a: PointLike, b: PointLike) -> Point:
    ax, ay = _xy(a)
    bx, by = _xy(b)
    return ((ax + bx) / 2.0, (ay + by) / 2.0)


def joint_angle_deg(a: PointLike, mid: PointLike, b: PointLike) -> float:
    """Angle at ``mid`` formed by vectors mid->a and mid->b. 180 deg = straight."""
    ax, ay = _xy(a)
    mx, my = _xy(mid)
    bx, by = _xy(b)
    v1 = np.array([ax - mx, ay - my])
    v2 = np.array([bx - mx, by - my])
    n1 = float(np.linalg.norm(v1))
    n2 = float(np.linalg.norm(v2))
    if n1 == 0.0 or n2 == 0.0:
        return 180.0
    cos_t = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return math.degrees(math.acos(cos_t))


def perpendicular_distance(point: PointLike, line_a: PointLike, line_b: PointLike) -> float:
    """Distance from ``point`` to the infinite line through line_a and line_b (px)."""
    px, py = _xy(point)
    ax, ay = _xy(line_a)
    bx, by = _xy(line_b)
    num = abs((by - ay) * px - (bx - ax) * py + bx * ay - by * ax)
    den = math.hypot(by - ay, bx - ax)
    return num / den if den > 0 else 0.0


def signed_perpendicular_distance(point: PointLike, line_a: PointLike, line_b: PointLike) -> float:
    """Signed distance from ``point`` to the directed line line_a -> line_b (px).

    Same magnitude as :func:`perpendicular_distance`; the sign flags which side of
    the directed line the point lies on (consistent for a fixed a->b ordering).
    Callers map the sign to anatomy themselves (e.g. anterior vs posterior)."""
    px, py = _xy(point)
    ax, ay = _xy(line_a)
    bx, by = _xy(line_b)
    num = (by - ay) * px - (bx - ax) * py + bx * ay - by * ax
    den = math.hypot(by - ay, bx - ax)
    return num / den if den > 0 else 0.0


def _normalize_tilt(ang_deg: float) -> float:
    """Fold an angle into [-90, 90] so tilt is independent of point ordering."""
    if ang_deg > 90.0:
        ang_deg -= 180.0
    elif ang_deg < -90.0:
        ang_deg += 180.0
    return ang_deg


def line_angle_from_horizontal_deg(a: PointLike, b: PointLike) -> float:
    """Signed tilt of line a->b from horizontal, in [-90, 90]. 0 = level.

    Image y grows downward, so a positive value means the line slopes downward
    to the right.
    """
    ax, ay = _xy(a)
    bx, by = _xy(b)
    return _normalize_tilt(math.degrees(math.atan2(by - ay, bx - ax)))


def line_angle_from_vertical_deg(a: PointLike, b: PointLike) -> float:
    """Signed tilt of line a->b from vertical, in [-90, 90]. 0 = plumb.

    Positive = the lower point is to the right of the upper point (lean right).
    """
    ax, ay = _xy(a)
    bx, by = _xy(b)
    return _normalize_tilt(math.degrees(math.atan2(bx - ax, by - ay)))


def euclidean(a: PointLike, b: PointLike) -> float:
    ax, ay = _xy(a)
    bx, by = _xy(b)
    return math.hypot(bx - ax, by - ay)
