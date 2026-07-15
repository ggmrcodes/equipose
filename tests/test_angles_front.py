import pytest

from equipose.angles_front import FRONT_METRICS, compute_front
from tests.conftest import upright_front_landmarks


def test_upright_pose_all_level():
    values, conf = compute_front(upright_front_landmarks())
    assert set(values) == set(FRONT_METRICS)
    assert values["head_tilt"] == pytest.approx(0.0, abs=1e-6)
    assert values["shoulder_tilt"] == pytest.approx(0.0, abs=1e-6)
    assert values["trunk_lateral_lean"] == pytest.approx(0.0, abs=1e-6)
    assert values["pelvic_obliquity"] == pytest.approx(0.0, abs=1e-6)
    assert values["midline_deviation"] == pytest.approx(0.0, abs=1e-6)
    assert values["symmetry_score"] == pytest.approx(100.0, abs=1e-6)


def test_head_tilt_value(make_lm):
    lms = upright_front_landmarks()
    by = {l.name: l for l in lms}
    by["right_ear"] = make_lm("right_ear", 110, 50)  # 10 down over 20 across -> 26.57 deg
    values, _ = compute_front(list(by.values()))
    assert values["head_tilt"] == pytest.approx(26.565, abs=1e-2)


def test_pelvis_occluded_is_best_effort_none(make_lm):
    lms = upright_front_landmarks()
    by = {l.name: l for l in lms}
    by["left_hip"] = make_lm("left_hip", 85, 200, 0.1)
    by["right_hip"] = make_lm("right_hip", 115, 200, 0.1)
    values, conf = compute_front(list(by.values()), vis_threshold=0.3)
    assert values["pelvic_obliquity"] is None
    assert conf["pelvic_obliquity"] == 0.0
    # trunk lean falls back to nose->shoulders (still computed, lower conf)
    assert values["trunk_lateral_lean"] is not None
    assert conf["trunk_lateral_lean"] < conf["shoulder_tilt"]
