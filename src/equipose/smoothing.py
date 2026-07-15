"""Temporal smoothing for noisy per-frame angle series.

OneEuroFilter (time-aware, streaming) reduces jitter while staying responsive.
``smooth_series`` interpolates SHORT gaps of missing (occluded) frames and
leaves LONG gaps as ``None`` — and resets the filter across any gap so a long
occlusion doesn't smear stale values forward.
"""
from __future__ import annotations

import math
from typing import Optional


class OneEuroFilter:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.0, d_cutoff: float = 1.0) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x_prev: Optional[float] = None
        self._dx_prev: float = 0.0
        self._t_prev: Optional[float] = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, t: float, x: float) -> float:
        if self._t_prev is None:
            self._t_prev, self._x_prev, self._dx_prev = t, x, 0.0
            return x
        dt = t - self._t_prev
        if dt <= 0:
            dt = 1e-6
        dx = (x - self._x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1 - a_d) * self._dx_prev
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self._x_prev
        self._t_prev, self._x_prev, self._dx_prev = t, x_hat, dx_hat
        return x_hat


def smooth_series(times: list[float], values: list[Optional[float]], max_gap: int = 5,
                  min_cutoff: float = 1.0, beta: float = 0.0, d_cutoff: float = 1.0
                  ) -> list[Optional[float]]:
    n = len(values)
    if n == 0:
        return []
    filled = list(values)

    # Linearly interpolate interior gaps no longer than max_gap.
    i = 0
    while i < n:
        if filled[i] is None:
            j = i
            while j < n and filled[j] is None:
                j += 1
            left = filled[i - 1] if i - 1 >= 0 else None
            right = filled[j] if j < n else None
            if left is not None and right is not None and (j - i) <= max_gap:
                span = j - (i - 1)
                for k in range(i, j):
                    frac = (k - (i - 1)) / span
                    filled[k] = left + (right - left) * frac
            i = j
        else:
            i += 1

    # OneEuro over contiguous non-None runs; reset filter across any gap.
    out: list[Optional[float]] = [None] * n
    flt = OneEuroFilter(min_cutoff, beta, d_cutoff)
    for idx in range(n):
        v = filled[idx]
        if v is None:
            out[idx] = None
            flt = OneEuroFilter(min_cutoff, beta, d_cutoff)
        else:
            out[idx] = flt.filter(times[idx], v)
    return out
