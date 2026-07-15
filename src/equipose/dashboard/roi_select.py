"""First-frame ROI picker — locks pose estimation onto the child rider.

A draggable box needs an extra Streamlit component; for the pilot build we use
four numeric bounds with a live preview overlay, which is dependency-free and
good enough to seed RoiTracker.
"""
from __future__ import annotations

import numpy as np

from equipose.roi import Bbox


def first_frame_bgr(video_path: str) -> np.ndarray | None:
    import cv2

    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def select_bbox(video_path: str) -> Bbox:
    import cv2
    import streamlit as st

    frame = first_frame_bgr(video_path)
    if frame is None:
        st.error("Could not read the first frame of this video.")
        return (0, 0, 100, 100)
    h, w = frame.shape[:2]
    st.caption("Box the child rider so pose estimation ignores side-walkers/handlers.")
    c1, c2, c3, c4 = st.columns(4)
    left = int(c1.number_input("left", 0, w, int(w * 0.40)))
    top = int(c2.number_input("top", 0, h, int(h * 0.20)))
    right = int(c3.number_input("right", 0, w, int(w * 0.60)))
    bottom = int(c4.number_input("bottom", 0, h, int(h * 0.85)))
    preview = frame.copy()
    cv2.rectangle(preview, (left, top), (right, bottom), (0, 255, 0), 3)
    st.image(preview[:, :, ::-1], caption="ROI preview", width="stretch")
    return (left, top, max(left + 1, right), max(top + 1, bottom))


def select_bbox_image(image_bgr) -> Bbox:
    """ROI picker for a single uploaded image (defaults to the full frame)."""
    import cv2
    import streamlit as st

    h, w = image_bgr.shape[:2]
    st.caption("Box the rider so pose estimation ignores other people. Defaults to the full image.")
    c1, c2, c3, c4 = st.columns(4)
    left = int(c1.number_input("left", 0, w, 0, key="img_l"))
    top = int(c2.number_input("top", 0, h, 0, key="img_t"))
    right = max(left + 1, int(c3.number_input("right", 0, w, w, key="img_r")))
    bottom = max(top + 1, int(c4.number_input("bottom", 0, h, h, key="img_b")))
    preview = image_bgr.copy()
    cv2.rectangle(preview, (left, top), (right, bottom), (0, 255, 0), max(2, round(w / 200)))
    st.image(preview[:, :, ::-1], caption="ROI preview", width="stretch")
    return (left, top, right, bottom)
