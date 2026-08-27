"""Configuration used only by the offline index pipeline."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

MAX_PAGES_FULL = int(os.getenv("MAX_PAGES_FULL", "150"))
MAX_PAGES_PREVIEW = int(os.getenv("MAX_PAGES_PREVIEW", "8"))
MIN_CHARS_PER_PDF = int(os.getenv("MIN_CHARS_PER_PDF", "200"))

GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
