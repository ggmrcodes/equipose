# Spec: Digital Goniometer Overlay (photo path)

**Date:** 2026-06-21  **Status:** approved design, pending spec review
**Scope:** the single-photo ("snapshot") path only. Degrees-only v1.

## Context

equipose's photo path currently runs pose estimation on one still and shows a
status-colored skeleton, a score, a body-chart, and a metrics table. That is a
competent measurement view but it does not match what physiotherapists actually
do with a posture photo: lay a goniometer on it to read joint angles, drop
plumb/grid lines to see lean, and read the numbers off the image itself.

This feature turns the photo into a **digital goniometer + posture grid**: angle
arcs with degree readouts drawn at each measured joint, plumb and horizontal
reference lines, the colored skeleton underneath, each layer independently
toggleable. It replaces the "print the photo, lay a physical goniometer on it"
workflow with an on-screen, exact, repeatable one.

### Decisions locked with the user
1. **Degrees only in v1.** No real-world (cm) scale calibration. Angles in
   degrees plus the existing normalized midline ratio. (cm calibration is a
   deferred follow-up.)
2. **Overlay layers:** angle arcs + degree labels, plumb + horizontal reference
   lines, the status-colored skeleton, and an **independent toggle per layer**.
3. **Render strategy: hybrid, one shared geometry source** (Approach C). A single
   `build_overlay_spec` computes primitives in image-pixel space; an SVG renderer
   draws the crisp on-screen overlay and a cv2 renderer draws the face-blurred
   PNG download. No fragile rasterization dependency; no duplicated math.

### Non-goals (v1)
cm/marker scale calibration; per-frame overlays on video; editable/draggable
landmarks; the one-page assessment PDF. Each is a separate future feature.

## Architecture

### New module: `src/equipose/dashboard/overlay.py`
Single responsibility: turn `(landmarks, view, metrics, layers)` into drawable
primitives, and render them two ways. Pure geometry + rendering, no Streamlit.

**Primitive dataclasses** (image-pixel coordinates):
- `Bone(p1, p2, color, width)`
- `Joint(p, color, r)`
- `Ref(p1, p2, color)`  (reference line, drawn dashed/faint)
- `Arc(cx, cy, r, a0_deg, a1_deg, color, width)`
- `Label(x, y, text, color, anchor)`

**`OverlaySpec`**: grouped lists `bones, joints, refs, arcs, labels`. Only the
groups whose layer is enabled are populated.

**`LAYERS = ("skeleton", "reference", "arcs", "labels")`**

**`build_overlay_spec(landmarks, view, metrics, layers, vis_threshold=0.3) -> OverlaySpec`**
- Index landmarks by name; pick camera-facing side for `view == "side"` via the
  existing `angles_side.pick_side`.
- **skeleton** layer: bones + joints for detected landmarks, status palette
  consistent with the body-chart (`glyphs.GOOD/CONCERN`); ghost/skip below
  `vis_threshold` exactly as `viz.draw_skeleton` does today.
- **reference** layer:
  - front: plumb vertical through hip-midpoint; horizontals through the shoulder
    line and the hip line.
  - side: plumb vertical through the shoulder; horizontal through the hip.
  - faint warm line color, drawn dashed.
- **arcs** layer: one arc per measured angle metric (skip metrics whose status is
  `none`/occluded, and skip composite scores `symmetry_score`,
  `sitting_alignment_index`). Helper `arc_between(vertex, ray1_deg, ray2_deg, r)`
  spans the interior angle; color = metric status.
  - Joint angles (arc at the vertex between two segments):
    `neck_forward_angle` at shoulder (ear, hip); `hip_flexion` at hip
    (shoulder, knee); `knee_angle` at knee (hip, ankle).
  - Tilt angles (arc between a reference axis and the segment):
    `head_tilt` (ear-ear vs horizontal), `shoulder_tilt` (shoulder line vs
    horizontal), `pelvic_obliquity` (hip line vs horizontal),
    `forward_trunk_lean` (shoulder->hip vs vertical), `trunk_lateral_lean`
    (shoulder-mid->hip-mid vs vertical).
  - `midline_deviation` is a distance ratio, not an angle: draw a short connector
    from the nose to the shoulder-hip axis (reference layer) and label the ratio;
    no arc.
- **labels** layer: degree text per arc placed along the bisector at
  `r + offset`, formatted `f"{value:.0f}°"`; midline ratio labeled `f"{v:.2f}w"`.
  Each label carries a semi-opaque dark pill background for legibility over the
  photo.
