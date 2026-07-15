"""Streamlit entry point — "warm night clinic" guided single-flow.

Run:  streamlit run src/equipose/dashboard/app.py
"""
from __future__ import annotations

from pathlib import Path

from equipose.dashboard import flow, ui
from equipose.persistence import Store

_DATA_DIR = Path.cwd() / "data"
_DB_PATH = _DATA_DIR / "equipose.sqlite"


def get_store() -> Store:
    _DATA_DIR.mkdir(exist_ok=True)
    return Store(_DB_PATH)


def main() -> None:
    import streamlit as st

    from equipose import deploy

    st.set_page_config(page_title="equipose", layout="wide",
                       initial_sidebar_state="expanded")
    # Hosted demo self-provisions the models on first boot; no-op (no network) locally.
    if deploy.missing_models():
        with st.spinner("First-time setup: downloading models…"):
            deploy.ensure_models()
    ui.inject_theme()
    store = get_store()
    flow.render(store)


if __name__ == "__main__":
    main()
