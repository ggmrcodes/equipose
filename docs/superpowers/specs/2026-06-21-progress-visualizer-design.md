# Spec: Patient Progress Visualizer (Review)

**Date:** 2026-06-21  **Status:** approved design

## Context
equipose stores each analyzed reading as a `SessionReport` in SQLite, but there
is no surface to review a child's posture over the 3–6 month program, and photo
snapshots aren't saved at all (only video sessions). Therapists work mostly from
photos, so progress can't be reviewed today. This adds a **Review** destination
that visualizes a patient's history, and makes **photo snapshots saveable** so
they populate the timeline.

### Decisions locked with the user
1. **Photos become saveable dated assessments** (a "Save to patient record"
   action on a photo result), feeding the same timeline as video sessions.
2. **Dedicated Review destination**, reachable from the start (a Capture/Review
   mode toggle), separate from the Patient→Capture→Read capture flow.
3. **Content:** patient overview + overall-score trend + per-metric small
   multiples with the acceptable-range band shaded + session history table.

### Non-goals (v1)
Session-vs-session side-by-side comparison; goals/targets; exporting a progress
PDF. (Each is a clean follow-up.)

## Architecture

A saved photo is already a `SessionReport` (built by `analyze_image` with
patient/view/metrics), so persisting one is just `save_report(...)` — no new
table. One `kind` column distinguishes photo assessments from video sessions.
Charts reuse `ui.trend_chart` + `persistence.metric_history`.

### Persistence (`persistence.py`)
- `sessions` gains `kind TEXT NOT NULL DEFAULT 'session'` (in `_SCHEMA` for fresh
  DBs; an idempotent `ALTER TABLE ... ADD COLUMN` in `Store.__init__`, wrapped to
  ignore "duplicate column", migrates the existing dev DB).
- `save_report(report, kind="session")` writes `kind`; photo save passes
  `kind="snapshot"`.
- `list_sessions(patient_id)` (already `SELECT *`) returns `kind`.
- Existing `metric_history(patient_id, name, view)` is reused for per-metric
  trends; no new query needed.

### Navigation + saving (`flow.py`)
- `st.session_state.eq_mode` ∈ {`capture`, `review`}, default `capture`. A small
  two-button toggle under the header (active = primary/accent). `capture` renders
  the existing stepper flow; `review` renders the Review page.
- Photo Read step gains **Save to patient record**: session_id =
  `f"{pid}-photo-{captured_at}"` (deterministic, so re-saving replaces not
  duplicates), `store.save_report(report, kind="snapshot")`, confirmation, and a
  **View progress** button that sets `eq_mode="review"` and reruns. A
  session_state flag marks the current result saved (button disables/confirms).

### Review page (`dashboard/flow_review.py`)
`render(store)`:
- Patient selectbox (defaults to `eq_patient`); view radio (front/side) since
  metrics and trends are per-view.
- `sessions = [s for s in store.list_sessions(pid) if s["view"] == view]`.
- **Empty state** if none: "No saved readings yet for this view — capture one and
  Save to patient record."
- Otherwise:
  - **Overview header** (`ui.review_overview`): reading count, date range, latest
    overall score + band chip, trend direction (latest − first), photo vs video
    counts.
  - **Overall-score trend**: `ui.trend_chart` over `captured_at`.
  - **Per-metric small multiples**: iterate the view's metric set
    (`FRONT_METRICS` / `SIDE_METRICS`), skip metrics with no history; for each,
    `metric_history(...)` → a mini `ui.trend_chart(..., band=acceptable_range)`
    in a 2-column grid, titled with the metric + latest value.
  - **History table** (`ui.review_history`): date, type (photo/video from
    `kind`), view, score, band chip.

### UI components (`ui.py`)
- `trend_chart(..., band=None)`: when `band=(lo, hi)`, layer a faint in-range
  rect (full x-width, y∈[lo,hi]) under the line+points.
- `review_overview_html(sessions)` and `review_history_html(sessions)`: pure HTML
  builders (testable), warm-night styled.

## Data flow
```
photo Read -> "Save to patient record" -> save_report(report, kind="snapshot")
Review mode -> pick patient+view -> list_sessions + metric_history
   -> overview header + overall trend + per-metric small multiples (range bands)
      + history table
```

## Testing
- Persistence: `save_report(kind="snapshot")` round-trips with `kind`; opening a
  Store on an old-schema DB (no `kind`) adds the column and still reads;
  `list_sessions` orders mixed photo+video by date.
- UI: `review_overview_html` shows counts/latest/direction; `review_history_html`
  shows a row per session with type; `trend_chart(band=...)` includes the band
  mark.
- Flow: `flow_review.render` is callable (smoke); saving a photo report persists a
  retrievable `kind="snapshot"` row.

## Verification
`pytest` green; restart server; in Review mode an empty patient shows the empty
state; save a couple of photo readings then confirm the overview, overall trend,
per-metric small multiples with shaded bands, and history table all populate.
Iterate chart/grid layout via browse screenshots.
