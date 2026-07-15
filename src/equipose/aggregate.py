"""Aggregate a per-frame metric series into a SessionMetric.

Stats over valid (non-None) frames: mean, std, %-time-in-acceptable-range, max
deviation outside the range, and a graded proximity-to-ideal score (what the
overall score is built from). Coverage (valid/total) and mean confidence are
recorded so scoring can gate unreliable metrics.
"""
from __future__ import annotations

import math
from typing import Optional

from equipose.config import ThresholdConfig
from equipose.schemas import SessionMetric


def _deviation_outside(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo - value
    if value > hi:
        return value - hi
    return 0.0


def _graded_frame_score(value: float, lo: float, hi: float,
                        higher_is_better: bool = False, lower_is_better: bool = False) -> float:
    """Smooth proximity-to-ideal in [0,1] — a Gaussian shoulder off the ideal.

    Grades *how good*, not just in/out: 1.0 at the ideal, ~0.607 at the acceptable
    edge, decaying toward 0 for gross deviations. The ideal and falloff scale come
    only from the band + a directionality flag (no invented cutoffs):
      - higher_is_better -> ideal = hi (values >= hi score 1.0), sigma = band width
      - lower_is_better  -> ideal = lo (values <= lo score 1.0), sigma = band width
      - otherwise        -> ideal = band centre, sigma = half-width (edge -> ~0.607)
    """
    if hi <= lo:
        return 1.0 if lo <= value <= hi else 0.0
    if higher_is_better:
        if value >= hi:
            return 1.0
        ideal, sigma = hi, (hi - lo)
    elif lower_is_better:
        if value <= lo:
            return 1.0
        ideal, sigma = lo, (hi - lo)
    else:
        ideal, sigma = (lo + hi) / 2.0, (hi - lo) / 2.0
    z = (value - ideal) / sigma
    return math.exp(-0.5 * z * z)


def aggregate_metric(name: str, per_frame_values: list[Optional[float]],
                     per_frame_conf: list[float], thresholds: ThresholdConfig) -> SessionMetric:
    mt = thresholds.metrics[name]
    lo, hi = mt.acceptable
    n_total = len(per_frame_values)
    pairs = [(v, c) for v, c in zip(per_frame_values, per_frame_conf) if v is not None]
    n_valid = len(pairs)
    if n_valid == 0:
        return SessionMetric(name=name, reliability=mt.reliability, unit=mt.unit,
                             n_valid_frames=0, n_total_frames=n_total)
    vals = [v for v, _ in pairs]
    confs = [c for _, c in pairs]
    mean = sum(vals) / n_valid
    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / n_valid)
    devs = [_deviation_outside(v, lo, hi) for v in vals]
    pct_in_range = sum(1 for d in devs if d == 0.0) / n_valid
    graded = sum(_graded_frame_score(v, lo, hi, mt.higher_is_better, mt.lower_is_better)
                 for v in vals) / n_valid
    return SessionMetric(
        name=name,
        reliability=mt.reliability,
        unit=mt.unit,
        mean=mean,
        max_deviation=max(devs),
        pct_in_range=pct_in_range,
        graded_score=graded,
        std=std,
        n_valid_frames=n_valid,
        n_total_frames=n_total,
        confidence=sum(confs) / n_valid,
    )
