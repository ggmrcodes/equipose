"""Normal-range context: config formatter, basis notes, and table column."""
from equipose.config import load_thresholds
from equipose.dashboard import ui
from equipose.schemas import SessionMetric


def test_format_range_variants():
    th = load_thresholds()
    assert th.format_range("head_tilt") == "±5°"            # symmetric
    assert th.format_range("midline_deviation") == "≤ 0.10 w"  # lower-better, min 0
    assert th.format_range("symmetry_score") == "≥ 80"      # higher-better
    assert th.format_range("forward_trunk_lean") == "−10° to 15°"  # asymmetric, real minus
    assert th.format_range("neck_forward_angle") == "≥ 150°"  # higher-better (180 = ideal)


def test_every_metric_has_a_basis():
    th = load_thresholds()
    for name in th.names():
        assert th.basis(name), f"{name} is missing a basis note"
    # principled vs placeholder split is explicit
    assert th.basis("shoulder_tilt").startswith("Principled")
    assert th.basis("hip_flexion").startswith("PLACEHOLDER")


def test_table_shows_normal_range_only_when_thresholds_given():
    th = load_thresholds()
    m = SessionMetric(name="head_tilt", reliability="primary", unit="deg", mean=2.0,
                      max_deviation=0.0, pct_in_range=0.9, std=1.0, n_valid_frames=9,
                      n_total_frames=10, confidence=0.85)
    with_ref = ui.metrics_table_html([m], th)
    assert "±5°" in with_ref            # range shown in the row's sub-line
    without = ui.metrics_table_html([m])
    assert "±5°" not in without         # range omitted when no thresholds given


def test_metrics_table_shows_graded_watch_not_binary_in_range():
    from equipose.config import load_scoring
    # knee 128.79 is INSIDE [80,130] (binary "in range") but grades ~0.64 -> Watch
    m = SessionMetric(name="knee_angle", reliability="best_effort", unit="deg", mean=128.79,
                      max_deviation=0.0, pct_in_range=1.0, graded_score=0.64, std=0.0,
                      n_valid_frames=1, n_total_frames=1, confidence=0.8)
    html = ui.metrics_table_html([m], load_thresholds(), scoring=load_scoring())
    assert "Watch" in html and "◐" in html      # graded status, consistent with the score
    assert "In range" not in html                # not the misleading binary label


def test_placeholder_metric_gets_needs_lit_tag():
    th = load_thresholds()
    m = SessionMetric(name="hip_flexion", reliability="best_effort", unit="deg", mean=95.0,
                      max_deviation=0.0, pct_in_range=0.6, std=1.0, n_valid_frames=8,
                      n_total_frames=10, confidence=0.5)
    html = ui.metrics_table_html([m], th)
    assert "needs-lit" in html and "110° to 160°" in html  # riding-specific band
