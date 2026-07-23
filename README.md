# equipose

**AI vision posture monitoring for pediatric hippotherapy (cerebral palsy).**

Analyzes the sitting posture of children with CP (GMFCS III) during hippotherapy
on a pony, from **front-view** and **side-view** video. Detects body landmarks,
computes clinically-relevant 2D posture angles, scores each session, and tracks
progress across a 3–6 month therapy period via a Streamlit dashboard.

> ⚠️ **Research build.** All clinical thresholds in `config/` are **placeholders**
> — they were not derived from clinical data and must be calibrated at the pilot.
> Metrics are 2D projective approximations; see `docs/ANGLE_DEFINITIONS.md`.
> This is a screening/tracking aid, **not** a diagnostic device.

## Why these design choices
- **MediaPipe Pose** (default backend) — 33 landmarks with per-joint visibility
  (the occlusion signal), single-person, CPU real-time. **MoveNet ONNX** is a
  drop-in fallback that needs no MediaPipe.
- **Trunk/upper-body first.** On a pony the pelvis/hips/knees are occluded by the
  saddle/horse/side-walkers, so those metrics are *best-effort* (computed only
  when visible, flagged otherwise); head/shoulder/trunk metrics are *primary*
  and drive the score.
- **ROI tracking** locks pose onto the child so a single-person model ignores
  handlers and side-walkers.
- **Front and side analyzed independently** (no hardware sync).

## Setup (Python 3.11 — NOT 3.13; MediaPipe has no 3.13 wheels)

```bash
cd equipose
/opt/homebrew/bin/python3.11 -m venv .venv
./.venv/bin/pip install -e ".[dev]"

# Models (already provided in models/ in this build):
#   models/pose_landmarker_full.task              (MediaPipe)
#   models/movenet_singlepose_thunder_4.onnx      (MoveNet fallback)
#   models/selfie_segmenter.tflite                (back_roundness silhouette; Apache-2.0)
# Fetch the segmenter once (offline thereafter):
#   curl -L -o models/selfie_segmenter.tflite \
#     https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite
```

## Run

```bash
# Dashboard (patients, run session, progress trends)
./.venv/bin/streamlit run src/equipose/dashboard/app.py

# One-shot CLI on a video
./.venv/bin/equipose --video front.mp4 --view front --patient P001 \
    --bbox 655,180,905,690 --backend mediapipe

# Tests
./.venv/bin/pytest
```

## Layout
```
src/equipose/
  geometry.py            2D math primitives (angles, distances, tilts)
  schemas.py             Pydantic data contracts
  config.py              YAML threshold/scoring loaders
  pose_backend/          swappable backends: mediapipe (default), movenet
  roi.py                 child-rider ROI crop + tracker
  quality.py             blur/luma QC + occlusion (visibility) gate
  angles_front.py        coronal metrics      angles_side.py  sagittal metrics
  smoothing.py           OneEuro temporal filter + gap handling
  video.py               offline frame iterator
  aggregate.py           per-metric session stats     scoring.py  0-100 + bands
  persistence.py         SQLite (patients/sessions/metrics/labels)
  export_csv.py / export_pdf.py / privacy.py / labeling.py
  pipeline.py            orchestrator: video(view) -> SessionReport
  dashboard/             Streamlit app
config/                  thresholds.yaml, scoring.yaml  (PLACEHOLDERS)
docs/                    SETUP_PROTOCOL, ANGLE_DEFINITIONS, PRIVACY
```

