"""SQLite persistence for patients, sessions, per-metric aggregates, and
therapist labels. Local-only (no network) — pediatric medical data.

``metric_history`` powers the longitudinal progress dashboard.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from equipose.schemas import PatientRecord, SessionReport

_SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    patient_id   TEXT PRIMARY KEY,
    age_years    INTEGER NOT NULL,
    gmfcs_level  INTEGER NOT NULL,
    notes        TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    patient_id    TEXT NOT NULL,
    view          TEXT NOT NULL,
    captured_at   TEXT NOT NULL,
    video_path    TEXT NOT NULL,
    fps           REAL NOT NULL,
    overall_score REAL NOT NULL,
    band          TEXT NOT NULL,
    notes         TEXT DEFAULT '',
    kind          TEXT NOT NULL DEFAULT 'session'  -- 'session' (video) | 'snapshot' (photo)
);
CREATE TABLE IF NOT EXISTS session_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    name            TEXT NOT NULL,
    reliability     TEXT NOT NULL,
    unit            TEXT NOT NULL,
    mean            REAL,
    max_deviation   REAL,
    pct_in_range    REAL,
    std             REAL,
    n_valid_frames  INTEGER NOT NULL,
    n_total_frames  INTEGER NOT NULL,
    confidence      REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS labels (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    frame_idx    INTEGER NOT NULL,
    label        TEXT NOT NULL,
    therapist_id TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        """Idempotent migrations for DBs created before a column existed."""
        try:
            self._conn.execute("ALTER TABLE sessions ADD COLUMN kind TEXT NOT NULL DEFAULT 'session'")
        except sqlite3.OperationalError:
            pass  # column already present

    def upsert_patient(self, p: PatientRecord) -> None:
        self._conn.execute(
            "INSERT INTO patients (patient_id, age_years, gmfcs_level, notes) VALUES (?,?,?,?) "
            "ON CONFLICT(patient_id) DO UPDATE SET age_years=excluded.age_years, "
            "gmfcs_level=excluded.gmfcs_level, notes=excluded.notes",
            (p.patient_id, p.age_years, p.gmfcs_level, p.notes),
        )
        self._conn.commit()

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        row = self._conn.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
        return PatientRecord(**dict(row)) if row else None

    def list_patients(self) -> list[PatientRecord]:
        rows = self._conn.execute("SELECT * FROM patients ORDER BY patient_id").fetchall()
        return [PatientRecord(**dict(r)) for r in rows]

    def save_report(self, r: SessionReport, kind: str = "session") -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, patient_id, view, captured_at, "
            "video_path, fps, overall_score, band, notes, kind) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (r.session_id, r.patient_id, r.view, r.captured_at, r.video_path, r.fps,
             r.overall_score, r.band, r.notes, kind),
        )
        self._conn.execute("DELETE FROM session_metrics WHERE session_id=?", (r.session_id,))
        for m in r.metrics:
            self._conn.execute(
                "INSERT INTO session_metrics (session_id, name, reliability, unit, mean, "
                "max_deviation, pct_in_range, std, n_valid_frames, n_total_frames, confidence) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (r.session_id, m.name, m.reliability, m.unit, m.mean, m.max_deviation,
                 m.pct_in_range, m.std, m.n_valid_frames, m.n_total_frames, m.confidence),
            )
        self._conn.commit()

    def list_sessions(self, patient_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM sessions WHERE patient_id=? ORDER BY captured_at", (patient_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def metric_history(self, patient_id: str, metric_name: str, view: str) -> list[tuple[str, float]]:
        rows = self._conn.execute(
            "SELECT s.captured_at AS captured_at, m.mean AS mean FROM sessions s "
            "JOIN session_metrics m ON m.session_id = s.session_id "
            "WHERE s.patient_id=? AND s.view=? AND m.name=? AND m.mean IS NOT NULL "
            "ORDER BY s.captured_at",
            (patient_id, view, metric_name),
        ).fetchall()
        return [(r["captured_at"], r["mean"]) for r in rows]

    def add_label(self, session_id: str, frame_idx: int, label: str,
                  therapist_id: str, created_at: str) -> None:
        self._conn.execute(
            "INSERT INTO labels (session_id, frame_idx, label, therapist_id, created_at) "
            "VALUES (?,?,?,?,?)",
            (session_id, frame_idx, label, therapist_id, created_at),
        )
        self._conn.commit()

    def list_labels(self, session_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM labels WHERE session_id=? ORDER BY frame_idx", (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()
