"""Review mode: a patient's posture readings over time.

Overview header + overall-score trend + per-metric small multiples (acceptable
range shaded) + history table. Reads saved sessions (video) and snapshots
(photo) from the Store; both are SessionReports differing only by ``kind``.
"""
from __future__ import annotations

from equipose.angles_front import FRONT_METRICS
from equipose.angles_side import SIDE_METRICS
from equipose.config import load_thresholds
from equipose.dashboard import ui
from equipose.persistence import Store


def render(store: Store) -> None:
    import pandas as pd
    import streamlit as st

    ui.section("Review", eyebrow="Patient progress",
               lead="A child's posture readings over the therapy program.")
    patients = store.list_patients()
    if not patients:
        ui.disclaimer("No patients yet. Switch to Capture to add one.")
        return

    ids = [p.patient_id for p in patients]
    cur = st.session_state.get("eq_patient")
    c1, c2 = st.columns([2, 1])
    pid = c1.selectbox("Patient", ids, index=ids.index(cur) if cur in ids else 0, key="rev_pid")
    st.session_state.eq_patient = pid
    view = c2.radio("View", ["front", "side"], horizontal=True, key="rev_view")

    sessions = [s for s in store.list_sessions(pid) if s["view"] == view]
    if not sessions:
        ui.disclaimer(f"No saved {view} readings for {pid} yet. Capture one and use "
                      "'Save to patient record' to start the timeline.")
        return

    th = load_thresholds()
    ui.review_overview(sessions)

    st.write("")
    ui.section("Overall score", eyebrow="Trend")
    sdf = pd.DataFrame([(s["captured_at"], s["overall_score"]) for s in sessions],
                       columns=["t", "score"])
    sdf["t"] = pd.to_datetime(sdf["t"])
    st.altair_chart(ui.trend_chart(sdf, "t", "score", "score / 100"), width="stretch")

    names = FRONT_METRICS if view == "front" else SIDE_METRICS
    series = [(n, store.metric_history(pid, n, view)) for n in names]
    series = [(n, h) for n, h in series if h]
    if series:
        st.write("")
        ui.section("By metric", eyebrow="Trends · acceptable range shaded")
        cols = st.columns(2)
        for i, (name, hist) in enumerate(series):
            df = pd.DataFrame(hist, columns=["t", "v"])
            df["t"] = pd.to_datetime(df["t"])
            lo, hi = th.acceptable_range(name)
            with cols[i % 2]:
                ui._md(f'<div class="eq-eyebrow" style="margin-top:.7rem;">'
                       f'{name.replace("_", " ")} · latest {hist[-1][1]:.1f}{ui_unit(th, name)}</div>')
                st.altair_chart(ui.trend_chart(df, "t", "v", th.unit(name), height=170, band=(lo, hi)),
                                width="stretch")

    st.write("")
    ui.section("History", eyebrow="All readings")
    ui.review_history(sessions)

    # ---- PDF export ----
    st.write("")
    from datetime import datetime, timezone

    from equipose import export_pdf

    patient = store.get_patient(pid)
    if patient is not None:
        pdf = export_pdf.build_progress_pdf(
            patient, view, sessions, dict(series), th,
            datetime.now(timezone.utc).isoformat(timespec="seconds"))
        st.download_button("Download progress report (PDF)", data=pdf,
                           file_name=f"{pid}_{view}_progress.pdf", mime="application/pdf")


def ui_unit(th, name: str) -> str:
    u = th.unit(name)
    return "°" if u == "deg" else ""
