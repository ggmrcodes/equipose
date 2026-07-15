"""Patient progress-report PDF: pure builders + valid PDF bytes."""
from equipose import export_pdf
from equipose.config import load_thresholds
from equipose.schemas import PatientRecord

_PATIENT = PatientRecord(patient_id="P-001", age_years=8, gmfcs_level=3)


def _sessions():
    return [
        {"captured_at": "2026-04-01T10:00:00", "overall_score": 55.0, "band": "red",
         "view": "front", "kind": "snapshot"},
        {"captured_at": "2026-05-01T10:00:00", "overall_score": 72.0, "band": "yellow",
         "view": "front", "kind": "snapshot"},
        {"captured_at": "2026-06-01T10:00:00", "overall_score": 88.0, "band": "green",
         "view": "front", "kind": "session"},
    ]


def _series():  # head_tilt moves from out (9) into range (2); shoulder stays in
    return {
        "head_tilt": [("2026-04-01T10:00:00", 9.0), ("2026-05-01T10:00:00", 5.0),
                      ("2026-06-01T10:00:00", 2.0)],
        "shoulder_tilt": [("2026-04-01T10:00:00", 3.0), ("2026-06-01T10:00:00", 1.0)],
    }


def test_build_progress_pdf_is_valid():
    th = load_thresholds()
    pdf = export_pdf.build_progress_pdf(_PATIENT, "front", _sessions(), _series(), th,
                                        "2026-06-21T00:00:00")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000  # has charts embedded, not an empty doc


def test_summary_improving_names_moved_in_metric():
    th = load_thresholds()
    s = export_pdf._summary(_PATIENT, "front", _sessions(), _series(), th)
    assert "improved" in s and "55 to 88" in s
    assert "head tilt" in s            # moved from 9 (out of +/-5) into 2 (in)
    assert "not a diagnosis" in s      # provisional caveat present


def test_summary_single_reading_is_graceful():
    th = load_thresholds()
    one = _sessions()[:1]
    s = export_pdf._summary(_PATIENT, "front", one, {}, th)
    assert "single" in s.lower() and "next visit" in s


def test_chart_builders_return_png():
    th = load_thresholds()
    assert export_pdf._overall_chart_png(_sessions())[:4] == b"\x89PNG"
    grid = export_pdf._metrics_grid_png(list(_series().keys()), _series(), th)
    assert grid[:4] == b"\x89PNG"
