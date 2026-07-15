"""MediaPipe backend tests with mocked inference — no model file needed."""
import numpy as np

from equipose.pose_backend.mediapipe_backend import MediaPipePoseBackend


class _FakeLM:
    def __init__(self, x, y, visibility):
        self.x = x
        self.y = y
        self.visibility = visibility


class _FakeResult:
    def __init__(self, landmarks):
        self.pose_landmarks = landmarks


def _make_33(overrides):
    lms = [_FakeLM(0.0, 0.0, 0.0) for _ in range(33)]
    for idx, (x, y, v) in overrides.items():
        lms[idx] = _FakeLM(x, y, v)
    return lms


def test_detect_maps_and_scales(monkeypatch):
    backend = MediaPipePoseBackend()
    # nose idx 0; left_shoulder idx 11
    fake = _FakeResult(_make_33({0: (0.5, 0.5, 0.9), 11: (0.4, 0.6, 0.8)}))
    monkeypatch.setattr(backend, "_raw_process", lambda img: fake)

    out = backend.detect(np.zeros((100, 200, 3), dtype=np.uint8))  # h=100, w=200
    by = {lm.name: lm for lm in out}
    assert by["nose"].x_px == 100.0 and by["nose"].y_px == 50.0
    assert by["nose"].confidence == 0.9
    assert by["left_shoulder"].x_px == 80.0 and by["left_shoulder"].y_px == 60.0
    assert by["left_shoulder"].confidence == 0.8


def test_detect_empty_result(monkeypatch):
    backend = MediaPipePoseBackend()
    monkeypatch.setattr(backend, "_raw_process", lambda img: _FakeResult([]))
    assert backend.detect(np.zeros((10, 10, 3), dtype=np.uint8)) == []


def test_visibility_none_becomes_zero_conf(monkeypatch):
    backend = MediaPipePoseBackend()
    fake = _FakeResult(_make_33({0: (0.5, 0.5, None)}))
    monkeypatch.setattr(backend, "_raw_process", lambda img: fake)
    out = {lm.name: lm for lm in backend.detect(np.zeros((10, 10, 3), dtype=np.uint8))}
    assert out["nose"].confidence == 0.0
