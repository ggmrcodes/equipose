"""Shared test fixtures: synthetic-landmark builders + golden-image paths."""
from __future__ import annotations

from pathlib import Path

import pytest

from equipose.schemas import Landmark

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN_IMAGE = FIXTURES / "golden_S__83238932.jpg"
GOLDEN_LANDMARKS = FIXTURES / "golden_landmarks.json"
GOLDEN_CROP = (655, 180, 905, 690)  # proven child-rider crop from sample/movenet_skeleton.py
MOVENET_MODEL = Path(__file__).resolve().parents[1] / "models" / "movenet_singlepose_thunder_4.onnx"


def lm(name: str, x: float, y: float, c: float = 1.0) -> Landmark:
    return Landmark(name=name, x_px=float(x), y_px=float(y), confidence=float(c))


@pytest.fixture
def make_lm():
    return lm


def upright_front_landmarks(c: float = 0.9) -> list[Landmark]:
    """A symmetric, upright front-view pose -> all tilts ~0, symmetry ~100."""
    return [
        lm("nose", 100, 30, c),
        lm("left_eye", 95, 28, c), lm("right_eye", 105, 28, c),
        lm("left_ear", 90, 40, c), lm("right_ear", 110, 40, c),
        lm("left_shoulder", 80, 100, c), lm("right_shoulder", 120, 100, c),
        lm("left_hip", 85, 200, c), lm("right_hip", 115, 200, c),
    ]


def upright_side_landmarks(c: float = 0.9) -> list[Landmark]:
    """A right-facing side-view pose with all joints visible."""
    return [
        lm("right_ear", 90, 80, c),
        lm("right_shoulder", 100, 100, c),
        lm("right_hip", 100, 200, c),
        lm("right_knee", 140, 210, c),
        lm("right_ankle", 140, 260, c),
        # left side low confidence so the right side is auto-selected
        lm("left_shoulder", 100, 100, 0.1),
        lm("left_hip", 100, 200, 0.1),
    ]
