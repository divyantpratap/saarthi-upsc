import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.references.catalog import load_catalog, lookup_direct


def test_catalog_loaded():
    cat = load_catalog()
    assert "entries" in cat
    if cat.get("count", 0) > 0:
        hits = lookup_direct("Article 32 constitution", top_k=2)
        assert len(hits) >= 1
