import pytest

from equipose.angles_side import SIDE_METRICS, compute_side, facing_direction
from tests.conftest import lm, upright_side_landmarks


def _left_facing_side_landmarks(c: float = 0.9):
    """Mirror of upright_side_landmarks: knee/ankle/nose sit LEFT of the hip."""
    return [
        lm("nose", 85, 78, c),
        lm("right_ear", 110, 80, c),
        lm("right_shoulder", 100, 100, c),
        lm("right_hip", 100, 200, c),
        lm("right_knee", 60, 210, c),
        lm("right_ankle", 60, 260, c),
        lm("left_shoulder", 100, 100, 0.1),
        lm("left_hip", 100, 200, 0.1),
    ]


def test_facing_direction_right_when_knee_leads_right():
    # upright_side_landmarks is a right-facing pose (knee x=140 > hip x=100).
    assert facing_direction(upright_side_landmarks()) == "right"


def test_facing_direction_left_when_knee_leads_left():
    assert facing_direction(_left_facing_side_landmarks()) == "left"


def test_facing_direction_defaults_right_without_cues():
    # No usable anterior/posterior pair -> conventional default.
    assert facing_direction([lm("right_hip", 100, 200, 0.9)]) == "right"


def test_side_metrics_present_and_values():
    values, conf = compute_side(upright_side_landmarks())
    assert set(values) == set(SIDE_METRICS)
    assert values["forward_trunk_lean"] == pytest.approx(0.0, abs=1e-6)
    assert values["neck_forward_angle"] == pytest.approx(153.43, abs=1e-1)
    assert values["hip_flexion"] == pytest.approx(104.04, abs=1e-1)
    assert values["knee_angle"] == pytest.approx(104.04, abs=1e-1)


def test_lower_body_occluded_skipped(make_lm):
    lms = upright_side_landmarks()
    by = {l.name: l for l in lms}
    by["right_knee"] = make_lm("right_knee", 140, 210, 0.1)
    by["right_ankle"] = make_lm("right_ankle", 140, 260, 0.1)
    values, conf = compute_side(list(by.values()), vis_threshold=0.3)
    assert values["hip_flexion"] is None
    assert values["knee_angle"] is None
    # primary metrics survive
    assert values["forward_trunk_lean"] is not None
    assert values["neck_forward_angle"] is not None
