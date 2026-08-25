"""Health checks for API, catalog, and vector store."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from settings import CATALOG_FILE, CHROMA_DIR


@dataclass
class HealthReport:
    ok: bool
    api_key_set: bool
    catalog_books: int = 0
    rag_chunks: int = 0
    chroma_exists: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "api_key_set": self.api_key_set,
            "catalog_books": self.catalog_books,
            "rag_chunks": self.rag_chunks,
            "chroma_exists": self.chroma_exists,
            "errors": self.errors,
        }


def check_health(*, user_api_key: str | None = None) -> HealthReport:
    report = HealthReport(
        ok=True,
        api_key_set=bool((user_api_key or "").strip() or os.getenv("GEMINI_API_KEY")),
    )

    if not report.api_key_set:
        report.errors.append("GEMINI_API_KEY missing in .env")
        report.ok = False

    report.chroma_exists = CHROMA_DIR.exists()
    if CATALOG_FILE.exists():
        try:
            import json
            cat = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
            report.catalog_books = cat.get("count", len(cat.get("entries", [])))
        except Exception as exc:
            report.errors.append(f"Catalog corrupt: {exc}")
    else:
        report.errors.append("Catalog not built — run scripts/build_catalog.py")

    if report.chroma_exists:
        try:
            from src.ingest.build_store import get_collection_count
            report.rag_chunks = get_collection_count()
        except Exception as exc:
            report.errors.append(f"ChromaDB error: {exc}")
    else:
        report.errors.append("RAG index missing — run scripts/build_all.py")

    if report.catalog_books == 0:
        report.ok = False
    return report
