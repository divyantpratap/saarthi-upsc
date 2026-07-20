"""Incremental ChromaDB indexing — one PDF at a time, Gemini embeddings."""
from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
from tqdm import tqdm

from settings import CHROMA_DIR, COLLECTION_NAME, DATA_DIR
from src.ingest.chunker import chunk_documents
from src.ingest.embeddings import get_embedding_function, reset_embedding_cache
from src.ingest.pdf_parser import list_pdfs, pdf_to_documents


def load_text_files(directory: Path) -> list[dict]:
    documents: list[dict] = []
    for txt_path in sorted(directory.glob("*.txt")):
        if txt_path.name == "sample_urls.txt":
            continue
        text = txt_path.read_text(encoding="utf-8")
        if text.strip():
            documents.append(
                {
                    "text": text,
                    "source": f"notes:{txt_path.name}",
                    "metadata": {"type": "notes", "filename": txt_path.name, "subject": "Notes"},
                }
            )
    return documents


_collection_cache = None


def get_collection_count() -> int:
    """Read index size without loading the sentence-transformer model."""
    if not CHROMA_DIR.exists():
        return 0
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return client.get_collection(COLLECTION_NAME).count()
    except Exception:
        return 0


def clear_collection_cache() -> None:
    global _collection_cache
    _collection_cache = None
    reset_embedding_cache()


def get_chroma_collection(reset: bool = False):
    global _collection_cache
    if reset:
        clear_collection_cache()
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        _collection_cache = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
        return _collection_cache

    if _collection_cache is not None:
        return _collection_cache

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    _collection_cache = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    return _collection_cache


def _stable_id(source: str, chunk_index: int) -> str:
    raw = f"{source}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def index_documents(collection, documents: list[dict], label: str = "") -> int:
    if not documents:
        return 0
    chunks = chunk_documents(documents)
    if not chunks:
        return 0

    ids, texts, metas = [], [], []
    for c in chunks:
        ids.append(_stable_id(c["metadata"]["source"], c["metadata"]["chunk_index"]))
        texts.append(c["text"])
        metas.append(c["metadata"])

    # Upsert in batches (Gemini embed API called inside Chroma)
    batch = 32
    for i in range(0, len(ids), batch):
        collection.upsert(
            ids=ids[i : i + batch],
            documents=texts[i : i + batch],
            metadatas=metas[i : i + batch],
        )
    if label:
        print(f"  indexed {len(chunks)} chunks from {label}")
    return len(chunks)


def build_vector_store(reset: bool = True) -> int:
    from settings import EMBEDDING_BACKEND
    import os
    backend = os.getenv("EMBEDDING_BACKEND", EMBEDDING_BACKEND)
    print(f"=== Incremental RAG Index (embed: {backend}) ===\n")
    collection = get_chroma_collection(reset=reset)
    total = 0

    notes = load_text_files(DATA_DIR)
    total += index_documents(collection, notes, "text notes")

    pdfs = list_pdfs()
    print(f"\nPDFs to index: {len(pdfs)}")
    for path in tqdm(pdfs, desc="PDFs"):
        docs = pdf_to_documents(path)
        if docs:
            total += index_documents(collection, docs, path.name)

    print(f"\nVector store: {CHROMA_DIR}")
    print(f"Total chunks in DB: {collection.count()}")
    return total
