# `trunk_roundness` — sagittal rounding proxy (design)

**Date:** 2026-07-14
**Status:** implemented 2026-07-14 (band widened ±0.06 → ±0.10 during verification)
**Context:** The side score can't distinguish a slumped/rounded back from an upright
one — the four sagittal metrics all read "mildly fine" for a rounded rider (see
`project_equipose_scoring` memory / the weakest-link work in `scoring.py`). Root
cause: MediaPipe has **no mid-spine landmark**, and `forward_trunk_lean` is a
straight shoulder→hip chord that can't encode curvature. This adds a *proxy* for
forward rounding from the landmarks we do have.

## What it measures

The signed perpendicular distance of the **shoulder** from the **ear→hip line**,
normalized by ear–hip length (the "bow" of the ear–shoulder–hip arc):

```
d = signed_perpendicular_distance(shoulder, ear, hip)   # + when shoulder is anterior (toward facing dir)
L = euclidean(ear, hip)                                  # trunk length, scale reference
trunk_roundness = d / L                                  # dimensionless; +forward = rounding, 0 = aligned
```

- **Ideal = 0** — ear, shoulder, hip collinear (straight).
- **Positive** — shoulder bows forward of the ear–hip line = rounding/kyphotic slump.
- **Negative** — shoulder behind the line = over-arched/erect.
- Sign uses `angles_side.facing_direction(landmarks)` (added in the facing-fix work)
  to decide which side is anterior.

## Configuration (all PLACEHOLDER, flagged as such)

| field | value |
|---|---|
| reliability | `primary` (ear/shoulder/hip are reliably visible above the saddle) |
| visibility gate | computed only when ear, shoulder, hip all pass `vis_threshold`, like `neck_forward_angle` |
| unit | new `frac_trunk` (fraction of trunk length; 2-decimal display, like `midline_deviation`) |
| acceptable band | `[-0.10, 0.10]` (symmetric, ideal 0) — placeholder tolerance (widened from ±0.06 after decent sample riders sat at ~0.07 bow) |
| grading | symmetric Gaussian path already in `aggregate._graded_frame_score` (center 0, σ = half-width); no directionality flag |
| weight | `0.5` in `scoring.yaml` (best-effort level), feeds the weakest-link blend |

Band is **symmetric** for v1 (penalizes any deviation from neutral). A forward-only
(asymmetric) penalty is a deliberate pilot-calibration refinement, not a v1 guess.

## Integration points (additive; no change to existing metrics)

| file | change |
|---|---|
| `geometry.py` | add `signed_perpendicular_distance(point, line_a, line_b)` (existing `perpendicular_distance` is unsigned) |
| `angles_side.py` | add `trunk_roundness` to `SIDE_METRICS`; compute in `compute_side` from ear/shoulder/hip + `facing_direction` sign, visibility-gated |
| `config/thresholds.yaml` | new `trunk_roundness` entry (band, unit, reliability, PLACEHOLDER basis) |
| `config/scoring.yaml` | `trunk_roundness: 0.5` weight |
| `config.py` | add `frac_trunk` to `_UNIT_SUFFIX`; include it in the 2-decimal `format_range` branch |
| `docs/ANGLE_DEFINITIONS.md` | one row under "Side view — sagittal plane" |
| tests | `test_angles_side` (straight→~0 in-range; forward-rounded→positive, out-of-range, drops score); `test_geometry` (sign of `signed_perpendicular_distance`) |

Metrics table + status chip render automatically (`ui.metrics_table` iterates all
metrics). Aggregation/scoring need no change — `aggregate_metric` already produces
`graded_score` and `overall_from_breakdown` already blends toward the worst joint.

## Honesty framing (carried into basis notes + docs)

- It's a **PLACEHOLDER proxy**, not a validated measurement.
- **Correlated with `neck_forward_angle`** (both derive from ear–shoulder–hip) → partial
  double-count; the deliberately low `0.5` weight limits how much it moves the score.
- It does **not** measure true thoracic kyphosis — no spine landmark exists; it only
  captures the ear–shoulder–hip bow.
- Tolerance and weight need pilot calibration before any clinical use.

## Out of scope (v1)

- ~~Goniometer overlay visualization of roundness~~ — **added 2026-07-14**: on the
  side view the overlay now draws a faint ear→hip "straight spine" chord plus a
  status-colored connector showing the shoulder's bow off it, with a `frac_trunk`
  label (under the Reference-lines / Labels toggles), mirroring the front-view
  `midline_deviation` indicator. See `overlay.build_overlay_spec`.
- Body-chart *schematic* visualization of roundness (the abstracted stick figure).
- Forward-only / asymmetric band (pilot refinement).
- Front-view analogue.

## Verification

`pytest` green including the two new failing-first tests; then reproduce on a real
side photo (ideally the rounded-back one, once landmarks are confirmed correct) and
confirm the overall score drops relative to a straight-backed rider. If the rounded
photo's landmarks turn out to be contaminated by the handler (hypothesis H1 from the
debugging session), fix detection first — this proxy assumes correct ear/shoulder/hip.
