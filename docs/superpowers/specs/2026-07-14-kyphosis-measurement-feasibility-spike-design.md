# Measuring back rounding (kyphosis) from a side photo — feasibility spike

**Date:** 2026-07-14
**Status:** scoped — feasibility spike, not a build
**Type:** research / go-no-go

## Why

`trunk_roundness` (the signed shoulder-bow proxy) was confirmed **structurally unable**
to detect thoracic rounding. On the real target photo (`sample/rounded_photo.jpg`), a
visibly, severely hunched child was scored **"good"** (bow −0.06, graded 0.86):

- Detection was correct — ear (694,143) → shoulder (728,225) → hip (753,447), all
  conf 1.00, all on the child (left of the handler at x>830). **Not** a landmark bug.
- Those three surface points are **nearly collinear** (neck angle 164°) because the
  kyphotic curve lives in the **thoracic spine, between the shoulder and hip**, where
  MediaPipe has **no landmark**. Ear/shoulder/hip cannot encode a curve that bends
  between them.

This is a measurement-*instrument* limitation, not a tuning problem. A metric that
reports a confident "good" on a rounded child is a **false negative on a screening
tool** — the most dangerous failure mode, and a direct violation of the project's
honest-restraint principle. Real capability requires a signal the skeleton doesn't
carry. This spike decides whether that signal is obtainable under the real capture
conditions before anything is built.

## Goal / success criterion

A single, testable question:

> Can we compute a rounding index that ranks `sample/rounded_photo.jpg` (visibly
> rounded) **clearly worse** than the straighter side riders (`S__83239357.jpg`,
> `S__83239363.jpg`), **robustly** (stable under ROI-bbox jitter), on the **real,
> backlit, occluded photos** — fully offline?

If yes → go, write a build spec. If no → no-go, fall back to fixing
`trunk_roundness`'s false-reassurance (remove or reframe).

## Primary approach: back-silhouette curvature (segmentation)

Measure the *shape of the back*, which the skeleton can't:

1. **Segment the rider** inside the operator's ROI bbox using an offline segmentation
   model (candidate: MediaPipe Selfie Segmentation — a bundled `.tflite`, no network;
   verify availability + license during the spike). Produce a person mask in the ROI.
2. **Extract the posterior torso contour** — the back edge of the trunk between shoulder
   and hip level. Use the existing pose landmarks (ear/shoulder/hip) to bound the
   vertical extent and `angles_side.facing_direction` to identify which side is
   posterior.
3. **Fit a smooth curve** (quadratic/cubic or spline) to those contour points in the
   trunk's local frame (shoulder→hip as one axis).
4. **Curvature index** = the max perpendicular deviation of the contour from the
   shoulder→hip chord (sagitta), normalized by trunk length — or a Cobb-like angle from
   the fitted curve's end tangents. Posterior bulge = rounding.

**Crux risks (what the spike must confront on the real photos):**

- **Occlusion overlap.** The handler is pressed against the child and the horse is
  behind — segmentation may merge them. Isolating the *child's* back contour may be
  unresolvable. Mitigation to try: constrain to the ROI + seed/verify the mask region
  with the pose landmarks. May still fail.
- **Backlighting.** `rounded_photo.jpg` is strongly backlit; the child is near-silhouette
  and may merge with the horse/background. Segmentation quality is the single biggest
  unknown.
- **Clothing bulk.** The polo/vest contour is not the spine; it adds noise.
- **No ground truth.** There is no clinician-rated or goniometer kyphosis value, so any
  index is uncalibrated — the spike judges *separation/ranking*, not absolute accuracy.

## Fallback (surveyed, not built): spine-capable keypoint model

Time-boxed survey during the spike: is there an **offline, license-clean** pose/posture
model that emits reliable thoracic/spine keypoints (→ a direct kyphosis angle)? Record
what exists and whether it's usable on children-on-horses. If a viable one is found,
note it as an alternative build path; if not, record the dead-end. Do **not** integrate
during the spike.

## The spike

1. Build a throwaway script (not production code) over the existing pipeline: for each
   sample photo, run ROI crop → segmentation → posterior-contour extraction → curve fit
   → curvature index. Reuse `RoiTracker`, the pose landmarks, and `facing_direction`.
2. Render overlays (segmentation mask + fitted back curve + index) on each real photo
   for visual inspection.
3. Compute the index for the rounded photo and the straighter ones; test robustness to
   ±10–20 px bbox jitter.
4. Run the fallback model survey.

## Deliverables

- A **spike report** (findings + a clear go/no-go recommendation).
- Sample overlay images (mask + fitted curve + index) on the real photos.
- If **go**: a follow-up build spec (production metric, config, honest calibration plan).
- If **no-go**: a recommendation to remove or reframe `trunk_roundness`.

## Interim safety risk (open)

`trunk_roundness` is being **left in place as-is** during this spike (user's call). It
still shows a confident "good" on rounded subjects — a known false-negative risk. This
must be revisited the moment the spike resolves: either replaced by a working signal, or
reframed/removed so it stops falsely reassuring.

## Out of scope (this spike)

- Any production implementation, config, schema, or UI change.
- Calibrating the index to clinical severity (needs pilot ground truth).
- Front-view / video.
- 3D reconstruction.
