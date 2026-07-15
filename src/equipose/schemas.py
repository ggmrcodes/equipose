"""Pydantic v2 data contracts shared across the pipeline.

Single source of truth for every data shape. Modeled on the BART_LAB
``records.py`` style (``extra="forbid"``, explicit field constraints).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Reliability = Literal["primary", "best_effort"]
View = Literal["front", "side"]
Band = Literal["green", "yellow", "red"]


class Landmark(BaseModel):
    """A single body landmark in original-image pixel space.

    ``confidence`` carries the backend's visibility/score so downstream code
    can gate occluded joints (the core occlusion strategy).
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    x_px: float
    y_px: float
    confidence: float = Field(ge=0.0, le=1.0)


class FramePose(BaseModel):
    """All landmarks detected for one video frame (in full-image pixels)."""

    model_config = ConfigDict(extra="forbid")

    frame_idx: int
    t_sec: float
    landmarks: list[Landmark]
    roi_bbox: Optional[tuple[int, int, int, int]] = None


class FrameAngles(BaseModel):
    """Per-frame posture-metric values. ``None`` value == skipped (occluded)."""

    model_config = ConfigDict(extra="forbid")

    frame_idx: int
    t_sec: float
    values: dict[str, Optional[float]]
    confidences: dict[str, float]


class SessionMetric(BaseModel):
    """Aggregate of one posture metric across a session."""

    model_config = ConfigDict(extra="forbid")

    name: str
    reliability: Reliability
    unit: str
    mean: Optional[float] = None
    max_deviation: Optional[float] = None  # max distance outside acceptable range
    pct_in_range: Optional[float] = None  # fraction of valid frames within range [0,1]
    graded_score: Optional[float] = None  # mean graded proximity-to-ideal [0,1]; drives the score
    std: Optional[float] = None
    n_valid_frames: int = 0
    n_total_frames: int = 0
    confidence: float = 0.0  # mean per-frame confidence over valid frames


class SessionReport(BaseModel):
    """One analyzed video (one view). Front and side are separate reports."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    patient_id: str
    view: View
    captured_at: str  # ISO-8601; supplied by caller (no clock calls in core)
    video_path: str
    fps: float
    metrics: list[SessionMetric]
    overall_score: float
    band: Band
    notes: str = ""


class PatientRecord(BaseModel):
    """Minimal patient identity for longitudinal tracking (no free-text PII)."""

    model_config = ConfigDict(extra="forbid")

    patient_id: str
    age_years: int = Field(ge=0, le=25)
    gmfcs_level: int = Field(ge=1, le=5)
    notes: str = ""
