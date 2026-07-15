"""Full pipeline driven by a fake backend + synthetic frames (no model/codec)."""
import numpy as np

from equipose.angles_front import FRONT_METRICS
from equipose.config import load_scoring, load_thresholds
from equipose.pipeline import analyze_session
from tests.conftest import upright_front_landmarks


class _FakeBackend:
    def __init__(self, landmarks):
        self._lms = landmarks

    def detect(self, image_bgr):
        return list(self._lms)


def _frames(n=8):
    return [(i, i / 30.0, np.zeros((480, 640, 3), dtype=np.uint8)) for i in range(n)]


def test_upright_session_scores_green():
    report = analyze_session(
        "synthetic.mp4", "front", "P1", (100, 100, 300, 400),
        session_id="s1", captured_at="2026-01-01T10:00:00",
        backend=_FakeBackend(upright_front_landmarks()),
        thresholds=load_thresholds(), scoring=load_scoring(),
        frames=_frames(8),
    )
    assert {m.name for m in report.metrics} == set(FRONT_METRICS)
    by = {m.name: m for m in report.metrics}
    assert by["head_tilt"].mean == 0.0
    assert by["symmetry_score"].mean == 100.0
    assert by["head_tilt"].pct_in_range == 1.0
    assert 0.0 <= report.overall_score <= 100.0
    assert report.band == "green"
    assert report.fps == 30.0


def test_occluded_pelvis_yields_no_valid_frames():
    lms = upright_front_landmarks()
    by = {l.name: l for l in lms}
    by["left_hip"].confidence = 0.1  # type: ignore[attr-defined]
    # rebuild with low-confidence hips
    from equipose.schemas import Landmark
    lms2 = [Landmark(name=l.name, x_px=l.x_px, y_px=l.y_px,
                     confidence=(0.1 if "hip" in l.name else l.confidence)) for l in lms]
    report = analyze_session(
        "synthetic.mp4", "front", "P1", (100, 100, 300, 400),
        session_id="s2", captured_at="2026-01-01T10:00:00",
        backend=_FakeBackend(lms2), thresholds=load_thresholds(), scoring=load_scoring(),
        frames=_frames(6),
    )
    pelvic = next(m for m in report.metrics if m.name == "pelvic_obliquity")
    assert pelvic.n_valid_frames == 0
    # primary metrics still drive a green score
    assert report.band == "green"
