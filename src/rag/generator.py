"""Answer generation with context budgeting and retry."""
from __future__ import annotations

from settings import MAX_CONTEXT_DIRECT, MAX_CONTEXT_RAG
from src.core.gemini import GeminiError, SYSTEM_INSTRUCTION, generate_text
from src.core.logging_config import log
from src.rag.retriever import format_context_block
from src.references.answer_style import get_answer_examples


def _build_prompt(user_query: str, context_block: str, mode: str) -> str:
    mode_note = {
        "direct": "Mode: DIRECT — answer from the book excerpts below.",
        "rag": "Mode: DEEP RAG — synthesize from retrieved passages.",
        "hybrid": "Mode: HYBRID — use both excerpt types; prefer RAG passages for depth.",
    }.get(mode, "")

    style_refs = get_answer_examples(user_query, mode=mode)
    style_section = ""
    if style_refs:
        style_section = f"""
## Answer style references (match this structure & tone; facts must come from study material)

{style_refs}

---
"""

    if context_block.strip():
        return f"""{mode_note}
{style_section}
## Study material

{context_block}

---

## Question

{user_query}

Write a complete answer in the style of the references above. Cite sources as [1], [2] matching the brackets above."""
    return f"""## Question

{user_query}

No study material was retrieved. Tell the user to run indexing if needed. Only state well-known syllabus facts you are certain about."""


def generate_answer(
    user_query: str,
    context_block: str,
    mode: str = "rag",
    history: str | None = None,
) -> str:
    cap = MAX_CONTEXT_DIRECT if mode == "direct" else MAX_CONTEXT_RAG
    if len(context_block) > cap:
        context_block = context_block[:cap] + "\n\n[...truncated for length]"

    history_block = ""
    if history:
        history_block = f"\n## Recent conversation\n{history}\n"

    prompt = history_block + _build_prompt(user_query, context_block, mode)

    try:
        return generate_text(prompt, system=SYSTEM_INSTRUCTION, temperature=0.25)
    except GeminiError as exc:
        log.error("Generation failed: %s", exc)
        # Retry once with half context
        if context_block.strip():
            short_ctx = format_context_block(
                [{"text": context_block[: cap // 2], "source": "truncated", "subject": ""}],
                max_chars=cap // 2,
            )
            try:
                return generate_text(
                    history_block + _build_prompt(user_query, short_ctx, mode),
                    system=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                )
            except GeminiError:
                pass
        raise
