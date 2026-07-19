"""Unit tests for the signature SVG builders (pure string output)."""
import re

from equipose.dashboard import glyphs


def _mk_cx(svg):
    return float(re.search(r'class="mk"[^>]*cx="([0-9.]+)"', svg).group(1))


def test_inband_track_marker_position_and_color():
    good = glyphs.inband_track_svg(0.0, -5, 5, 0.0, "good")
    assert good.startswith("<svg") and glyphs.GOOD in good
    # marker x grows with the value; out-of-band clamps to the end
    lo = glyphs.inband_track_svg(-5, -5, 5, 0.0, "good")
    hi = glyphs.inband_track_svg(5, -5, 5, 0.0, "good")
    assert _mk_cx(lo) < _mk_cx(hi)
    assert _mk_cx(glyphs.inband_track_svg(20, -5, 5, 0.0, "concern")) == _mk_cx(hi)
    # status carries through to the marker color
    assert glyphs.CONCERN in glyphs.inband_track_svg(20, -5, 5, 0.0, "concern")
    assert glyphs.AMBER in glyphs.inband_track_svg(4.6, -5, 5, 0.0, "watch")


def test_logo_mark_is_svg():
    s = glyphs.logo_mark_svg()
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>")
    assert glyphs.ACCENT in s  # the angle stroke uses the accent


def test_score_dial_renders_number_and_band_color():
    s = glyphs.score_dial_svg(56, "red")
    assert "<svg" in s and ">56<" in s
    assert glyphs.CONCERN in s            # value arc colored by band (status)
    assert "/ 100" in s
    assert 'stroke-width="5"' in s        # thinner, Apple-precise arc
    z = glyphs.score_dial_svg(0, "red")
    assert ">0<" in z


def test_posture_chart_side_colors_by_status_and_ghosts_missing():
    data = {
        "forward_trunk_lean": ("good", 8.0),
        "neck_forward_angle": ("concern", 150.0),
        # hip_flexion / knee_angle omitted -> should ghost
    }
    s = glyphs.posture_chart_svg("side", data)
    assert s.startswith("<svg") and "viewBox" in s
    assert glyphs.GOOD in s and glyphs.CONCERN in s   # detected joints colored
    assert glyphs.GHOST in s                          # missing joints ghosted
    assert "8°" in s and "150°" in s                  # angle labels in Plex Mono


def test_posture_chart_side_mirrors_to_face_left():
    data = {
        "forward_trunk_lean": ("good", 8.0),
        "neck_forward_angle": ("good", 165.0),
        "hip_flexion": ("good", 130.0),
        "knee_angle": ("good", 110.0),
    }
    right = glyphs.posture_chart_svg("side", data)                    # default: faces right
    left = glyphs.posture_chart_svg("side", data, face_left=True)
    assert right != left
    # Base foot tip is at x=172 (right of centre); mirrored about x=120 -> x=68.
    assert 'x2="172.0"' in right and 'x2="172.0"' not in left
    assert 'x2="68.0"' in left
    # The rider mirrors via reflected points, not a group flip, so labels stay upright.
    # Only the context horse silhouette may carry a mirror transform (it has no text).
    assert left.count("scale(-1") <= 1
    assert "8°" in left and "165°" in left


def test_posture_chart_side_colors_watch_amber():
    # a "watch" joint must render in amber (the graded near-edge state), not ghost
    s = glyphs.posture_chart_svg("side", {"forward_trunk_lean": ("watch", 12.0)})
    assert glyphs.AMBER in s


def test_posture_chart_front_has_plumb_and_labels():
    data = {
        "shoulder_tilt": ("good", 3.0),
        "pelvic_obliquity": ("concern", 12.0),
        "trunk_lateral_lean": ("good", 4.0),
        "head_tilt": ("good", 2.0),
        "midline_deviation": ("concern", 0.3),
    }
    s = glyphs.posture_chart_svg("front", data)
    assert "stroke-dasharray" in s   # plumb reference line
    assert "3°" in s and "12°" in s


def test_chart_handles_all_missing_gracefully():
    s = glyphs.posture_chart_svg("side", {})
    assert s.startswith("<svg")
    assert glyphs.GHOST in s          # ghosted figure + "Not detected" legend swatch
    assert "you " not in s            # no per-joint callouts when nothing is detected


def test_side_chart_renders_you_ideal_callouts_and_legend():
    from equipose.config import load_thresholds
    th = load_thresholds()
    data = {"forward_trunk_lean": ("good", 8.0), "neck_forward_angle": ("watch", 165.0)}
    s = glyphs.posture_chart_svg("side", data, thresholds=th)
    assert "Trunk lean" in s and "Neck" in s          # short joint names on callouts
    assert "you 8°" in s and "ideal 2°" in s           # value + ideal (trunk centre 2.5 -> 2)
    assert "you 165°" in s and "ideal 180°" in s       # neck higher-is-better ideal
    assert "Good" in s and "Watch" in s and "Not detected" in s   # compact legend
