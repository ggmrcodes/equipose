"""Guided single-flow workspace: Patient -> Capture -> Read.

One continuous workspace driven by ``st.session_state``. Step 1 picks or adds a
patient; step 2 captures a photo or video and analyzes it; step 3 reads the
result and the patient's trend. Replaces the old four-page sidebar nav.
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from equipose.config import load_scoring, load_thresholds
from equipose.dashboard import flow_review, ui
from equipose.dashboard.roi_select import select_bbox, select_bbox_image
from equipose.persistence import Store
from equipose.pipeline import analyze_image, analyze_session
from equipose.pose_backend import get_backend
from equipose.schemas import PatientRecord

STEPS = ["Patient", "Capture", "Read"]
_DISCLAIMER = ("Normal ranges are provisional: coronal targets are principled "
               "(level/centered = 0), but the sagittal joint ranges still need clinical "
               "literature and pilot calibration (hover a range for its basis). Values are "
               "2D projective approximations. A screening aid, not a diagnostic device.")


def _init() -> None:
    import streamlit as st

    st.session_state.setdefault("eq_step", 0)
    st.session_state.setdefault("eq_patient", None)
    st.session_state.setdefault("eq_result", None)
    st.session_state.setdefault("eq_mode", "capture")
    st.session_state.setdefault("eq_saved", None)


def _goto(step: int) -> None:
    import streamlit as st

    st.session_state.eq_step = step
    st.rerun()


def _mode_toggle() -> None:
    import streamlit as st

    mode = st.session_state.eq_mode
    c1, c2, _ = st.columns([1, 1, 5])
    if c1.button("Capture", type="primary" if mode == "capture" else "secondary", width="stretch"):
        if mode != "capture":
            st.session_state.eq_mode = "capture"
            st.rerun()
    if c2.button("Review", type="primary" if mode == "review" else "secondary", width="stretch"):
        if mode != "review":
            st.session_state.eq_mode = "review"
            st.rerun()


def render(store: Store) -> None:
    import streamlit as st

    _init()
    ui.app_header(st.session_state.eq_patient)
    _mode_toggle()

    if st.session_state.eq_mode == "review":
        flow_review.render(store)
    else:
        step = st.session_state.eq_step
        with st.sidebar:
            st.markdown('<div class="eq-railhead">STEPS</div>', unsafe_allow_html=True)
            ui.stepper(STEPS, step)
        if step == 0:
            _step_patient(store)
        elif step == 1:
            _step_capture(store)
        else:
            _step_read(store)

    from equipose import deploy
    if deploy.is_hosted():
        ui.footer("equipose · HOSTED DEMO — images are processed on a server; do NOT upload "
                  "real patient data · research build, not a diagnostic device · placeholder thresholds.")
    else:
        ui.footer("equipose · local-only, no data leaves this machine · faces are blurred in any export.")


# ---- step 1: patient ------------------------------------------------------
def _step_patient(store: Store) -> None:
    import streamlit as st

    ui.section("Who are we looking at?", eyebrow="Step 1 · Patient",
               lead="Pick a child to continue, or add a new one. Use a code, never a real name.")
    patients = store.list_patients()

    if patients:
        ids = [p.patient_id for p in patients]
        current = st.session_state.eq_patient
        idx = ids.index(current) if current in ids else 0
        pid = st.selectbox("Patient", ids, index=idx)
        if st.button("Continue", type="primary"):
            st.session_state.eq_patient = pid
            _goto(1)
    else:
        ui.disclaimer("No patients yet. Add the first one below.")

    with st.expander("Add a new patient", expanded=not patients):
        with st.form("add_patient"):
            c1, c2, c3 = st.columns([2, 1, 1])
            new_id = c1.text_input("Patient code")
            age = c2.number_input("Age", 0, 25, 8)
            gmfcs = c3.number_input("GMFCS", 1, 5, 3)
            notes = st.text_input("Notes", "")
            if st.form_submit_button("Add and continue", type="primary") and new_id:
                store.upsert_patient(PatientRecord(patient_id=new_id, age_years=int(age),
                                                   gmfcs_level=int(gmfcs), notes=notes))
                st.session_state.eq_patient = new_id
                _goto(1)


# ---- step 2: capture ------------------------------------------------------
def _save_upload(uploaded) -> str:
    suffix = Path(uploaded.name).suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getbuffer())
    tmp.flush()
    tmp.close()
    return tmp.name


def _step_capture(store: Store) -> None:
    import cv2
    import numpy as np
    import streamlit as st

    pid = st.session_state.eq_patient
    if not pid:
        _goto(0)
        return

    ui.section("Capture a reading", eyebrow="Step 2 · Capture",
               lead="A photo gives a snapshot; a video gives a full session. Front reads "
                    "coronal posture, side reads sagittal.")
    c1, c2, c3 = st.columns(3)
    mode = c1.radio("Source", ["photo", "video"], horizontal=True)
    view = c2.radio("View", ["front", "side"], horizontal=True)
    from equipose import deploy
    backends = ["mediapipe"] if deploy.is_hosted() else ["mediapipe", "movenet"]
    backend_name = c3.selectbox("Pose backend", backends)

    if mode == "photo":
        uploaded = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "webp", "bmp"])
        if uploaded:
            data = np.frombuffer(uploaded.getbuffer(), dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if image is None:
                st.error("Could not decode this image.")
            else:
                bbox = select_bbox_image(image)
                b1, b2 = st.columns([1, 1])
                if b2.button("Analyze", type="primary"):
                    _run_photo(image, view, bbox, backend_name)
                if b1.button("Back"):
                    _goto(0)
    else:
        uploaded = st.file_uploader("Video", type=["mp4", "mov", "avi", "m4v"])
        if uploaded:
            path = _save_upload(uploaded)
            bbox = select_bbox(path)
            b1, b2 = st.columns([1, 1])
            if b2.button("Analyze", type="primary"):
                _run_video(store, path, view, bbox, backend_name, pid)
            if b1.button("Back"):
                _goto(0)

    if not uploaded:
        if st.button("Back"):
            _goto(0)


def _run_photo(image, view, bbox, backend_name) -> None:
    import streamlit as st

    with st.spinner("Detecting pose…"):
        report, landmarks = analyze_image(
            image, view, bbox, backend=get_backend(backend_name),
            thresholds=load_thresholds(), scoring=load_scoring(),
            captured_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            patient_id=st.session_state.eq_patient,
        )
    st.session_state.eq_result = {
        "kind": "Snapshot", "report": report, "view": view,
        "image_bgr": image.copy(), "landmarks": landmarks,
    }
    _goto(2)


def _run_video(store, path, view, bbox, backend_name, pid) -> None:
    import streamlit as st

    stamp = datetime.now(timezone.utc)
    with st.spinner("Analyzing video…"):
        report = analyze_session(
            path, view, pid, bbox,
            session_id=f"{pid}-{view}-{stamp.strftime('%Y%m%dT%H%M%S')}",
            captured_at=stamp.isoformat(timespec="seconds"),
            backend=get_backend(backend_name),
            thresholds=load_thresholds(), scoring=load_scoring(), qc=True,
        )
        store.save_report(report)
    st.session_state.eq_result = {"kind": "Session", "report": report, "view": view,
                                  "image_bgr": None, "landmarks": None}
    _goto(2)


# ---- step 3: read ---------------------------------------------------------
def _render_goniometer(res, store: Store) -> None:
    """Full-width annotated photo with live overlay toggles + save/download actions.
    The score/status now lead the screen in the summary hero, so this is evidence."""
    import base64

    import cv2
    import streamlit as st

    from equipose.dashboard import overlay
    from equipose.privacy import blur_faces

    report, view = res["report"], res["view"]
    raw, landmarks = res["image_bgr"], res["landmarks"]
    h, w = raw.shape[:2]

    st.markdown('<div class="eq-eyebrow" style="margin:.1rem 0 .1rem">Overlays · annotated photo</div>',
                unsafe_allow_html=True)
    t = st.columns(4)
    layers = set()
    if t[0].toggle("Angle arcs", True):
        layers.add("arcs")
    if t[1].toggle("Reference lines", True):
        layers.add("reference")
    if t[2].toggle("Skeleton", True):
        layers.add("skeleton")
    if t[3].toggle("Labels", True):
        layers.add("labels")

    spec = overlay.build_overlay_spec(landmarks, view, report.metrics, layers, w, h,
                                      scoring=load_scoring())

    # display base downscaled for a lighter inline data URI; viewBox stays full-res
    disp = raw if w <= 1000 else cv2.resize(raw, (1000, int(h * 1000 / w)), interpolation=cv2.INTER_AREA)
    ok, dbuf = cv2.imencode(".png", disp)
    uri = ("data:image/png;base64," + base64.b64encode(dbuf.tobytes()).decode()) if ok else ""

    # full-width evidence photo
    st.markdown(overlay.overlay_svg(spec, w, h, uri), unsafe_allow_html=True)
    st.write("")

    # actions row
    sid = f"{report.patient_id}-photo-{report.captured_at}"
    a, b = st.columns([1, 1])
    if a.button("Save to patient record", type="primary"):
        store.save_report(report.model_copy(update={"session_id": sid}), kind="snapshot")
        st.session_state.eq_saved = report.captured_at
        st.success("Saved to patient record.")
    raster = overlay.overlay_raster(blur_faces(raw, landmarks), spec)
    ok2, rbuf = cv2.imencode(".png", raster)
    if ok2:
        b.download_button("Download annotated (face-blurred)", data=rbuf.tobytes(),
                          file_name=f"posture_{view}.png", mime="image/png")
    if st.session_state.get("eq_saved") == report.captured_at:
        if st.button("View progress"):
            st.session_state.eq_mode = "review"
            st.rerun()


def _step_read(store: Store) -> None:
    import pandas as pd
    import streamlit as st

    res = st.session_state.eq_result
    if not res:
        _goto(1)
        return
    report = res["report"]

    ui.section("The reading", eyebrow=f"Step 3 · Read · {res['view']} view",
               lead=f"{res['kind']} for patient {report.patient_id}.")

    scoring = load_scoring()
    # baseline: the child's own earliest prior session for this view (not a cohort avg)
    prior = [s for s in store.list_sessions(report.patient_id)
             if s["view"] == report.view and s["session_id"] != report.session_id]
    baseline = prior[0]["overall_score"] if prior else None

    # answer-first summary hero: score dial + status + plain-language 'why' + position scale
    why = ui.reading_why(report.metrics, scoring)
    ui.reading_hero(report.overall_score, report.band, why, scoring, baseline, kind=res["kind"])
    st.write("")

    # big annotated evidence photo (+ overlay toggles + actions); video has no photo
    if res["image_bgr"] is not None:
        _render_goniometer(res, store)
    st.write("")

    with st.expander("Why this score?"):
        ui.score_breakdown(report.metrics, scoring, report.overall_score)

    st.write("")
    # Orient the sagittal schematic to match the subject's facing in the photo.
    # Landmarks are retained for photo snapshots only; video sessions keep the
    # base (right-facing) orientation. See angles_side.facing_direction.
    face_left = False
    if res["view"] == "side" and res.get("landmarks"):
        from equipose.angles_side import facing_direction
        face_left = facing_direction(res["landmarks"]) == "left"
    thresholds = load_thresholds()
    ui.posture_panel(res["view"], report.metrics, face_left=face_left, scoring=scoring,
                     thresholds=thresholds)
    st.write("")
    ui.metrics_table(report.metrics, thresholds, scoring=scoring)
    st.write("")
    ui.disclaimer(_DISCLAIMER)

    # patient trend (stored sessions only)
    sessions = [s for s in store.list_sessions(report.patient_id) if s["view"] == report.view]
    if len(sessions) >= 2:
        st.write("")
        ui.section("Progress", eyebrow="Same patient · same view")
        sdf = pd.DataFrame([(s["captured_at"], s["overall_score"]) for s in sessions],
                           columns=["captured_at", "overall_score"])
        sdf["captured_at"] = pd.to_datetime(sdf["captured_at"])
        st.altair_chart(ui.trend_chart(sdf, "captured_at", "overall_score", "score / 100"),
                        width="stretch")

    st.write("")
    a, b = st.columns([1, 1])
    if a.button("Capture another", type="primary"):
        st.session_state.eq_result = None
        _goto(1)
    if b.button("Switch patient"):
        st.session_state.eq_result = None
        _goto(0)
