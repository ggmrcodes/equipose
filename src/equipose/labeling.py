"""Therapist labeling sink — collects labels for FUTURE ML training.

This build only STORES labels; no model consumes them yet (out of scope).
"""
from __future__ import annotations

from equipose.persistence import Store

# Therapist label vocabulary (from the project brief, Phase 6).
LABELS = (
    "good_posture",
    "lean_left",
    "lean_right",
    "forward_collapse",
    "unstable",
)


def store_label(store: Store, session_id: str, frame_idx: int, label: str,
                therapist_id: str, created_at: str) -> None:
    if label not in LABELS:
        raise ValueError(f"unknown label {label!r}; expected one of {LABELS}")
    store.add_label(session_id, frame_idx, label, therapist_id, created_at)
