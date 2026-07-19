"""Tests for the digital-goniometer overlay (spec builder + both renderers)."""
import numpy as np

from equipose.dashboard import overlay
from equipose.schemas import Landmark, SessionMetric
from tests.conftest import upright_front_landmarks, upright_side_landmarks

ALL = {"skeleton", "reference", "arcs", "labels"}


def M(name, rel, mean, pct, unit="deg", conf=0.7):
    return SessionMetric(name=name, reliability=rel, unit=unit, mean=mean, max_deviation=0.0,
                         pct_in_range=pct, std=1.0, n_valid_frames=1, n_total_frames=1, confidence=conf)


def _side_metrics(knee=True):
    ms = [
        M("forward_trunk_lean", "primary", 9.0, 0.8),
        M("neck_forward_angle", "primary", 158.0, 0.7),
        M("hip_flexion", "best_effort", 150.0, 0.6),
    ]
    ms.append(M("knee_angle", "best_effort", 140.0, 0.6) if knee
              else M("knee_angle", "best_effort", None, None, conf=0.0))
    return ms


def _front_metrics():
    return [
        M("head_tilt", "primary", 3.0, 0.9),
        M("shoulder_tilt", "primary", 4.0, 0.8),
        M("pelvic_obliquity", "best_effort", 6.0, 0.5),
        M("trunk_lateral_lean", "primary", 5.0, 0.7),
        M("midline_deviation", "primary", 0.2, 0.6, unit="frac"),
        M("symmetry_score", "primary", 68.0, 0.5, unit="score"),  # composite, excluded
    ]


def test_side_spec_one_arc_per_detected_angle():
    spec = overlay.build_overlay_spec(upright_side_landmarks(), "side", _side_metrics(), ALL, 240, 300)
    assert len(spec.arcs) == 4                 # trunk lean, neck, hip, knee (composite excluded)
    assert len(spec.labels) == 4
    assert spec.bones and spec.refs


def test_occluded_metric_gets_no_arc():
    spec = overlay.build_overlay_spec(upright_side_landmarks(), "side", _side_metrics(knee=False), ALL, 240, 300)
    assert len(spec.arcs) == 3                 # knee dropped


def test_layer_toggles_filter_groups():
    lms, ms = upright_side_landmarks(), _side_metrics()
    no_arcs = overlay.build_overlay_spec(lms, "side", ms, {"skeleton", "reference", "labels"}, 240, 300)
    assert no_arcs.arcs == []
    no_ref = overlay.build_overlay_spec(lms, "side", ms, {"skeleton", "arcs", "labels"}, 240, 300)
    assert no_ref.refs == []
    no_skel = overlay.build_overlay_spec(lms, "side", ms, {"reference", "arcs", "labels"}, 240, 300)
    assert no_skel.bones == []


def test_front_tilts_and_midline_connector():
    spec = overlay.build_overlay_spec(upright_front_landmarks(), "front", _front_metrics(), ALL, 240, 300)
    assert len(spec.arcs) == 4                 # head/shoulder/pelvic tilt + trunk lean
    # midline deviation is a connector + ratio label, not an arc
    assert any(lb.text.endswith("w") for lb in spec.labels)
    assert any("°" in lb.text for lb in spec.labels)


def test_overlay_svg_embeds_image_and_arcs():
    spec = overlay.build_overlay_spec(upright_side_landmarks(), "side", _side_metrics(), ALL, 240, 300)
    s = overlay.overlay_svg(spec, 240, 300, "data:image/png;base64,AAAA")
    assert "<svg" in s and "viewBox=\"0 0 240 300\"" in s
    assert "data:image/png;base64,AAAA" in s
    assert "°" in s and "<path" in s


