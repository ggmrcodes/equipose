"""Deployment helpers: hosted-mode flag + one-time model provisioning.

The core app is offline: `models/` is gitignored and provided at setup, and there are
no network calls at *runtime* (user data never leaves the box locally). These helpers
let a HOSTED demo self-provision the models on first boot — a one-time fetch of trusted
Google model files when they are missing. On a local run whose models already exist,
`ensure_models` does nothing (no network).

`is_hosted()` (env `EQUIPOSE_HOSTED=1`) flips the app into demo mode: the privacy footer
tells the user images are processed on a server (the local "no data leaves this machine"
claim would be FALSE when hosted), and the pose-backend choice is mediapipe-only.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.request import urlopen

_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

# Public MediaPipe model files (Apache-2.0). MoveNet is intentionally NOT here — the
# hosted demo is mediapipe-only (lighter, faster cold start).
_MODEL_URLS = {
    "pose_landmarker_full.task":
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/latest/pose_landmarker_full.task",
    "selfie_segmenter.tflite":
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
        "selfie_segmenter/float16/latest/selfie_segmenter.tflite",
}
_REQUIRED = ("pose_landmarker_full.task", "selfie_segmenter.tflite")


def is_hosted() -> bool:
    """True when running as a hosted demo (``EQUIPOSE_HOSTED`` truthy).

    Reads the OS env var first, then Streamlit secrets — Streamlit Community Cloud
    exposes its Secrets via ``st.secrets``, NOT as environment variables, so a
    secrets-only value must still flip the demo footer / backend."""
    val = os.environ.get("EQUIPOSE_HOSTED", "")
    if not val:
        try:
            import streamlit as st
            val = str(st.secrets.get("EQUIPOSE_HOSTED", ""))
        except Exception:
            val = ""
    return val.strip().lower() not in ("", "0", "false", "no")


def missing_models(names: tuple[str, ...] = _REQUIRED) -> list[str]:
    return [n for n in names if not (_MODELS_DIR / n).exists() or (_MODELS_DIR / n).stat().st_size == 0]


def ensure_models(names: tuple[str, ...] = _REQUIRED) -> list[str]:
    """Download any missing required models to ``models/`` (one-time). Returns the names
    fetched (empty when all present — the common local case, no network)."""
    _MODELS_DIR.mkdir(exist_ok=True)
    fetched: list[str] = []
    for name in missing_models(names):
        dest = _MODELS_DIR / name
        tmp = dest.with_suffix(dest.suffix + ".part")
        with urlopen(_MODEL_URLS[name], timeout=120) as r, open(tmp, "wb") as f:  # trusted Google host
            f.write(r.read())
        tmp.replace(dest)
        fetched.append(name)
    return fetched
