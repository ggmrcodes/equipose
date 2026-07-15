"""Typed loaders for the YAML config so thresholds never live in code.

All clinical values are PLACEHOLDERS to be tuned at the pilot (the build has
only one real image — no clinical data to calibrate against yet).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict

# repo_root/config  (src/equipose/config.py -> parents[2] == repo root)
_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


_UNIT_SUFFIX = {"deg": "°", "frac_shoulder_w": " w", "frac_back": " b", "score": ""}
_MINUS = "−"  # typographic minus, not a dash


class MetricThreshold(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acceptable: tuple[float, float]  # [min, max] in the metric's natural unit
    unit: str
    reliability: Literal["primary", "best_effort"]
    higher_is_better: bool = False  # ideal sits at the UPPER edge (e.g. neck stacked = 180)
    lower_is_better: bool = False   # ideal sits at the LOWER edge (e.g. midline deviation = 0)
    basis: str = ""  # why this range is what it is (principled vs needs-literature)


class ThresholdConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: dict[str, MetricThreshold]

    def acceptable_range(self, name: str) -> tuple[float, float]:
        return self.metrics[name].acceptable

    def reliability(self, name: str) -> str:
        return self.metrics[name].reliability

    def unit(self, name: str) -> str:
        return self.metrics[name].unit

    def basis(self, name: str) -> str:
        return self.metrics[name].basis if name in self.metrics else ""

    def names(self) -> list[str]:
        return list(self.metrics.keys())

    def format_range(self, name: str) -> str:
        """Human-readable normal range, e.g. '±5°', '≤ 0.10 w', '≥ 80'."""
        m = self.metrics.get(name)
        if m is None:
            return ""
        lo, hi = m.acceptable
        suf = _UNIT_SUFFIX.get(m.unit, "")

        def num(v: float) -> str:
            s = f"{v:.2f}" if m.unit in ("frac_shoulder_w", "frac_back") else f"{v:g}"
            return s.replace("-", _MINUS)

        if m.higher_is_better:
            return f"≥ {num(lo)}{suf}"
        if lo == 0:
            return f"≤ {num(hi)}{suf}"
        if lo == -hi:
            return f"±{num(hi)}{suf}"
        return f"{num(lo)}{suf} to {num(hi)}{suf}"


class ScoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    green_min: float
    yellow_min: float
    min_coverage: float  # min fraction of valid frames for a metric to count
    best_effort_min_confidence: float
    weights: dict[str, float]
    display_only: list[str] = []  # shown as summaries, excluded from the score


def load_thresholds(path: Optional[str | Path] = None) -> ThresholdConfig:
    p = Path(path) if path else _CONFIG_DIR / "thresholds.yaml"
    return ThresholdConfig(**yaml.safe_load(p.read_text()))


def load_scoring(path: Optional[str | Path] = None) -> ScoringConfig:
    p = Path(path) if path else _CONFIG_DIR / "scoring.yaml"
    return ScoringConfig(**yaml.safe_load(p.read_text()))
