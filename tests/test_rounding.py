"""Back-roundness measure: pure contour-curvature over synthetic masks (no model)."""
import numpy as np

from equipose import rounding
from equipose.rounding import back_roundness_from_mask
from equipose.schemas import Landmark


class _FakeBackend:
    def __init__(self, lms):
        self._lms = lms

    def detect(self, image_bgr):
        return list(self._lms)


def _side_lms(faces_right=True):
    # shoulder/hip y span the synthetic mask torso (rows 30-210) so the walk covers the bulge
    kx = 140 if faces_right else 60
    return [Landmark(name="right_ear", x_px=100, y_px=15, confidence=0.9),
            Landmark(name="right_shoulder", x_px=100, y_px=40, confidence=0.9),
            Landmark(name="right_hip", x_px=100, y_px=200, confidence=0.9),
            Landmark(name="right_knee", x_px=kx, y_px=225, confidence=0.9),
            Landmark(name="right_ankle", x_px=kx, y_px=239, confidence=0.9)]


def _straight_mask(w=140, h=240):
    m = np.zeros((h, w), np.uint8)
    m[30:210, 50:90] = 1                       # a vertical rectangle torso
    return m


def _rounded_mask(w=140, h=240, bulge=26, side="right"):
    m = np.zeros((h, w), np.uint8)
    for y in range(30, 210):
        t = (y - 30) / 180.0
        b = int(bulge * np.sin(np.pi * t))     # max bulge at mid-back
        if side == "right":
            m[y, 50:90 + b] = 1                # posterior (right) edge bows out
        else:
            m[y, 50 - b:90] = 1                # posterior (left) edge bows out
    return m


def test_straight_back_scores_near_zero():
    idx = back_roundness_from_mask(_straight_mask(), (70, 30), (70, 210), "left")
    assert idx is not None and idx < 0.02


def test_rounded_back_scores_high_facing_left():
    # facing left -> posterior is the right edge; a right-edge bulge is rounding
    idx = back_roundness_from_mask(_rounded_mask(side="right"), (70, 30), (70, 210), "left")
    assert idx is not None and idx > 0.10


def test_rounded_back_scores_high_facing_right_mirror():
    idx = back_roundness_from_mask(_rounded_mask(side="left"), (70, 30), (70, 210), "right")
    assert idx is not None and idx > 0.10


def test_rounded_scores_above_straight():
    straight = back_roundness_from_mask(_straight_mask(), (70, 30), (70, 210), "left")
    rounded = back_roundness_from_mask(_rounded_mask(side="right"), (70, 30), (70, 210), "left")
    assert rounded > straight + 0.08


def test_too_few_contour_points_returns_none():
    assert back_roundness_from_mask(np.zeros((240, 140), np.uint8), (70, 30), (70, 210), "left") is None


# ---- orchestrator (model seam mocked) ----
def test_index_segments_then_measures(monkeypatch):
    # faces right -> posterior is the LEFT edge; a left-edge bulge is rounding
    monkeypatch.setattr(rounding, "_segment_person", lambda crop: _rounded_mask(side="left"))
    idx = rounding.back_roundness_index(np.zeros((240, 140, 3), np.uint8), _side_lms(faces_right=True))
    assert idx is not None and idx > 0.10


def test_index_none_without_shoulder_hip(monkeypatch):
    monkeypatch.setattr(rounding, "_segment_person", lambda crop: _straight_mask())
    only_ear = [Landmark(name="right_ear", x_px=100, y_px=60, confidence=0.9)]
    assert rounding.back_roundness_index(np.zeros((240, 140, 3), np.uint8), only_ear) is None


def test_index_none_on_segmentation_failure(monkeypatch):
    def boom(crop):
        raise RuntimeError("seg failed")
    monkeypatch.setattr(rounding, "_segment_person", boom)
    assert rounding.back_roundness_index(np.zeros((240, 140, 3), np.uint8), _side_lms()) is None


def test_pipeline_side_photo_includes_back_roundness(monkeypatch):
    # side photo -> back_roundness is computed and joins the metrics
    from equipose.pipeline import analyze_image
    monkeypatch.setattr(rounding, "_segment_person", lambda crop: _rounded_mask(side="left"))
    report, _ = analyze_image(np.zeros((300, 240, 3), np.uint8), "side", (0, 0, 240, 300),
                              backend=_FakeBackend(_side_lms(faces_right=True)))
    br = next((m for m in report.metrics if m.name == "back_roundness"), None)
    assert br is not None and br.mean is not None and br.mean > 0.10


def test_pipeline_front_photo_has_no_back_roundness(monkeypatch):
    from equipose.pipeline import analyze_image
    monkeypatch.setattr(rounding, "_segment_person", lambda crop: _rounded_mask(side="left"))
    report, _ = analyze_image(np.zeros((300, 240, 3), np.uint8), "front", (0, 0, 240, 300),
                              backend=_FakeBackend(_side_lms()))
    assert not any(m.name == "back_roundness" for m in report.metrics)
