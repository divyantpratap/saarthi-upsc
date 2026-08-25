"""Production hybrid pipeline with timing, history, and error handling."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from settings import DIRECT_EXCERPT_CHARS, TOP_K_DIRECT, TOP_K_RAG
from src.core.gemini import GeminiError
from src.core.logging_config import log
from src.ingest.build_store import get_collection_count
from src.rag.generator import generate_answer
from src.rag.retriever import format_context_block, retrieve_context
from src.rag.router import route_question
from src.references.catalog import lookup_direct


@dataclass
class AskResult:
    answer: str
    mode: str
    sources: list[dict] = field(default_factory=list)
    context_used: bool = False
    latency_ms: int = 0
    error: str | None = None


class UPSCChatbot:
    def __init__(self, max_history_turns: int = 3):
        self.max_history_turns = max_history_turns
        self._history: list[tuple[str, str]] = []

    def _has_rag(self) -> bool:
        return get_collection_count() > 0

    def _history_text(self) -> str:
        if not self._history:
            return ""
        lines = []
        for q, a in self._history[-self.max_history_turns :]:
            lines.append(f"Student: {q[:500]}")
            lines.append(f"Assistant: {a[:800]}")
        return "\n".join(lines)

    def ask(
        self,
        question: str,
        guidance: str | None = None,
        *,
        api_key: str | None = None,
    ) -> dict:
        t0 = time.perf_counter()
        question = question.strip()
        if not question:
            return AskResult(answer="Please ask a question.", mode="none").__dict__

        try:
            mode = route_question(question, self._has_rag())
            contexts: list[dict] = []
            sources: list[dict] = []

            if mode in ("direct", "hybrid"):
                for d in lookup_direct(question, top_k=TOP_K_DIRECT):
                    excerpt = d["text"][:DIRECT_EXCERPT_CHARS]
                    contexts.append(
                        {
                            "text": excerpt,
                            "source": d["source"],
                            "subject": d.get("subject", ""),
                        }
                    )
                    sources.append(
                        {
                            "source": d["source"],
                            "subject": d.get("subject", ""),
                            "preview": excerpt[:280] + ("..." if len(excerpt) > 280 else ""),
                            "mode": "direct",
                        }
                    )

            if mode in ("rag", "hybrid"):
                for c in retrieve_context(question, top_k=TOP_K_RAG):
                    contexts.append(c)
                    sources.append(
                        {
                            "source": c["source"],
                            "subject": c.get("subject", ""),
                            "preview": c["text"],
                            "mode": "rag",
                            "page_number": c.get("page_number"),
                            "paragraph_index": c.get("paragraph_index"),
                            "filename": c.get("filename"),
                            "relevance": round(max(0.0, 1.0 - float(c.get("distance") or 0.0)) * 100),
                        }
                    )

            seen: set[tuple] = set()
            unique_sources = []
            for s in sources:
                key = (s["source"], s.get("page_number"), s.get("paragraph_index"))
                if key not in seen:
                    seen.add(key)
                    unique_sources.append(s)

            from settings import MAX_CONTEXT_DIRECT, MAX_CONTEXT_RAG

            cap = MAX_CONTEXT_DIRECT if mode == "direct" else MAX_CONTEXT_RAG
            context_block = format_context_block(contexts, max_chars=cap)

            generation_question = f"{guidance}\n\nStudent question: {question}" if guidance else question
            try:
                answer = generate_answer(
                    generation_question,
                    context_block,
                    mode=mode,
                    history=self._history_text() or None,
                    api_key=api_key,
                )
            except GeminiError as exc:
                # Retrieval remains useful during transient model outages. Never
                # turn a provider-side 429/503 into a broken student workflow.
                log.warning("generation unavailable; serving source fallback: %s", exc)
                if contexts:
                    excerpts = []
                    for i, ctx in enumerate(contexts[:3], 1):
                        text = " ".join(ctx.get("text", "").split())
                        excerpts.append(f"**[{i}] {ctx.get('source', 'Study material')}**\n\n{text[:900]}")
                    answer = (
                        "### Source notes\n\n"
                        "The answer model is temporarily busy, so I’m showing the strongest "
                        "matching passages instead of failing your request.\n\n"
                        + "\n\n---\n\n".join(excerpts)
                        + "\n\n*You can retry shortly for a synthesized UPSC-style answer.*"
                    )
                else:
                    answer = (
                        "I couldn’t find a reliable passage for this question, and the answer "
                        "model is temporarily unavailable. Try a more specific UPSC topic or retry shortly."
                    )

            self._history.append((question, answer))
            if len(self._history) > self.max_history_turns:
                self._history = self._history[-self.max_history_turns :]

            ms = int((time.perf_counter() - t0) * 1000)
            log.info("ask mode=%s sources=%s latency_ms=%s", mode, len(unique_sources), ms)

            return AskResult(
                answer=answer,
                mode=mode,
                sources=unique_sources,
                context_used=bool(contexts),
                latency_ms=ms,
            ).__dict__

        except GeminiError as exc:
            ms = int((time.perf_counter() - t0) * 1000)
            log.exception("ask failed")
            return AskResult(
                answer=(
                    "I could not generate an answer right now. "
                    f"Details: {exc}\n\n"
                    "Check your API key, quota, and try a shorter question."
                ),
                mode="error",
                latency_ms=ms,
                error=str(exc),
            ).__dict__
        except Exception as exc:
            ms = int((time.perf_counter() - t0) * 1000)
            log.exception("unexpected ask failure")
            return AskResult(
                answer=f"Unexpected error: {exc}",
                mode="error",
                latency_ms=ms,
                error=str(exc),
            ).__dict__

    def load_history(self, messages: list[dict]) -> None:
        """Restore conversation memory from stored messages."""
        self._history = []
        i = 0
        while i < len(messages) - 1:
            if messages[i].get("role") == "user" and messages[i + 1].get("role") == "assistant":
                self._history.append(
                    (messages[i]["content"], messages[i + 1]["content"])
                )
                i += 2
            else:
                i += 1

    def reset(self) -> None:
        self._history = []
