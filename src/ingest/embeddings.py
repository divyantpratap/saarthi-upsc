"""Embedding backends for ChromaDB."""
from __future__ import annotations

import os
import time

from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions

from settings import EMBEDDING_BACKEND, LOCAL_EMBED_MODEL
from src.core.gemini import embed_texts


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input)
        for attempt in range(5):
            try:
                return embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
            except Exception as exc:
                if "429" in str(exc) and attempt < 4:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        return []


_embed_fn: EmbeddingFunction | None = None


def get_embedding_function() -> EmbeddingFunction:
    global _embed_fn
    if _embed_fn is not None:
        return _embed_fn
    backend = os.getenv("EMBEDDING_BACKEND", EMBEDDING_BACKEND).lower()
    if backend == "gemini":
        _embed_fn = GeminiEmbeddingFunction()
    else:
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=LOCAL_EMBED_MODEL
        )
    return _embed_fn


def reset_embedding_cache() -> None:
    global _embed_fn
    _embed_fn = None
