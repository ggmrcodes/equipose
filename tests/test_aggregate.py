import math

import pytest

from equipose.aggregate import aggregate_metric
from equipose.config import load_thresholds


def test_graded_score_grades_within_band_symmetric():
    # head_tilt [-5,5] is symmetric: ideal = centre 0, sigma = half-width 5.
    # An in-range-but-not-ideal value grades BELOW 1.0 — this is what stops the
    # score pinning at 100 for every acceptable posture.
    th = load_thresholds()
    m = aggregate_metric("head_tilt", [2.5], [0.9], th)
    assert m.pct_in_range == 1.0                                    # still literally in range
    assert m.graded_score == pytest.approx(math.exp(-0.5 * (2.5 / 5.0) ** 2), abs=1e-6)  # ~0.882
    assert aggregate_metric("head_tilt", [0.0], [0.9], th).graded_score == pytest.approx(1.0, abs=1e-6)
    assert aggregate_metric("head_tilt", [5.0], [0.9], th).graded_score == pytest.approx(math.exp(-0.5), abs=1e-6)


def test_graded_score_directional_higher_is_better():
    # neck_forward_angle [150,180], higher_is_better: ideal = 180, sigma = band width 30.
    th = load_thresholds()
    assert aggregate_metric("neck_forward_angle", [180.0], [0.9], th).graded_score == pytest.approx(1.0, abs=1e-6)
    assert aggregate_metric("neck_forward_angle", [185.0], [0.9], th).graded_score == pytest.approx(1.0, abs=1e-6)
    assert aggregate_metric("neck_forward_angle", [150.0], [0.9], th).graded_score == pytest.approx(math.exp(-0.5), abs=1e-6)


def test_aggregate_basic_stats():
    th = load_thresholds()  # head_tilt acceptable [-5, 5]
    values = [0.0, 0.0, 0.0, 20.0, None]
    conf = [0.9, 0.9, 0.9, 0.9, 0.0]
    m = aggregate_metric("head_tilt", values, conf, th)
    assert m.n_total_frames == 5
    assert m.n_valid_frames == 4
    assert m.mean == 5.0
    assert m.pct_in_range == 0.75       # 3 of 4 within [-5, 5]
    assert m.max_deviation == 15.0      # 20 - 5
    assert m.reliability == "primary"
    assert m.confidence == 0.9


def test_aggregate_all_none():
    th = load_thresholds()
    m = aggregate_metric("pelvic_obliquity", [None, None], [0.0, 0.0], th)
    assert m.n_valid_frames == 0
    assert m.mean is None and m.pct_in_range is None
    assert m.reliability == "best_effort"
