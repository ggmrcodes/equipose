"""Session orchestrator: video (one view) -> SessionReport.

Pure analysis — the caller owns persistence/export. Accepts either a video path
(read via VideoSession) or an injected ``frames`` iterator of
(frame_idx, t_sec, frame_bgr) tuples, which lets tests drive the full pipeline
on synthetic frames with no codec/model dependency.
"""
from __future__ import annotations

from typing import Iterable, Optional, Tuple

import numpy as np

from equipose.aggregate import aggregate_metric
from equipose.angles_front import FRONT_METRICS, compute_front
from equipose.angles_side import SIDE_METRICS, compute_side
from equipose.config import ScoringConfig, ThresholdConfig, load_scoring, load_thresholds
from equipose.pose_backend import PoseBackend, get_backend
from equipose.quality import run_qc
from equipose.roi import Bbox, RoiTracker
from equipose.schemas import Landmark, SessionReport, View
from equipose.scoring import score_session
from equipose.smoothing import smooth_series
from equipose.video import VideoSession

FrameTuple = Tuple[int, float, np.ndarray]


def analyze_session(
    video_path: str,
    view: View,
    patient_id: str,
    init_bbox: Bbox,
    *,
    session_id: str,
    captured_at: str,
    backend: Optional[PoseBackend] = None,
    thresholds: Optional[ThresholdConfig] = None,
    scoring: Optional[ScoringConfig] = None,
    vis_threshold: float = 0.3,
    qc: bool = False,
    smoothing_kw: Optional[dict] = None,
    frames: Optional[Iterable[FrameTuple]] = None,
    notes: str = "",
) -> SessionReport:
    backend = backend or get_backend("mediapipe")
    thresholds = thresholds or load_thresholds()
    scoring = scoring or load_scoring()
    compute = compute_front if view == "front" else compute_side
    metric_names = FRONT_METRICS if view == "front" else SIDE_METRICS

    tracker = RoiTracker(init_bbox)
    times: list[float] = []
    per_frame: dict[str, list] = {n: [] for n in metric_names}
    per_conf: dict[str, list] = {n: [] for n in metric_names}

    vs: Optional[VideoSession] = None
    if frames is None:
        vs = VideoSession(video_path)
        frames = vs.frames()

    def _skip(t: float) -> None:
        times.append(t)
        for n in metric_names:
            per_frame[n].append(None)
            per_conf[n].append(0.0)

    for _idx, t, frame in frames:
        if qc and not run_qc(frame).ok:
            _skip(t)
            continue
        square, transform = tracker.crop(frame)
        landmarks = RoiTracker.map_back(backend.detect(square), transform)
        tracker.update_from_landmarks(landmarks, vis_threshold)
        values, confs = compute(landmarks, vis_threshold)
        times.append(t)
        for n in metric_names:
            per_frame[n].append(values.get(n))
            per_conf[n].append(confs.get(n, 0.0))

    metrics = []
    for n in metric_names:
        smoothed = smooth_series(times, per_frame[n], **(smoothing_kw or {}))
        metrics.append(aggregate_metric(n, smoothed, per_conf[n], thresholds))

    if vs is not None:
        fps = vs.fps
    elif len(times) > 1 and times[1] != times[0]:
        fps = 1.0 / (times[1] - times[0])
    else:
        fps = 30.0

    score, band = score_session(metrics, scoring)
    return SessionReport(
        session_id=session_id, patient_id=patient_id, view=view, captured_at=captured_at,
        video_path=str(video_path), fps=fps, metrics=metrics, overall_score=score,
        band=band, notes=notes,
    )


def analyze_image(
    image_bgr: np.ndarray,
    view: View,
    init_bbox: Bbox,
    *,
    backend: Optional[PoseBackend] = None,
    thresholds: Optional[ThresholdConfig] = None,
    scoring: Optional[ScoringConfig] = None,
    vis_threshold: float = 0.3,
    session_id: str = "photo",
    captured_at: str = "",
    patient_id: str = "(photo)",
) -> tuple[SessionReport, list[Landmark]]:
    """Single-image ('snapshot') analysis.

    A photo is one frame: no temporal smoothing/aggregation. Each metric becomes a
    1-frame SessionMetric (mean = the value, pct_in_range = in/out flag). Returns
    the report AND the mapped landmarks so the caller can draw the overlay without
    a second inference. Not persisted here.
    """
    backend = backend or get_backend("mediapipe")
    thresholds = thresholds or load_thresholds()
    scoring = scoring or load_scoring()
    compute = compute_front if view == "front" else compute_side
    metric_names = list(FRONT_METRICS if view == "front" else SIDE_METRICS)

    tracker = RoiTracker(init_bbox)
    square, transform = tracker.crop(image_bgr)
    raw_lms = backend.detect(square)                       # crop-pixel coords
    landmarks = RoiTracker.map_back(raw_lms, transform)    # full-image coords
    values, confs = compute(landmarks, vis_threshold)

    # back_roundness (segmentation-based kyphosis proxy) — side photos only; needs the
    # crop image + crop-coord landmarks. None when it can't segment/measure (excluded,
    # never a false "good"). Not run for video (per-frame segmentation is expensive).
    if view == "side":
        from equipose.rounding import back_roundness_index
        br = back_roundness_index(square, raw_lms, vis_threshold)
        values["back_roundness"] = br
        confs["back_roundness"] = 1.0 if br is not None else 0.0
        metric_names.append("back_roundness")

    metrics = [aggregate_metric(n, [values.get(n)], [confs.get(n, 0.0)], thresholds)
               for n in metric_names]
    score, band = score_session(metrics, scoring)
    report = SessionReport(
        session_id=session_id, patient_id=patient_id, view=view, captured_at=captured_at,
        video_path="(photo upload)", fps=0.0, metrics=metrics, overall_score=score,
        band=band, notes="single photo — snapshot, no temporal data",
    )
    return report, landmarks
