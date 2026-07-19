# Reading-screen gauges — position scale + in-band metric track (build)

**Date:** 2026-07-19
**Status:** implemented 2026-07-19
**Inspiration:** a posture-app reference (per-joint gauges + a "you vs ideal" position
slider), reinterpreted in equipose's graphite-instrument language — no rainbow, no
fabricated "average users", sage/amber/clay + one bone marker only.

Two components (both make the *graded* score legible; both status-colored, mono numerals):

## 1. Overall position scale

A horizontal scale reframing the 0–100 score as a position from "needs attention" to
"in range". Validated by mock; user approved the look.

- **Zones** from the band cutoffs (`scoring.yaml`): concern `[0, yellow_min)` clay,
  watch `[yellow_min, green_min)` amber, good `[green_min, 100]` sage — each a **muted
  ~20%-alpha** fill (calm heat scale, not neon), with a neutral track outline and mono
  ticks at the two cutoffs.
- **This-reading marker:** a bone (accent) vertical line + a status-colored dot at the
  score, mono score above it.
- **Baseline marker (honest, not "avg users"):** a dashed SOFT tick at the child's
  **earliest stored session score for this view**, labelled `baseline N`. Omitted when
  there's no prior session (fresh snapshot).
- End labels: `needs attention` (left) / `in range` (right).
- **Builder:** `ui.position_scale_html(score, band, scoring, baseline=None)` (pure).
  Rendered on the Reading screen under the score readout (`flow._step_read`), with the
  baseline pulled from `store.list_sessions(patient_id)` filtered by view.

## 2. In-band metric track (per row)

Each metric row gets a thin track showing where its value sits in its acceptable band —
the "position in range" idea, where there's room (the metrics list), not on the figure.

- A neutral horizontal band track; a subtle **ideal tick** (SOFT); a **value marker**
  (dot) at the value's normalized position in `[lo, hi]` (clamped to the edge when
  out-of-band), colored by the metric's **graded status** (`metric_status`).
- **Ideal** reuses the grading target: `MetricThreshold.ideal` = `hi` (higher_is_better),
  `lo` (lower_is_better), else band centre — a new property on the config model (same
  rule as `aggregate._graded_frame_score`).
- Replaces the current confidence mini-bar's slot in the row sub-line; `conf N.NN` stays
  as text. Not-detected / no-mean metrics show no track.
- **Builder:** `glyphs.inband_track_svg(value, lo, hi, ideal, status)` (pure). Emitted
  by `ui.metrics_table_html` per counted metric.

## Tests (TDD)

- `inband_track_svg`: value at ideal → marker at the ideal x; out-of-low / out-of-high →
  marker clamped to the ends; marker fill = status color (good/watch/concern).
- `position_scale_html`: marker x tracks the score; zone boundaries at the cutoffs;
  baseline tick present only when a baseline is given; contains the score + zone labels.
- `MetricThreshold.ideal`: centre / hi / lo by directionality.

## Out of scope

- Per-joint gauges on the body-chart figure (too cramped at 240×300 — dropped per the
  mock).
- Callout labels on the figure.
- Front-view gets the same treatment automatically (both builders are view-agnostic).
