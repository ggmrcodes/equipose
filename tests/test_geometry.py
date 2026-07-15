import math

import pytest

from equipose import geometry as geo


def test_joint_angle_right_angle():
    assert geo.joint_angle_deg((1, 0), (0, 0), (0, 1)) == pytest.approx(90.0)


def test_joint_angle_straight():
    assert geo.joint_angle_deg((1, 0), (0, 0), (-1, 0)) == pytest.approx(180.0)


def test_joint_angle_degenerate_returns_straight():
    assert geo.joint_angle_deg((0, 0), (0, 0), (1, 1)) == pytest.approx(180.0)


def test_perpendicular_distance():
    assert geo.perpendicular_distance((0, 1), (0, 0), (1, 0)) == pytest.approx(1.0)
    assert geo.perpendicular_distance((5, 0), (0, 0), (10, 0)) == pytest.approx(0.0)


def test_signed_perpendicular_distance():
    A, B = (100, 50), (100, 200)          # vertical line, directed downward
    # opposite sides of the line -> opposite signs, magnitude = the offset
    assert geo.signed_perpendicular_distance((120, 100), A, B) == pytest.approx(20.0)
    assert geo.signed_perpendicular_distance((80, 100), A, B) == pytest.approx(-20.0)
    assert geo.signed_perpendicular_distance((100, 130), A, B) == pytest.approx(0.0)  # on the line
    # magnitude agrees with the unsigned helper
    assert abs(geo.signed_perpendicular_distance((120, 100), A, B)) == pytest.approx(
        geo.perpendicular_distance((120, 100), A, B))


def test_line_angle_from_horizontal():
    assert geo.line_angle_from_horizontal_deg((0, 0), (1, 0)) == pytest.approx(0.0)
    assert geo.line_angle_from_horizontal_deg((0, 0), (1, 1)) == pytest.approx(45.0)
    # ordering independent: a level line reads ~0 regardless of direction
    assert geo.line_angle_from_horizontal_deg((1, 0), (0, 0)) == pytest.approx(0.0)


def test_line_angle_from_vertical():
    assert geo.line_angle_from_vertical_deg((0, 0), (0, 1)) == pytest.approx(0.0)
    assert geo.line_angle_from_vertical_deg((0, 0), (1, 1)) == pytest.approx(45.0)
    # a horizontal line is 90 deg from vertical
    assert geo.line_angle_from_vertical_deg((0, 0), (1, 0)) == pytest.approx(90.0)


def test_midpoint_and_euclidean():
    assert geo.midpoint((0, 0), (10, 20)) == (5.0, 10.0)
    assert geo.euclidean((0, 0), (3, 4)) == pytest.approx(5.0)


def test_by_name_confidence_gate(make_lm):
    lms = [make_lm("nose", 1, 1, 0.9), make_lm("left_hip", 2, 2, 0.2)]
    by = geo.by_name(lms, conf_min=0.5)
    assert "nose" in by and "left_hip" not in by
