"""Load Streamlit secrets into the process environment when present."""
from __future__ import annotations

import os


def apply_streamlit_secrets() -> None:
    """Map Streamlit Community Cloud secrets → env vars (local .env still wins if set)."""
    try:
        import streamlit as st
    except ImportError:
        return

    try:
        secrets = st.secrets
    except Exception:
        return

    for key in (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_MODEL_FALLBACK",
        "EMBEDDING_BACKEND",
        "LOG_LEVEL",
        "TOP_K_RAG",
        "RAG_MAX_DISTANCE",
        "MAX_CONTEXT_CHARS",
    ):
        if key in os.environ and os.environ[key]:
            continue
        try:
            value = secrets.get(key, None)
        except Exception:
            value = None
        if value is not None and str(value).strip():
            os.environ[key] = str(value).strip()
