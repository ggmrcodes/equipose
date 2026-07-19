# Body-chart redesign — per-joint callouts (build)

**Date:** 2026-07-19
**Status:** implemented 2026-07-19
**Problem:** the current body-chart crams a thin figure into ~20% of a wide panel with a
floating legend and dead space, and labels only two joints — not pretty, not intuitive.

## Design (per the approved mock)

The chart becomes one wide SVG: an **enlarged figure on the left** + a **column of
per-joint callouts on the right**, each linked to its joint by a faint leader line, +
a **compact legend footer**. Graphite-instrument language throughout (dark cards,
sage/amber/clay status, mono numerals, one bone tone — no rainbow, no bubbles).

- **Callout** = a small rounded `PANEL` card: status dot, joint **name** (SF), and
  **`you X° · ideal Y°`** (mono). `ideal` = `MetricThreshold.ideal`; unit from the metric.
- **Placement:** callouts stacked in a right-hand column, **ordered by joint height** so
  leader lines don't cross; leader from the joint (highlighted dot) to the card.
- **Which metrics get a callout:** the angle metrics that map to a figure joint —
  side: `forward_trunk_lean` (trunk), `neck_forward_angle` (neck), `hip_flexion` (hip),
  `knee_angle` (knee); front: `head_tilt`, `shoulder_tilt`, `pelvic_obliquity`,
  `trunk_lateral_lean`. Non-jointed metrics (`back_roundness`, `midline_deviation`) stay
  in the table only. Undetected joints: ghost segment + a "not detected" callout.
- **Legend:** compact horizontal row (Good/Watch/Concern/Not detected) as an SVG footer,
  replacing the side flex-list.

## Implementation

- `glyphs`: `_callouts_svg(specs, ...)` (reusable leader+card column, y-ordered),
  `_legend_svg()` (footer row). Rework `_posture_side` / `_posture_front` to draw the
  (enlarged) figure, build callout specs from the metric data, and compose figure +
  callouts + legend in a wider viewBox. `posture_chart_svg(view, data, face_left,
  thresholds=None)` gains `thresholds` (for ideal + unit); still renders value-only when
  it's absent.
- `ui.posture_panel`: build the data with status + value, pass `thresholds`; drop the
  separate `_legend_html` flex (legend now lives in the chart). Keep the full metrics
  table below (user's call — figure = at-a-glance, table = detail).

## Tests

- `_posture_side`/`_posture_front` render callout cards: joint names, `you`/`ideal` text,
  status colors, and the legend labels; ghost for undetected joints.
- Update the existing exact-coord tests (face-left mirror) to the new geometry.
- `posture_chart_svg` still renders with data lacking `thresholds` (value-only callouts).

## Out of scope

- Callouts for non-jointed metrics; front-view leader-crossing beyond simple y-ordering;
  animating the figure.
