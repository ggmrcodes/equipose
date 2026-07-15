from equipose.labeling import store_label
from equipose.persistence import Store
from equipose.schemas import PatientRecord, SessionMetric, SessionReport


def _report():
    return SessionReport(
        session_id="s1", patient_id="P1", view="front",
        captured_at="2026-01-01T10:00:00", video_path="front.mp4", fps=30.0,
        metrics=[SessionMetric(name="head_tilt", reliability="primary", unit="deg",
                               mean=2.0, max_deviation=0.0, pct_in_range=0.9, std=1.0,
                               n_valid_frames=9, n_total_frames=10, confidence=0.85)],
        overall_score=90.0, band="green",
    )


def test_roundtrip_and_history(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.upsert_patient(PatientRecord(patient_id="P1", age_years=8, gmfcs_level=3))
    store.save_report(_report())

    assert store.get_patient("P1").age_years == 8
    sessions = store.list_sessions("P1")
    assert len(sessions) == 1 and sessions[0]["band"] == "green"
    assert store.metric_history("P1", "head_tilt", "front") == [("2026-01-01T10:00:00", 2.0)]
    store.close()


def test_save_report_is_idempotent(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.save_report(_report())
    store.save_report(_report())  # replace, not duplicate
    assert len(store.list_sessions("P1")) == 1
    rows = store._conn.execute("SELECT COUNT(*) AS c FROM session_metrics").fetchone()
    assert rows["c"] == 1
    store.close()


def test_save_snapshot_kind(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.save_report(_report(), kind="snapshot")
    sessions = store.list_sessions("P1")
    assert sessions[0]["kind"] == "snapshot"
    store.close()


def test_default_kind_is_session(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.save_report(_report())  # default
    assert store.list_sessions("P1")[0]["kind"] == "session"
    store.close()


def test_migration_adds_kind_to_old_db(tmp_path):
    import sqlite3

    p = tmp_path / "old.sqlite"
    con = sqlite3.connect(p)
    con.executescript(
        "CREATE TABLE sessions (session_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, "
        "view TEXT NOT NULL, captured_at TEXT NOT NULL, video_path TEXT NOT NULL, fps REAL NOT NULL, "
        "overall_score REAL NOT NULL, band TEXT NOT NULL, notes TEXT DEFAULT '');"
    )
    con.execute("INSERT INTO sessions VALUES "
                "('s0','P1','front','2026-01-01T10:00:00','v.mp4',30,90,'green','')")
    con.commit()
    con.close()

    store = Store(p)  # __init__ runs the idempotent migration
    sessions = store.list_sessions("P1")
    assert len(sessions) == 1 and sessions[0]["kind"] == "session"  # backfilled default
    store.close()


def test_label_sink(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.save_report(_report())
    store_label(store, "s1", 42, "lean_left", "therapist-A", "2026-01-01T10:05:00")
    labels = store.list_labels("s1")
    assert labels[0]["label"] == "lean_left" and labels[0]["frame_idx"] == 42
    store.close()
