"""Load and match one-shot answer style examples."""
from __future__ import annotations

import json
import re
from functools import lru_cache

from settings import ANSWER_EXAMPLES_FILE


@lru_cache(maxsize=1)
def _load_examples() -> list[dict]:
    if not ANSWER_EXAMPLES_FILE.exists():
        return []
    data = json.loads(ANSWER_EXAMPLES_FILE.read_text(encoding="utf-8"))
    return data.get("examples", [])


def _score_example(question: str, ex: dict) -> int:
    q = question.lower()
    score = 0
    for pattern in ex.get("match", []):
        if re.search(pattern, q, re.I):
            score += 3
    # Light overlap with example question words
    ex_words = set(re.findall(r"[a-z]{4,}", ex.get("question", "").lower()))
    q_words = set(re.findall(r"[a-z]{4,}", q))
    score += len(ex_words & q_words)
    return score


def get_answer_examples(question: str, mode: str = "direct", max_examples: int = 2) -> str:
    """
    Return formatted few-shot examples for the model to mimic structure.
    """
    examples = _load_examples()
    if not examples:
        return ""

    scored = []
    for ex in examples:
        s = _score_example(question, ex)
        types = ex.get("types", [])
        if mode in types or "hybrid" in types:
            s += 1
        if s > 0:
            scored.append((s, ex))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [ex for _, ex in scored[:max_examples]]

    if not picked and examples:
        # Default: definition + compare templates
        picked = [examples[0]]
        if mode in ("rag", "hybrid") and len(examples) > 1:
            picked.append(examples[1])

    blocks = []
    for i, ex in enumerate(picked, 1):
        blocks.append(
            f"### Style reference {i} (format only — use YOUR material's facts)\n"
            f"**Sample Q:** {ex['question']}\n\n"
            f"**Sample A:**\n{ex['answer']}"
        )
    return "\n\n---\n\n".join(blocks)
