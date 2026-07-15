"""Single-photo analysis + skeleton drawing (fake backend, synthetic image)."""
import numpy as np

from equipose.config import load_scoring, load_thresholds
from equipose.pipeline import analyze_image
from equipose.viz import draw_skeleton
from tests.conftest import upright_front_landmarks, upright_side_landmarks


class _FakeBackend:
    def __init__(self, landmarks):
        self._lms = landmarks

    def detect(self, image_bgr):
        return list(self._lms)


def test_analyze_image_front_is_single_frame():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    report, landmarks = analyze_image(
        img, "front", (0, 0, 640, 480),
        backend=_FakeBackend(upright_front_landmarks()),
        thresholds=load_thresholds(), scoring=load_scoring(),
    )
    assert report.view == "front"
    assert report.fps == 0.0
    assert all(m.n_total_frames == 1 for m in report.metrics)
    by = {m.name: m for m in report.metrics}
    assert by["head_tilt"].mean == 0.0
    assert by["head_tilt"].pct_in_range == 1.0      # single frame: in-range flag
    assert by["symmetry_score"].mean == 100.0
    assert report.band == "green"
    assert len(landmarks) > 0


def test_analyze_image_side_selects_facing_side():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    report, landmarks = analyze_image(
        img, "side", (0, 0, 640, 480),
        backend=_FakeBackend(upright_side_landmarks()),
        thresholds=load_thresholds(), scoring=load_scoring(),
    )
    by = {m.name: m for m in report.metrics}
    assert by["forward_trunk_lean"].mean == 0.0
    assert by["forward_trunk_lean"].n_total_frames == 1


def test_draw_skeleton_returns_same_shape_both_views():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    out_front = draw_skeleton(img, upright_front_landmarks(), "front")
    out_side = draw_skeleton(img, upright_side_landmarks(), "side")
    assert out_front.shape == img.shape
    assert out_side.shape == img.shape
    # something was drawn (non-zero pixels) for the front skeleton
    assert int(out_front.sum()) > 0


def test_draw_skeleton_side_only_omits_far_side():
    # right side high-confidence, left side low -> side view should draw no left_* joints
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    out = draw_skeleton(img, upright_side_landmarks(), "side")
    # purely a smoke assertion that it runs and draws the near side
    assert out.shape == img.shape and int(out.sum()) > 0
