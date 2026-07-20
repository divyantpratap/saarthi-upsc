"""Retrieve and filter chunks from ChromaDB."""
from __future__ import annotations

from functools import lru_cache

from settings import RAG_MAX_DISTANCE, TOP_K_RAG
from src.core.logging_config import log
from src.ingest.build_store import get_chroma_collection


@lru_cache(maxsize=256)
def _cached_retrieve(query: str, top_k: int, collection_size: int) -> tuple[tuple, ...]:
    """Cache hot questions; collection size naturally invalidates rebuilt indexes."""
    collection = get_chroma_collection(reset=False)
    results = collection.query(query_texts=[query], n_results=min(top_k * 2, collection_size))
    rows = []
    for doc, meta, dist in zip(
        results.get("documents", [[]])[0],
        results.get("metadatas", [[]])[0],
        results.get("distances", [[]])[0],
    ):
        rows.append((doc, meta, dist))
    return tuple(rows)


def retrieve_context(query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or TOP_K_RAG
    collection = get_chroma_collection(reset=False)
    n = collection.count()
    if n == 0:
        return []

    contexts: list[dict] = []
    for doc, meta, dist in _cached_retrieve(query.strip().lower(), top_k, n):
        if dist is not None and dist > RAG_MAX_DISTANCE:
            continue
        source = meta.get("source", meta.get("filename", "unknown"))
        contexts.append(
            {
                "text": doc,
                "source": source,
                "subject": meta.get("subject", ""),
                "distance": dist,
                "page_number": meta.get("page_number"),
                "paragraph_index": meta.get("paragraph_index"),
                "filename": meta.get("filename", source.removeprefix("pdf:")),
            }
        )
        if len(contexts) >= top_k:
            break

    log.info("RAG retrieved %s chunks for query (filtered by distance<=%s)", len(contexts), RAG_MAX_DISTANCE)
    return contexts


def format_context_block(contexts: list[dict], max_chars: int | None = None) -> str:
    from settings import MAX_CONTEXT_RAG

    max_chars = max_chars or MAX_CONTEXT_RAG
    if not contexts:
        return ""
    parts, size = [], 0
    for i, ctx in enumerate(contexts, 1):
        block = f"[{i}] {ctx['source']}"
        if ctx.get("subject"):
            block += f" ({ctx['subject']})"
        block += f"\n{ctx['text']}"
        if size + len(block) > max_chars:
            block = block[: max_chars - size]
            if block.strip():
                parts.append(block)
            break
        parts.append(block)
        size += len(block)
    return "\n\n---\n\n".join(parts)
