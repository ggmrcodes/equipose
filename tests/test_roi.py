import numpy as np

from equipose.roi import RoiTracker
from equipose.schemas import Landmark


def test_crop_and_map_back_roundtrip():
    frame = np.zeros((400, 400, 3), dtype=np.uint8)
    tracker = RoiTracker((100, 100, 300, 300), pad=0.0)
    square, transform = tracker.crop(frame)
    assert square.shape[0] == square.shape[1] == 200
    # a landmark at square coord (50,50) maps back to full (150,150)
    mapped = RoiTracker.map_back([Landmark(name="nose", x_px=50, y_px=50, confidence=1.0)], transform)
    assert (mapped[0].x_px, mapped[0].y_px) == (150.0, 150.0)


def test_update_recenters_on_centroid():
    tracker = RoiTracker((100, 100, 200, 200), smooth=0.5)
    centroid_lms = [
        Landmark(name="left_shoulder", x_px=300, y_px=300, confidence=0.9),
        Landmark(name="right_shoulder", x_px=300, y_px=300, confidence=0.9),
    ]
    tracker.update_from_landmarks(centroid_lms)
    assert tracker.bbox == (175, 175, 275, 275)


def test_update_ignores_low_confidence():
    tracker = RoiTracker((100, 100, 200, 200), smooth=0.5)
    tracker.update_from_landmarks([
        Landmark(name="left_shoulder", x_px=300, y_px=300, confidence=0.1),
    ])
    assert tracker.bbox == (100, 100, 200, 200)  # unchanged
