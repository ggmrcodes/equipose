"""Rule-based session score (0-100) + green/yellow/red band.

Per-metric sub-score = graded_score * 100 — a smooth proximity-to-ideal in [0,1]
(``aggregate._graded_frame_score``), so a merely-acceptable posture scores below a
near-ideal one instead of both pinning at 100. Falls back to the binary
pct_in_range for metrics aggregated before grading existed. Overall = a
weakest-link blend (``overall_from_breakdown``): halfway between the weighted mean
and the single worst joint, over metrics that clear the coverage gate (and, for
best-effort metrics, the confidence gate), so one bad joint is not averaged away.
``score_breakdown`` is the single source of truth — both ``score_session`` and the
dashboard's "why this score" view derive from it, so the number is always
explainable. All cutoffs come from config/scoring.yaml (provisional).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from equipose.config import ScoringConfig
from equipose.schemas import Band, SessionMetric


@dataclass
class ScoreEntry:
    name: str
    counted: bool
    reason: str             # "" if counted, else why it was excluded
    weight: float
    sub_score: Optional[float]   # 0..100, or None when excluded
    contribution: float          # weight * sub_score when counted, else 0


def score_breakdown(metrics: list[SessionMetric], scoring: ScoringConfig) -> list[ScoreEntry]:
    out: list[ScoreEntry] = []
    for m in metrics:
        w = scoring.weights.get(m.name, 1.0)
        if m.name in scoring.display_only:
            out.append(ScoreEntry(m.name, False, "summary (not scored)", w, None, 0.0))
            continue
        if m.n_total_frames == 0 or m.pct_in_range is None:
            out.append(ScoreEntry(m.name, False, "not detected", w, None, 0.0))
            continue
        coverage = m.n_valid_frames / m.n_total_frames
        if coverage < scoring.min_coverage:
            out.append(ScoreEntry(m.name, False, "low coverage", w, None, 0.0))
            continue
        if m.reliability == "best_effort" and m.confidence < scoring.best_effort_min_confidence:
            out.append(ScoreEntry(m.name, False, "low confidence", w, None, 0.0))
            continue
        # Graded proximity-to-ideal when available; fall back to the binary
        # in-range fraction for metrics aggregated before grading existed.
        frac = m.graded_score if m.graded_score is not None else m.pct_in_range
        sub = frac * 100.0
        out.append(ScoreEntry(m.name, True, "", w, sub, w * sub))
    return out


# Weakest-link blend: the overall is pulled from the weighted mean toward the
# single worst joint, so one bad metric can't be averaged away by good ones. 0.5
# = "halfway between the average joint and the worst joint". Not a clinical cutoff;
# tune here to lean softer (->0, pure mean) or harsher (->1, pure worst-joint).
WORST_WEIGHT = 0.5


def overall_from_breakdown(entries: list[ScoreEntry]) -> float:
    counted = [e for e in entries if e.counted]
    total_w = sum(e.weight for e in counted)
    if total_w <= 0:
        return 0.0
    weighted_mean = sum(e.contribution for e in counted) / total_w
    worst = min(e.sub_score for e in counted)
    return (1.0 - WORST_WEIGHT) * weighted_mean + WORST_WEIGHT * worst


def band_for(score: float, scoring: ScoringConfig) -> Band:
    if score >= scoring.green_min:
        return "green"
    if score >= scoring.yellow_min:
        return "yellow"
    return "red"


def metric_band(metric: SessionMetric, scoring: ScoringConfig) -> str:
    """Per-metric status band: ``green`` | ``yellow`` | ``red`` | ``none``.

    Graded on the SAME cutoffs as the overall score (``band_for`` on the metric's
    sub-score), so a joint's indicator matches how it actually scores — a value
    inside its range but near the edge reads ``yellow`` (Watch), not a flat ``green``.
    Falls back to the binary in-range fraction when no graded score is present."""
    if metric.pct_in_range is None:
        return "none"
    frac = metric.graded_score if metric.graded_score is not None else metric.pct_in_range
    return band_for(frac * 100.0, scoring)


def score_session(metrics: list[SessionMetric], scoring: ScoringConfig) -> tuple[float, Band]:
    entries = score_breakdown(metrics, scoring)
    score = overall_from_breakdown(entries)
    return score, band_for(score, scoring)
