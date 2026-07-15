# Camera Setup Protocol (REQUIRED for valid measurements)

equipose computes **2D in-image-plane angles**. They are only meaningful if the
camera geometry is controlled. Treat this protocol as a hard prerequisite for
every recording session.

## Two independent cameras

Front and side videos are analyzed **separately** (no time-sync needed). Record
two clips per session — one from the front, one from the side.

### Front camera (coronal plane → tilt/lean/symmetry)
- Placed **directly in front** of the rider's line of travel, optical axis
  perpendicular to the pony's direction of motion at the measurement zone.
- Height ≈ the **child's trunk/chest level** when seated.
- Frame the **whole child** (head to feet/stirrups) with margin; avoid cutting
  off the head or hips.

### Side camera (sagittal plane → trunk/neck/hip/knee)
- Placed **perpendicular to the side** of the pony at the measurement zone.
- Same height guidance (child trunk level).
- Capture the camera-facing side of the body fully; the rider should pass
  through a zone where the optical axis is square to their sagittal plane.

## General requirements
- **Tripod, fixed position.** No panning/zooming during the measurement window.
- Good, even lighting; avoid strong backlight (the QC gate rejects dark/blurry
  frames).
- Keep **side-walkers/handlers** as clear of the rider's silhouette as possible.
  The operator boxes the child on the first frame; the tracker follows, but
  heavy overlap still degrades landmark confidence.
- Record at a steady frame rate (≥24 fps). Note the rate; it is read from the
  file automatically.
- A short, slow, straight pass through the measurement zone yields the cleanest
  data (least out-of-plane rotation).

## What breaks the measurement
- Oblique camera angles (not perpendicular) → systematic angle error.
- Camera too high/low → foreshortening of trunk/limb segments.
- Rider turning (out-of-plane rotation) → 2D angles diverge from anatomy.
- Loose clothing obscuring hip/knee → best-effort metrics drop out.
