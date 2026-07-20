import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.references.catalog import load_catalog
from src.ingest.build_store import get_chroma_collection

cat = load_catalog()
print("Catalog books:", cat.get("count", 0))
for e in cat.get("entries", [])[:5]:
    print(f"  - {e['filename']} [{e['subject']}]")
if len(cat.get("entries", [])) > 5:
    print(f"  ... and {len(cat['entries']) - 5} more")

try:
    c = get_chroma_collection(reset=False)
    print("RAG chunks:", c.count())
except Exception as ex:
    print("RAG chunks: 0 (", ex, ")")
