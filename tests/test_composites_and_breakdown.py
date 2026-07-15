"""Reworked composites (unit-consistent, bounded) + score breakdown."""
import pytest

from equipose.angles_front import _symmetry_score
from equipose.config import load_scoring
from equipose.scoring import score_breakdown, overall_from_breakdown, score_session
from equipose.schemas import SessionMetric


# ---- composites -----------------------------------------------------------
def test_symmetry_perfect_is_100():
    assert _symmetry_score({"head_tilt": 0.0, "shoulder_tilt": 0.0, "midline_deviation": 0.0}) == 100.0


def test_symmetry_bounded_and_no_component_dominates():
    # a large midline alone cannot crater the score past its 1/3 share
    s = _symmetry_score({"head_tilt": 0.0, "shoulder_tilt": 0.0, "midline_deviation": 5.0})
    assert s == pytest.approx(100.0 * (1 - 1 / 3), abs=1e-6)  # one of three maxed out
    assert 0.0 <= s <= 100.0


def test_symmetry_averages_available_components():
    # only one component present -> based on it alone, still bounded
    s = _symmetry_score({"head_tilt": 7.5})  # 7.5/15 = 0.5 penalty
    assert s == pytest.approx(50.0)


# ---- breakdown ------------------------------------------------------------
def _m(name, rel, pct, conf=0.9, n=10):
    return SessionMetric(name=name, reliability=rel, unit="deg", mean=0.0, max_deviation=0.0,
                         pct_in_range=pct, std=0.0, n_valid_frames=n, n_total_frames=10, confidence=conf)


def test_breakdown_matches_score_session():
    sc = load_scoring()
    metrics = [
        _m("head_tilt", "primary", 1.0),
        _m("shoulder_tilt", "primary", 0.0),
        _m("pelvic_obliquity", "best_effort", 1.0, conf=0.1),  # excluded: low conf
    ]
    entries = score_breakdown(metrics, sc)
    overall = overall_from_breakdown(entries)
    score, _ = score_session(metrics, sc)
    assert overall == pytest.approx(score)
    by = {e.name: e for e in entries}
    assert by["pelvic_obliquity"].counted is False and by["pelvic_obliquity"].reason == "low confidence"
    assert by["head_tilt"].counted and by["head_tilt"].sub_score == 100.0
    assert by["shoulder_tilt"].sub_score == 0.0


def test_symmetry_is_display_only_not_scored():
    sc = load_scoring()
    assert "symmetry_score" in sc.display_only
    assert "sitting_alignment_index" not in sc.display_only  # metric removed entirely
    # front: individual angles all in range; the composite would be 0 at weight 2.0
    metrics = [
        _m("head_tilt", "primary", 1.0),
        _m("shoulder_tilt", "primary", 1.0),
        _m("midline_deviation", "primary", 1.0),
        _m("symmetry_score", "primary", 0.0),  # display-only: must not drag
    ]
    entries = score_breakdown(metrics, sc)
    by = {e.name: e for e in entries}
    assert by["symmetry_score"].counted is False
    assert by["symmetry_score"].reason == "summary (not scored)"
    score, band = score_session(metrics, sc)
    assert score == 100.0 and band == "green"  # composite does not drag it


def test_breakdown_html_shows_reason_and_overall():
    from equipose.dashboard import ui

    sc = load_scoring()
    entries = score_breakdown([_m("hip_flexion", "best_effort", 1.0, conf=0.1)], sc)
    html = ui.score_breakdown_html(entries, overall_from_breakdown(entries))
    assert "low confidence" in html and "Overall" in html