- Sizing: arc radius and stroke widths scale by image width.

**`overlay_svg(spec, w, h, image_data_uri) -> str`**
HTML: a positioned wrapper containing the photo as the base
(`<img>` at 100% width) and an absolutely-positioned
`<svg viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid meet">` on top, so
primitive coordinates (image pixels) map exactly at any display size. Arcs via
`glyphs._arc`/`_pol`; labels in JetBrains Mono with `<rect>` backings.

**`overlay_raster(img_bgr, spec) -> np.ndarray`**
cv2 draws the same primitives onto a copy for the face-blurred download: arcs via
`cv2.ellipse`, lines via `cv2.line` (dashed for refs), dots via `cv2.circle`,
labels via `cv2.putText` with a filled-rect backing. (Export labels use cv2's
font; the on-screen view uses JetBrains Mono.)

### Reuse
`geometry` (angle math, `line_angle_*`), `glyphs._arc`/`_pol` + palette
(`GOOD/CONCERN/GHOST/SOFT/LINE`), the landmark sets in
`angles_front`/`angles_side` (+ `pick_side`), `viz` skeleton edge topology,
`privacy.blur_faces`. No new third-party dependency.

### Flow change: `src/equipose/dashboard/flow.py`
- `_run_photo` stores in `eq_result` the **raw image** (`image_rgb` numpy) +
  **landmarks** (`list[Landmark]`) + `view` + `report`, instead of the
  pre-annotated image and blurred PNG. (Re-rendering on toggle is a cheap
  Streamlit rerun.)
- `_step_read` photo branch:
  - A row of four `st.checkbox` toggles: Arcs / Reference lines / Skeleton /
    Labels (default all on).
  - `build_overlay_spec(...layers...)` -> `overlay_svg(...)` -> `st.markdown`
    (base image embedded as a base64 data URI; on-screen image stays unblurred,
    a local clinician view, as today).
  - Download button: `overlay_raster(blur_faces(raw_bgr), spec)` ->
    `cv2.imencode(".png")` -> `st.download_button` (export stays face-blurred).
  - Body-chart (`posture_panel`) and metrics table remain below, unchanged.
- Video branch unchanged.

## Data flow
```
photo -> analyze_image -> (report, landmarks)        [stored raw image + landmarks]
read step: toggles -> build_overlay_spec(landmarks, view, report.metrics, layers)
   -> overlay_svg(spec, w, h, dataURI(raw))    -> on-screen goniometer
   -> overlay_raster(blur_faces(raw), spec)    -> face-blurred PNG download
```

## Testing (`tests/test_overlay.py`)
1. **Spec content (side):** synthetic landmarks with all sagittal metrics
   detected -> spec has an arc per joint/tilt angle metric (composites excluded),
   labels count == arcs count, >=1 reference line.
2. **Occlusion:** omit `knee_angle` landmarks (low confidence) -> no knee arc; the
   detected metrics still produce arcs.
3. **Layer toggles:** `layers` without `"arcs"` -> `spec.arcs == []`; without
   `"reference"` -> `spec.refs == []`.
4. **SVG render:** `overlay_svg` returns a string containing `<svg`, `viewBox`,
   the base `data:image` URI, and a `°` label.
5. **Raster render:** `overlay_raster(np.zeros((H,W,3)), spec)` returns an ndarray
   of shape `(H,W,3)` without error.
6. **Front mapping:** front synthetic landmarks -> arcs for head/shoulder/pelvic
   tilt + trunk lean; `midline_deviation` produces a connector + ratio label, not
   an arc.

## Risks & mitigations
- **Label clutter over a busy photo.** Pill backings + skip occluded metrics +
  per-layer toggles; Labels can be turned off for a clean view.
- **Very small tilt angles (e.g., 2 deg) hard to see.** Always draw the reference
  axis so the deviation reads even when the arc is tiny; the label carries the
  exact value.
- **Phone EXIF rotation.** `cv2.imdecode` ignores EXIF, so a rotated phone photo
  could be sideways. Out of scope for v1; note as a known limitation and handle
  orientation in a later pass.
- **Inline base64 image per rerun.** Acceptable for a local single-user app;
  revisit (static-serve the frame) only if it becomes sluggish.

## Verification
`pytest` green (incl. new `test_overlay.py`); restart server; drive a side photo
with a real ROI; confirm arcs land on the joints, labels are legible, toggles
hide/show layers, and the face-blurred download contains the overlay. Iterate arc
radius/label placement via browse screenshots.
