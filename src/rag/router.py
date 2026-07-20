"""Route questions: DIRECT (catalog) vs RAG (vector DB) vs HYBRID."""
from __future__ import annotations

import re

# Heuristic routing only (no extra API latency/cost)
_DEEP_PATTERNS = re.compile(
    r"\b(compare|contrast|analyze|analysis|discuss|evaluate|critically|"
    r"relationship between|difference between|similarit|implications|"
    r"multi|comprehensive|in detail|elaborate|mains answer|essay)\b",
    re.I,
)
_DIRECT_PATTERNS = re.compile(
    r"\b(what is|who is|when was|define|article \d+|list the|name the|"
    r"which article|full form|meaning of|how many|term of|capital of)\b",
    re.I,
)


def route_question(question: str, has_rag_index: bool) -> str:
    """
    Returns: 'direct' | 'rag' | 'hybrid'
    """
    q = question.strip()
    if not has_rag_index:
        return "direct"

    if _DEEP_PATTERNS.search(q):
        return "rag"
    if _DIRECT_PATTERNS.search(q) and len(q.split()) < 25:
        return "direct"
    if len(q.split()) > 35:
        return "rag"

    # Ambiguous: prefer hybrid (catalog + RAG) — best quality without extra API call
    return "hybrid" if has_rag_index else "direct"
