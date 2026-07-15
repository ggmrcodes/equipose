# Spec: PDF Export — Patient Progress Report

**Date:** 2026-06-21  **Status:** approved design

## Context
The Review view shows a child's posture over the program on screen, but there's
no way to share it with caregivers, an MDT, or the medical record. This adds a
**Download progress report (PDF)** from Review. An orphaned `export_pdf.py`
(`write_session_pdf`, a per-session light report) exists but is unused, untested,
and pre-dates the redesign; it will be **replaced** by the progress-report
builder.

### Decisions locked with the user
1. **Scope:** patient progress report (the Review content), not per-reading.
2. **Engine:** reportlab + matplotlib (both already deps; offline; no new deps).
3. **Audience:** clinical, opening with a short plain-language summary for parents.

### Design decisions (mine, stated)
- **Light, printable** document (white paper, ink text, deep dusty-rose accent,
  status traffic-light tuned for white). The app is dark, but a filed/printed
  clinical artifact should be light.
- Fonts: reportlab built-in **Helvetica** (robust; the app's woff2 fonts can't be
  loaded by reportlab without conversion).
- **No child images** in this report → de-identified by construction (patient
  code only).

### Non-goals (v1)
Per-reading PDF; embedding the goniometer photo; multi-patient batch export.

## Architecture

### `export_pdf.py` (rewritten)
`build_progress_pdf(patient, view, sessions, series, thresholds, generated_at) -> bytes`
- **Pure** (no DB): all data is passed in, so it's unit-testable and returns PDF
  bytes for `st.download_button`.
- Inputs: `patient` (PatientRecord), `view`, `sessions` (list of session dicts,
  oldest→newest), `series` ({metric_name: [(captured_at, mean), ...]}),
  `thresholds` (ThresholdConfig), `generated_at` (str; no clock in the pure fn).
- Layout (reportlab `SimpleDocTemplate` → `BytesIO`, letter, 1in margins):
  1. **Header** — "equipose" wordmark + a small plumb/goniometer mark (drawn or
     embedded), `patient code · age · GMFCS`, view, date range, "Generated …".
  2. **Summary** — `_summary(...)` templated paragraph (improved/held/declined +
     count and names of metrics that moved into range + provisional caveat).
  3. **Overview strip** — readings, span, latest score + band, trend.
  4. **Overall-score trend** — `_overall_chart_png(sessions)` (matplotlib, white,
     rose line, 0–100).
  5. **Per-metric small multiples** — `_metrics_grid_png(names, series,
     thresholds)` (subplot grid; each metric's mean over time + `axhspan(lo,hi)`
     faint-green acceptable band).
  6. **History table** — reportlab Table: date, type (photo/video), score, status.
  7. **Provenance footer** — provisional thresholds, 2D approximations, screening
     aid not a diagnostic device, local-only.

### Helpers (in `export_pdf.py`)
- `_overall_chart_png(sessions) -> bytes`, `_metrics_grid_png(...) -> bytes`
  (matplotlib Agg, light palette, return PNG bytes via `BytesIO`).
- `_summary(patient, view, sessions, series, thresholds) -> str`:
  - n≥2: direction from `last − first` overall (improved >+5, held ±5,
    declined <−5); "moved into range" = metrics whose first reading was outside
    `[lo,hi]` and last inside (count + up to 3 names); ends with the provisional /
    not-a-diagnosis caveat. No em-dashes.
  - n==1: "A single reading on {date}; trends appear after the next visit."
  - `in_range(v) = lo <= v <= hi` (matches `aggregate`).

### Integration (`flow_review.py`)
After the history table, a **"Download progress report (PDF)"** button:
`store.get_patient(pid)` + the already-gathered `sessions`/`series` + `thresholds`
+ `datetime.now(timezone.utc)` → `build_progress_pdf(...)` →
`st.download_button(file_name=f"{pid}_{view}_progress.pdf")`.

## Privacy
Code-only, no images → de-identified. Footer carries local-only + provisional +
not-diagnostic notes.

## Testing (`tests/test_export_pdf.py`)
- `build_progress_pdf(...)` returns bytes starting `b"%PDF"`, non-trivial size.
- `_summary`: improving series says "improved" and names a moved-into-range
  metric; single-reading (n=1) returns the graceful one-reading sentence.
- `_overall_chart_png` / `_metrics_grid_png` return PNG bytes (`\x89PNG` header).
- `flow_review.render` smoke (already covered); download path verified live.

## Verification
`pytest` green; restart server; in Review for the seeded DEMO-PROG patient, click
Download, open the PDF, confirm header/summary/overview/trend/small-multiples/
history/footer render and the summary text matches the data. Iterate layout via
`pdftoppm` screenshots.
