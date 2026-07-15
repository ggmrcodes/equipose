# `back_roundness` — segmentation back-contour kyphosis metric (build)

**Date:** 2026-07-14
**Status:** implemented 2026-07-14 (verified: rounded child → concern/score 47; straight → good)
**Supersedes:** `trunk_roundness` (the shoulder-bow proxy — confirmed unable to detect
thoracic rounding; see the spike report). This metric **replaces** it.

## What it measures

The **bow of the child's back silhouette off its own top→bottom chord**, normalized by
that chord's length. From the spike, this robustly separated a rounded child (index
~0.15) from straighter riders (~0.05), stable under bbox jitter — because it isolates
*curvature* from torso thickness (measuring off the back contour's own endpoints, not
the shoulder→hip joint line).

Higher = more rounded. Ideal = 0 (straight back).

## Architecture

New module **`equipose/rounding.py`**, split for testability (the pose-backend seam
pattern):

- **`back_roundness_from_mask(mask, shoulder, hip, facing) -> Optional[float]`** — PURE.
  Given a binary person mask (crop res) + shoulder/hip points (crop px) + facing
  ("left"/"right"), walks rows shoulder.y→hip.y, takes the posterior mask edge within an
  x-window around the trunk, and returns `max_sagitta / back_chord_len` off the contour's
  own top/bottom chord. Returns `None` if too few contour points. **Fully unit-tested with
  synthetic masks — no model.**
- **`_segment_person(crop_bgr) -> np.ndarray`** — the model seam. Lazily builds a MediaPipe
  `ImageSegmenter` from a bundled tflite, returns a binary mask. Mocked in tests.
- **`back_roundness_index(crop_bgr, landmarks) -> Optional[float]`** — orchestrates:
  `_segment_person` → pick_side/facing → `back_roundness_from_mask`.

**Model:** bundle `models/selfie_segmenter.tflite` (~250 KB, MediaPipe — confirm
Apache-2.0). Lazy-loaded, offline, `output_category_mask=True` (uint8 — the float
`PoseLandmarker` mask read hard-crashes; do NOT use it).

## Pipeline integration

In `pipeline.analyze_image` (the **photo** path): after detecting on the square crop,
compute `back_roundness_index(square, raw_crop_landmarks)` (crop-coord landmarks, same
frame as the mask), and inject the value/confidence into the `values`/`confs` dicts before
aggregation. `back_roundness` joins `SIDE_METRICS`, so `aggregate_metric` picks it up.

**Video (`analyze_session`): not computed** for v1 — per-frame segmentation is expensive
and the project is single-image-first. `back_roundness` will be `None` (excluded) for
video sessions. Noted as a follow-up.

If segmentation fails or the contour is unrecoverable → `None` → the metric is
"not detected" and excluded from the score. This is the honest fallback: **no false
"good."** That is the whole point of replacing `trunk_roundness`.

## Config

`config/thresholds.yaml`:
```
back_roundness:
  acceptable: [0.0, 0.10]      # PLACEHOLDER from the 3-photo spike; needs pilot validation
  unit: frac_back
  reliability: primary
  lower_is_better: true        # ideal = 0 (straight); grading peaks there
  basis: "PLACEHOLDER: bow of the back silhouette off its own chord / chord length ..."
```
`config/scoring.yaml`: `back_roundness: 1.0` (rounding is a primary clinical concern; the
signal is now real, but the threshold is provisional). Feeds the weakest-link blend.

`config.py`: add `frac_back` to `_UNIT_SUFFIX` (" b") + the 2-decimal `format_range`
branch. `ui.py`: add `frac_back` → "b" to `_UNIT_DISP`.

## Remove `trunk_roundness`

Fully: from `SIDE_METRICS` + `compute_side` (`angles_side.py`), `thresholds.yaml`,
`scoring.yaml`, the overlay bow/chord viz + its test (`overlay.py`, `test_overlay.py`),
and `test_angles_side.py`. Keep `geometry.signed_perpendicular_distance` (harmless, tested).

## Tests (TDD)

- `test_rounding.py` (new): `back_roundness_from_mask` on synthetic masks — a straight
  rectangle torso → ~0; a mask with a posterior bulge → clearly higher; too-few-points →
  None; facing left vs right both work.
- Pipeline: `analyze_image` with a **mocked** `_segment_person` returns a `back_roundness`
  metric; segmentation failure → metric excluded (not detected), score unaffected.
- Update the metric-count / config tests that referenced `trunk_roundness`.

## Deferred (follow-up, not this build)

- **Overlay visualization** of `back_roundness` (drawing the segmented back curve on the
  photo) — the overlay renderer has no mask today; needs plumbing. The metric ships in the
  table + score first.
- Video-path computation.
- Calibrating the threshold to clinical severity (needs pilot ground truth).
- Larger validation set (the current basis is 3 photos).

## Honest framing (carried into basis + docs)

Provisional threshold from 3 photos; a real measurement of back *shape* (not a joint
proxy), but not yet clinically validated. When it can't segment/measure, it reports
nothing rather than a false "good."
