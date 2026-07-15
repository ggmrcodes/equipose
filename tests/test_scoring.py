import pytest

from equipose.config import load_scoring
from equipose.schemas import SessionMetric
from equipose.scoring import score_session


def _metric(name, reliability, pct, conf=0.9, n=10):
    return SessionMetric(name=name, reliability=reliability, unit="deg",
                         mean=0.0, max_deviation=0.0, pct_in_range=pct, std=0.0,
                         n_valid_frames=n, n_total_frames=10, confidence=conf)


def test_scoring_prefers_graded_score_when_present():
    sc = load_scoring()
    # in range (pct=1.0) but graded 0.88 -> sub-score 88, not a flat 100
    m = SessionMetric(name="head_tilt", reliability="primary", unit="deg", mean=2.5,
                      max_deviation=0.0, pct_in_range=1.0, graded_score=0.88, std=0.0,
                      n_valid_frames=10, n_total_frames=10, confidence=0.9)
    score, _ = score_session([m], sc)
    assert score == pytest.approx(88.0, abs=1e-6)


def test_scoring_falls_back_to_pct_when_graded_absent():
    sc = load_scoring()  # metrics with no graded_score keep the binary path (backward compatible)
    score, _ = score_session([_metric("head_tilt", "primary", 1.0)], sc)
    assert score == 100.0


def test_metric_band_grades_like_the_overall_score():
    from equipose.scoring import metric_band
    sc = load_scoring()

    def m(graded=None, pct=1.0):
        return SessionMetric(name="knee_angle", reliability="best_effort", unit="deg",
                             mean=0.0, pct_in_range=pct, graded_score=graded,
                             n_valid_frames=10, n_total_frames=10, confidence=0.9)

    assert metric_band(m(graded=0.92), sc) == "green"    # comfortably good
    assert metric_band(m(graded=0.64), sc) == "yellow"   # in band but near edge -> Watch
    assert metric_band(m(graded=0.40), sc) == "red"      # poor
    assert metric_band(m(graded=None, pct=1.0), sc) == "green"   # fallback to binary in-range
    not_detected = SessionMetric(name="knee_angle", reliability="best_effort", unit="deg",
                                 n_valid_frames=0, n_total_frames=1)
    assert metric_band(not_detected, sc) == "none"


def test_overall_blends_weighted_mean_with_worst_joint():
    # weakest-link: overall = halfway between the weighted mean and the single
    # worst joint, so one bad joint pulls the total down instead of being averaged away.
    sc = load_scoring()
    good = _metric("head_tilt", "primary", 1.0)       # sub 100, weight 1.0
    poor = _metric("shoulder_tilt", "primary", 0.4)   # sub 40,  weight 1.0
    score, _ = score_session([good, poor], sc)
    # weighted mean = 70, worst = 40, blend 0.5/0.5 -> 55
    assert score == pytest.approx(55.0, abs=1e-6)
    # a single metric is its own worst joint: blend == that sub-score
    assert score_session([poor], sc)[0] == pytest.approx(40.0, abs=1e-6)


def test_all_in_range_is_green():
    sc = load_scoring()
    score, band = score_session([_metric("head_tilt", "primary", 1.0)], sc)
    assert score == 100.0 and band == "green"


def test_all_out_of_range_is_red():
    sc = load_scoring()
    score, band = score_session([_metric("head_tilt", "primary", 0.0)], sc)
    assert score == 0.0 and band == "red"


def test_low_confidence_best_effort_excluded():
    sc = load_scoring()
    metrics = [
        _metric("head_tilt", "primary", 1.0),
        _metric("pelvic_obliquity", "best_effort", 0.0, conf=0.1),  # excluded: low conf
    ]
    score, band = score_session(metrics, sc)
    assert score == 100.0 and band == "green"


def test_low_coverage_excluded():
    sc = load_scoring()
    metrics = [
        _metric("head_tilt", "primary", 1.0),
        _metric("shoulder_tilt", "primary", 0.0, n=1),  # coverage 0.1 < 0.3 -> excluded
    ]
    score, band = score_session(metrics, sc)
    assert score == 100.0
