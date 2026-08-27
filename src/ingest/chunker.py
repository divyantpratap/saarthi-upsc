"""Split documents into overlapping chunks for vector search."""
from __future__ import annotations

from settings import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_text(text: str, source: str, metadata: dict | None = None) -> list[dict]:
    """Split text into chunks with source metadata."""
    # Keep paragraph boundaries: they are part of the citation contract shown
    # to students. Lines inside a paragraph are still normalised for retrieval.
    paragraphs = [" ".join(p.split()) for p in text.split("\n\n") if p.strip()]
    text = "\n\n".join(paragraphs)
    if not text.strip():
        return []

    meta = metadata or {}
    chunks: list[dict] = []
    start = 0
    idx = 0

    while start < len(text):
        target_end = min(start + CHUNK_SIZE, len(text))
        end = target_end
        if target_end < len(text):
            # Search for a boundary only in the back half, so a full stop near
            # the start of the window can never shrink a chunk to a crumb.
            floor = start + CHUNK_SIZE // 2
            paragraph_end = text.rfind("\n\n", floor, target_end)
            sentence_end = max(text.rfind(". ", floor, target_end), text.rfind("? ", floor, target_end))
            end = paragraph_end if paragraph_end > start else (sentence_end + 1 if sentence_end > start else target_end)
        piece = text[start:end].strip()
        if piece:
            paragraph_index = text[:start].count("\n\n") + 1
            chunks.append(
                {
                    "id": f"{source}__chunk_{idx}",
                    "text": piece,
                    "metadata": {
                        **meta,
                        "source": source,
                        "chunk_index": idx,
                        "paragraph_index": paragraph_index,
                    },
                }
            )
            idx += 1
        if end >= len(text):
            break  # text consumed; stepping back by the overlap would re-emit its tail
        start = max(end - CHUNK_OVERLAP, start + 1)

    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chunk a list of {text, source, metadata?} documents."""
    all_chunks: list[dict] = []
    for doc in documents:
        all_chunks.extend(
            chunk_text(
                doc["text"],
                doc["source"],
                doc.get("metadata"),
            )
        )
    return all_chunks
