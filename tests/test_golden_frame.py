"""Golden-frame regression: run the real MoveNet backend once on the single
real image and freeze the landmarks. Validates pipeline STABILITY across
refactors — NOT clinical accuracy (that is deferred to the pilot).

Skips cleanly if onnxruntime/cv2/model/image are unavailable, and auto-creates
the baseline on first run.
"""
import json

import pytest

from tests.conftest import GOLDEN_CROP, GOLDEN_IMAGE, GOLDEN_LANDMARKS, MOVENET_MODEL


def test_golden_frame_landmarks_stable():
    pytest.importorskip("onnxruntime")
    cv2 = pytest.importorskip("cv2")
    if not MOVENET_MODEL.exists() or not GOLDEN_IMAGE.exists():
        pytest.skip("MoveNet model or golden image not present")

    from equipose.pose_backend.movenet_backend import MoveNetPoseBackend

    img = cv2.imread(str(GOLDEN_IMAGE))
    assert img is not None, "failed to read golden image"
    l, t, r, b = GOLDEN_CROP
    crop = img[t:b, l:r]
    backend = MoveNetPoseBackend(model_path=MOVENET_MODEL)
    landmarks = backend.detect(crop)
    current = {lm.name: [round(lm.x_px, 1), round(lm.y_px, 1), round(lm.confidence, 3)]
               for lm in landmarks}
    assert len(current) == 17

    if not GOLDEN_LANDMARKS.exists():
        GOLDEN_LANDMARKS.write_text(json.dumps(current, indent=2, sort_keys=True))
        pytest.skip("golden landmark baseline created — re-run to assert stability")

    baseline = json.loads(GOLDEN_LANDMARKS.read_text())
    for name, (bx, by, _bc) in baseline.items():
        assert name in current, f"missing landmark {name}"
        cx, cy, _cc = current[name]
        assert abs(cx - bx) <= 2.0, f"{name} x drifted: {cx} vs {bx}"
        assert abs(cy - by) <= 2.0, f"{name} y drifted: {cy} vs {by}"
