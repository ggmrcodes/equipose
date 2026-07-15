# Posture Metric Definitions

> **Limitation — read first.** Every metric below is a **2D projective
> approximation** of a true 3D anatomical angle, measured in the image plane of
> a single camera. It is valid only under `SETUP_PROTOCOL.md` (perpendicular
> optical axis, fixed height, full-body framing, minimal out-of-plane rotation).
> Out-of-plane rotation introduces error that **cannot** be corrected from one
> view. These are screening/tracking signals, not goniometer replacements.

Reliability tiers:
- **PRIMARY** — uses head/shoulder/trunk landmarks, reliably visible above the
  saddle. Drives the session score.
- **BEST-EFFORT** — uses pelvis/hip/knee landmarks, heavily occluded by the
  saddle/horse/side-walkers. Computed only when landmark confidence ≥ the
  visibility threshold; otherwise skipped for that frame and flagged.

## Front view — coronal plane

| Metric | Tier | Definition (landmarks → geometry) | Unit |
|---|---|---|---|
| `head_tilt` | primary | tilt of the **ear–ear** line from horizontal (fallback eye–eye) | deg, 0 = level |
| `shoulder_tilt` | primary | tilt of the **shoulder–shoulder** line from horizontal | deg, 0 = level |
| `trunk_lateral_lean` | primary | tilt of **mid-shoulder → mid-hip** from vertical (fallback nose → mid-shoulder) | deg, 0 = plumb |
| `pelvic_obliquity` | best-effort | tilt of the **hip–hip** line from horizontal | deg, 0 = level |
| `midline_deviation` | primary | perpendicular distance of **nose** from the mid-shoulder→mid-hip axis, normalized by shoulder width | fraction (scale-invariant) |
| `symmetry_score` | primary | composite: 100 − (\|head_tilt\| + \|shoulder_tilt\| + \|midline_deviation\|·100) | score 0–100 |

## Side view — sagittal plane
The camera-facing side is auto-selected as the higher mean-confidence side.

| Metric | Tier | Definition | Unit |
|---|---|---|---|
| `forward_trunk_lean` | primary | tilt of **shoulder → hip** from vertical (fallback ear → shoulder) | deg, 0 = upright |
| `neck_forward_angle` | primary | angle **ear–shoulder–hip** (smaller = more forward-head) | deg, 180 = stacked |
| `hip_flexion` | best-effort | angle **shoulder–hip–knee** | deg |
| `knee_angle` | best-effort | angle **hip–knee–ankle** | deg |
| `back_roundness` | primary | **bow of the back silhouette off its own top→hip chord**, ÷ chord length (0 = straight, higher = rounded) | fraction |

> `back_roundness` measures thoracic rounding from the rider's **silhouette**
> (`equipose.rounding`, offline segmentation), so it sees the back curve the
> ear–shoulder–hip skeleton cannot. Side **photos** only (segmentation is per-frame
> expensive; video is a follow-up). Returns nothing when it can't segment/measure —
> never a false "good". Threshold is a **placeholder** from a 3-photo spike; needs pilot
> validation. Replaces the removed `trunk_roundness` shoulder-bow proxy.

## Aggregation (per session, per metric)
- `mean`, `std` over valid (non-occluded, smoothed) frames
- `pct_in_range` — fraction of valid frames within the acceptable range
- `max_deviation` — largest distance outside the acceptable range
- `confidence` — mean per-frame landmark confidence
- `n_valid_frames` / `n_total_frames` — coverage

Acceptable ranges live in `config/thresholds.yaml` and are **placeholders** to
be calibrated at the pilot. The composite scaling factors above are likewise
provisional.
