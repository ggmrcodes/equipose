"""Per-session CSV export (one row per metric). Appends; writes header once."""
from __future__ import annotations

import csv
from pathlib import Path

from equipose.schemas import SessionReport

CSV_FIELDS = [
    "session_id", "patient_id", "view", "captured_at", "metric", "reliability", "unit",
    "mean", "max_deviation", "pct_in_range", "std", "n_valid_frames", "n_total_frames",
    "confidence", "overall_score", "band",
]


def write_session_csv(report: SessionReport, path: str | Path) -> str:
    p = Path(path)
    is_new = not p.exists()
    with p.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        for m in report.metrics:
            writer.writerow({
                "session_id": report.session_id,
                "patient_id": report.patient_id,
                "view": report.view,
                "captured_at": report.captured_at,
                "metric": m.name,
                "reliability": m.reliability,
                "unit": m.unit,
                "mean": m.mean,
                "max_deviation": m.max_deviation,
                "pct_in_range": m.pct_in_range,
                "std": m.std,
                "n_valid_frames": m.n_valid_frames,
                "n_total_frames": m.n_total_frames,
                "confidence": m.confidence,
                "overall_score": report.overall_score,
                "band": report.band,
            })
    return str(p)
