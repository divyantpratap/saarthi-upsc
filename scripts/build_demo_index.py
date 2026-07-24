"""Build a tiny public demo index from bundled study notes (no copyrighted PDFs)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

# Prefer Gemini embeddings for the hosted demo (no PyTorch on Streamlit Cloud).
os.environ.setdefault("EMBEDDING_BACKEND", "gemini")

from settings import CHROMA_DIR, DATA_DIR
from src.core.secrets import apply_streamlit_secrets
from src.ingest.build_store import get_chroma_collection, index_documents, load_text_files


def build_demo_index(reset: bool = True) -> int:
    apply_streamlit_secrets()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY required to build the demo index with Gemini embeddings.")

    notes_dir = DATA_DIR
    docs = load_text_files(notes_dir)
    if not docs:
        raise SystemExit(f"No .txt notes found under {notes_dir}")

    collection = get_chroma_collection(reset=reset)
    n = index_documents(collection, docs, "demo notes")
    print(f"Demo index ready at {CHROMA_DIR} ({collection.count()} chunks, added {n})")
    return collection.count()


if __name__ == "__main__":
    build_demo_index(reset=True)