def test_overlay_side_matches_metrics_side():
    """Regression: the overlay must pick the same camera-facing side as the
    metrics (pick_side over ALL landmarks), even when confidence-filtering would
    flip it. Otherwise arcs land on the wrong side and vanish."""
    from equipose.angles_side import pick_side

    def L(n, x, y, c):
        return Landmark(name=n, x_px=x, y_px=y, confidence=c)

    # left has high trunk conf but occluded (low) knee/ankle; right is uniformly
    # moderate. Unfiltered mean -> right; confidence-filtered mean -> left (the bug).
    lms = [
        L("left_shoulder", 100, 100, 0.9), L("left_hip", 100, 200, 0.9), L("left_ear", 95, 70, 0.9),
        L("left_knee", 100, 260, 0.1), L("left_ankle", 100, 320, 0.1),
        L("right_shoulder", 140, 100, 0.7), L("right_hip", 140, 200, 0.7), L("right_ear", 135, 70, 0.7),
        L("right_knee", 140, 260, 0.7), L("right_ankle", 140, 320, 0.7),
    ]
    assert pick_side({l.name: l for l in lms}) == "right"  # metrics' side
    neck = SessionMetric(name="neck_forward_angle", reliability="primary", unit="deg", mean=160.0,
                         max_deviation=0.0, pct_in_range=1.0, std=0.0, n_valid_frames=1,
                         n_total_frames=1, confidence=0.7)
    spec = overlay.build_overlay_spec(lms, "side", [neck], {"arcs"}, 240, 300)
    assert len(spec.arcs) == 1
    # neck arc vertex is the shoulder of the metrics' side (right @ x=140), not left
    assert round(spec.arcs[0].cx) == 140


def test_low_confidence_markers_are_ghosted_not_dropped():
    from equipose.angles_side import pick_side

    def L(n, x, y, c):
        return Landmark(name=n, x_px=x, y_px=y, confidence=c)

    lms = [
        L("right_ear", 95, 70, 0.9), L("right_shoulder", 100, 100, 0.9),
        L("right_hip", 100, 200, 0.9), L("right_knee", 130, 250, 0.15),  # ghost (boot)
        L("right_ankle", 130, 300, 0.15),                                  # ghost
    ]
    assert pick_side({l.name: l for l in lms}) == "right"
    spec = overlay.build_overlay_spec(lms, "side", [], {"skeleton"}, 240, 300)
    colors = {round(j.p[0]): j.color for j in spec.joints}
    from equipose.dashboard import glyphs
    assert colors[130] == glyphs.GHOST   # low-conf knee/ankle shown, ghosted
    assert colors[100] == overlay.SEG    # confident shoulder/hip solid


def test_overlay_raster_returns_same_shape():
    spec = overlay.build_overlay_spec(upright_side_landmarks(), "side", _side_metrics(), ALL, 240, 300)
    img = np.zeros((300, 240, 3), dtype=np.uint8)
    out = overlay.overlay_raster(img, spec)
    assert out.shape == (300, 240, 3)


def _side_metrics_with_back(val=0.19, pct=0.0):
    ms = _side_metrics()
    ms.append(M("back_roundness", "primary", val, pct, unit="frac"))
    return ms


def _bow_depth(c):
    import math
    mx, my = (c.p1[0] + c.p2[0]) / 2, (c.p1[1] + c.p2[1]) / 2
    return math.hypot(c.c[0] - mx, c.c[1] - my)


def test_back_roundness_draws_bow_with_depth_scaled_to_value():
    deep = overlay.build_overlay_spec(upright_side_landmarks(), "side",
                                      _side_metrics_with_back(0.19), ALL, 240, 300)
    assert len(deep.curves) == 1
    assert any(lb.text == "back rounding" for lb in deep.labels)
    # a rounder back bows deeper off the chord than a nearly straight one
    shallow = overlay.build_overlay_spec(upright_side_landmarks(), "side",
                                         _side_metrics_with_back(0.03), ALL, 240, 300)
    assert _bow_depth(deep.curves[0]) > _bow_depth(shallow.curves[0])


def test_back_roundness_bow_is_in_arcs_layer_and_side_only():
    lms = upright_side_landmarks()
    off = overlay.build_overlay_spec(lms, "side", _side_metrics_with_back(), {"skeleton"}, 240, 300)
    assert off.curves == []                       # bow rides the 'arcs' layer toggle
    front = overlay.build_overlay_spec(upright_front_landmarks(), "front",
                                       _front_metrics(), ALL, 240, 300)
    assert front.curves == []                     # never drawn on the front view


def test_back_roundness_absent_when_not_measured():
    spec = overlay.build_overlay_spec(upright_side_landmarks(), "side", _side_metrics(), ALL, 240, 300)
    assert spec.curves == []                      # no back_roundness metric -> no bow
