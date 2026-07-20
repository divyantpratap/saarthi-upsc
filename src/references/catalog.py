"""One-shot reference catalog: fast BM25 lookup over PDF previews."""
from __future__ import annotations

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from settings import CATALOG_FILE, PDF_DIR, REFERENCES_DIR
from src.ingest.pdf_parser import _guess_subject, list_pdfs, pdf_preview

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _load_note_entries() -> list[dict]:
    from settings import DATA_DIR

    entries = []
    for txt in sorted(DATA_DIR.glob("*.txt")):
        if txt.name == "sample_urls.txt":
            continue
        text = txt.read_text(encoding="utf-8")
        if len(text.strip()) < 50:
            continue
        entries.append(
            {
                "filename": txt.name,
                "subject": "Notes",
                "source": f"notes:{txt.name}",
                "preview": text[:12000],
                "keywords": f"notes polity {txt.stem}".lower(),
            }
        )
    return entries


def build_catalog(force: bool = False) -> dict:
    """Build JSON catalog from PDF folder (preview text per book)."""
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = list_pdfs()
    entries = _load_note_entries()

    print(f"Building reference catalog for {len(pdfs)} PDFs...")
    for path in pdfs:
        preview = pdf_preview(path)
        if len(preview.strip()) < 100:
            print(f"  [skip empty] {path.name}")
            continue
        try:
            display_name = str(path.relative_to(PDF_DIR))
        except ValueError:
            display_name = path.name
        subject = _guess_subject(display_name)
        entries.append(
            {
                "filename": display_name,
                "subject": subject,
                "source": f"pdf:{display_name}",
                "preview": preview[:12000],
                "keywords": f"{subject} {display_name}".lower(),
            }
        )
        print(f"  + {display_name} [{subject}]")

    catalog = {"version": 1, "count": len(entries), "entries": entries}
    CATALOG_FILE.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Catalog saved: {CATALOG_FILE} ({len(entries)} books)")
    return catalog


def load_catalog() -> dict:
    if not CATALOG_FILE.exists():
        return {"entries": []}
    return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))


def lookup_direct(query: str, top_k: int = 3) -> list[dict]:
    """BM25 over catalog previews — instant reference pick for direct Qs."""
    catalog = load_catalog()
    entries = catalog.get("entries", [])
    if not entries:
        return []

    corpus = [
        _tokenize(e["preview"] + " " + e.get("keywords", "") + " " + e["filename"])
        for e in entries
    ]
    bm25 = BM25Okapi(corpus)
    q_tokens = _tokenize(query)
    scores = list(bm25.get_scores(q_tokens))
    # Boost subject/filename matches (e.g. "article" -> Polity books)
    for i, e in enumerate(entries):
        blob = (e["subject"] + " " + e["filename"] + " " + e.get("keywords", "")).lower()
        overlap = sum(1 for t in q_tokens if t in blob and len(t) > 3)
        scores[i] += overlap * 0.8
    ranked = sorted(zip(entries, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {
            "source": e["source"],
            "filename": e["filename"],
            "subject": e["subject"],
            "text": e["preview"],
            "score": float(s),
        }
        for e, s in ranked
        if s > 0
    ]
