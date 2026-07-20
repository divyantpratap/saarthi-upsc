"""Step 1: catalog (fast). Step 2: RAG index (slower, per-PDF)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.references.catalog import build_catalog
from src.ingest.build_store import build_vector_store

if __name__ == "__main__":
    print("STEP 1/2 — Reference catalog (one-shot lookups)\n")
    build_catalog()
    print("\nSTEP 2/2 — RAG vector index (deep queries)\n")
    n = build_vector_store(reset=True)
    print(f"\nAll done. Indexed {n} chunk operations.")
