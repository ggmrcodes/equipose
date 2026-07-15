"""MediaPipe Pose (Tasks API) backend.

Reimplements the BART_LAB ``pose.py`` pattern: deferred heavy-model
construction, a mockable ``_raw_process`` seam (so tests never need the model
file), and an index->canonical-name map. The map EXTENDS BART_LAB's 13-name
subset with eyes (2/5) and ears (7/8) so head-tilt is computable.

MediaPipe ``visibility`` is carried through as ``Landmark.confidence`` — this is
the per-joint occlusion signal the rest of the system gates on.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np

from equipose.schemas import Landmark

# MediaPipe Pose 33-landmark index -> canonical name (subset we use).
_INDEX_TO_NAME = {
    0: "nose",
    2: "left_eye", 5: "right_eye",
    7: "left_ear", 8: "right_ear",
    11: "left_shoulder", 12: "right_shoulder",
    13: "left_elbow", 14: "right_elbow",
    15: "left_wrist", 16: "right_wrist",
    23: "left_hip", 24: "right_hip",
    25: "left_knee", 26: "right_knee",
    27: "left_ankle", 28: "right_ankle",
}

# repo_root/models/...  (src/equipose/pose_backend/x.py -> parents[3] == repo root)
_DEFAULT_MODEL = Path(__file__).resolve().parents[3] / "models" / "pose_landmarker_full.task"


def _extract_pose_landmarks(result: Any) -> Optional[list]:
    """Adapt a Tasks-API result OR a legacy/mocked result to a flat landmark list.

    Tasks API: ``result.pose_landmarks`` is ``list[list[NormalizedLandmark]]``.
    Legacy/mock: ``result.pose_landmarks`` is a flat list, or has ``.landmark``.
    """
    if result is None:
        return None
    pl = getattr(result, "pose_landmarks", None)
    if not pl:
        return None
    if isinstance(pl, list):
        first = pl[0]
        if isinstance(first, list):          # Tasks API: list-of-lists
            return first
        if hasattr(first, "landmark"):        # wrapped
            return list(first.landmark)
        return pl                             # flat list of landmark-likes (mock)
    if hasattr(pl, "landmark"):               # legacy solutions style
        return list(pl.landmark)
    return None


class MediaPipePoseBackend:
    def __init__(self, model_path: Optional[str | Path] = None) -> None:
        self._model_path = Path(model_path) if model_path else _DEFAULT_MODEL
        self._landmarker = None  # built lazily on first real inference

    def _build_landmarker(self):  # pragma: no cover - needs the model file
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        base_options = mp_python.BaseOptions(model_asset_path=str(self._model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            output_segmentation_masks=False,
        )
        return vision.PoseLandmarker.create_from_options(options)

    def _raw_process(self, image_rgb: np.ndarray) -> Any:  # pragma: no cover - mocked in tests
        """Run the Tasks-API detector. The seam tests patch."""
        import mediapipe as mp

        if self._landmarker is None:
            self._landmarker = self._build_landmarker()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image_rgb))
        return self._landmarker.detect(mp_image)

    def detect(self, image_bgr: np.ndarray) -> list[Landmark]:
        h, w = image_bgr.shape[:2]
        image_rgb = np.ascontiguousarray(image_bgr[:, :, ::-1])
        result = self._raw_process(image_rgb)
        lms = _extract_pose_landmarks(result)
        if not lms:
            return []
        out: list[Landmark] = []
        for idx, name in _INDEX_TO_NAME.items():
            if idx >= len(lms):
                continue
            lm = lms[idx]
            vis = getattr(lm, "visibility", 1.0)
            conf = float(vis) if vis is not None else 0.0
            out.append(
                Landmark(
                    name=name,
                    x_px=float(lm.x) * w,
                    y_px=float(lm.y) * h,
                    confidence=min(max(conf, 0.0), 1.0),
                )
            )
        return out
