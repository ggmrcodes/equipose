"""End-to-end smoke: build a short video from the one real image, run the full
pipeline with the MoveNet backend, persist to SQLite, and export CSV + PDF + a
face-blurred frame. Proves the whole chain works on real image data.

    python demo/demo_end_to_end.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np

from equipose.config import load_scoring, load_thresholds
from equipose.export_csv import write_session_csv
from equipose.export_pdf import write_session_pdf
from equipose.persistence import Store
from equipose.pipeline import analyze_session
from equipose.pose_backend import get_backend
from equipose.privacy import blur_faces
from equipose.schemas import PatientRecord

REPO = Path(__file__).resolve().parents[1]
IMAGE = REPO / "tests" / "fixtures" / "golden_S__83238932.jpg"
CROP = (655, 180, 905, 690)  # child rider


def _make_video(img: np.ndarray, path: Path, n: int = 24, fps: int = 12) -> None:
    h, w = img.shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(n):
        # gentle synthetic sway so the series isn't perfectly static
        shift = int(6 * np.sin(i / 3.0))
        M = np.float32([[1, 0, shift], [0, 1, 0]])
        writer.write(cv2.warpAffine(img, M, (w, h)))
    writer.release()


def main() -> None:
    img = cv2.imread(str(IMAGE))
    assert img is not None, f"cannot read {IMAGE}"
    out = Path(tempfile.mkdtemp(prefix="equipose_demo_"))
    video = out / "front.mp4"
    _make_video(img, video)
    print(f"built video: {video} ({video.stat().st_size} bytes)")

    report = analyze_session(
        str(video), "front", "DEMO-01", CROP,
        session_id="DEMO-01-front-0001", captured_at="2026-06-16T12:00:00",
        backend=get_backend("movenet"),
        thresholds=load_thresholds(), scoring=load_scoring(),
        qc=False,
    )
    print(f"\nfps={report.fps:.1f}  score={report.overall_score:.0f}/100  band={report.band}")
    for m in report.metrics:
        val = "—" if m.mean is None else f"{m.mean:7.2f} {m.unit}"
        pct = "—" if m.pct_in_range is None else f"{m.pct_in_range*100:5.0f}% in-range"
        print(f"  {m.name:24s} [{m.reliability:11s}] {val:18s} {pct:16s} "
              f"valid {m.n_valid_frames}/{m.n_total_frames}  conf {m.confidence:.2f}")

    store = Store(out / "equipose.sqlite")
    store.upsert_patient(PatientRecord(patient_id="DEMO-01", age_years=8, gmfcs_level=3))
    store.save_report(report)
    store.close()

    csv_path = write_session_csv(report, out / "session.csv")
    pdf_path = write_session_pdf(report, out / "session.pdf")

    # privacy: face-blur a frame using the detected landmarks
    crop = img[CROP[1]:CROP[3], CROP[0]:CROP[2]]
    lms = get_backend("movenet").detect(crop)
    blurred = blur_faces(crop, lms)
    blurred_path = out / "frame_faceblur.png"
    cv2.imwrite(str(blurred_path), blurred)

    print(f"\nartifacts in {out}:")
    for p in (out / "equipose.sqlite", csv_path, pdf_path, blurred_path):
        p = Path(p)
        print(f"  {p.name:22s} {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
