# Kyphosis / back-rounding feasibility spike — REPORT

**Date:** 2026-07-14
**Spike spec:** `2026-07-14-kyphosis-measurement-feasibility-spike-design.md`
**Verdict: GO** (with caveats) — the back-silhouette curvature approach robustly
separates the rounded child from straighter riders on the real photos, fully offline.

## What was tested

Pipeline (throwaway scripts, not production): ROI crop → **selfie segmentation**
(offline) → posterior torso edge between shoulder & hip → **bow of the back contour
off its own top→bottom chord**, normalized by the back-chord length = the rounding
index.

Segmentation: MediaPipe **`ImageSegmenter`** with the **selfie_segmenter** tflite
(~250 KB, `output_category_mask=True` → uint8 mask). This reads cleanly. (Two dead
ends found: the legacy `solutions.pose`/`selfie_segmentation` APIs are **removed** in
mediapipe 0.10.35, and `PoseLandmarker`'s built-in segmentation mask **hard-crashes**
on `numpy_view()` — a channel-size assertion. So the bundled pose model can't supply
the mask; a dedicated segmenter model is required.)

## Results

Rounding index (higher = more rounded):

| photo | index | robustness over 7 bbox jitters (min–max) |
|---|---|---|
| `rounded_photo.jpg` (visibly hunched) | **0.187** | **0.114 – 0.212** |
| `S__83239357.jpg` (straighter) | 0.005 | 0.005 – 0.077 |
| `S__83239363.jpg` (straighter) | 0.045 | 0.045 – 0.093 |

**The rounded min (0.114) exceeds both straight maxes (0.077, 0.093)** — a clean,
non-overlapping gap (~0.09 vs ~0.11) that survives ±15–20 px bbox jitter.

## Key findings

1. **Segmentation works even backlit.** The near-silhouette child was cleanly
   segmented and the mask **visibly shows the rounded C-curve** the skeleton can't —
   the exact signal we needed. (Overlays generated during the spike.)
2. **The measure matters.** Sagitta off the shoulder→hip **joint** line does NOT
   separate (it includes torso thickness → straight357 scored *higher* than rounded).
   Sagitta off the back contour's **own** chord DOES — it isolates curvature from
   thickness. This is the core design lesson for the build.
3. **Handler/horse overlap was avoidable here** by bounding the contour to the
   shoulder→hip vertical extent + an x-window around the trunk. The handler bled into
   the mask lower down but not in the measured region.

## Caveats / risks (must carry into any build)

- **Tiny sample.** 1 rounded + 2 straight. The clean separation is encouraging, not
  validated. Needs more photos (esp. more rounded riders + borderline cases).
- **New model dependency.** selfie_segmenter tflite (~250 KB) must be **bundled**
  offline (fits the no-CDN constraint; downloaded once). Confirm license (expected
  Apache-2.0 for MediaPipe models) before shipping.
- **Overlap not guaranteed.** On photos where the handler overlaps the *torso* region,
  the back edge could be contaminated. Needs a robustness pass on more cases.
- **Uncalibrated.** The ~0.10 separating threshold is from 3 photos, not clinical data.
  Absolute severity still needs pilot ground truth.
- **Backlight worked here but isn't guaranteed** across lighting conditions.

## Recommendation

**Proceed to a build spec** for a real `back_roundness` (kyphosis) metric using
selfie-segmentation back-contour curvature, to **replace** the failed `trunk_roundness`
shoulder-bow proxy. The build spec should cover: bundling + license of the segmenter
model, the contour/measure implementation, a bigger validation set, a provisional
threshold + honest "needs pilot calibration" framing, and how it lands in the pipeline
(new backend step, schema, config, overlay).

## Interim safety (unchanged, still open)

`trunk_roundness` remains in place and still reports a confident **"good"** on rounded
subjects — a false negative. It should be replaced by (or gated behind) the new metric,
or reframed/removed, as soon as the build lands.
