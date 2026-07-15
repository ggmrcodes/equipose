"""Unit tests for the signature SVG builders (pure string output)."""
from equipose.dashboard import glyphs


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
    # Glyph text must stay upright (no group flip that would reverse the labels).
    assert "scale(-1" not in left
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
    assert glyphs.GHOST in s and glyphs.GOOD not in s
