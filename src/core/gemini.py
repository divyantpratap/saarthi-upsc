"""Production Gemini client: retries, validation, safe truncation."""
from __future__ import annotations

import os
import time
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

from settings import (
    GEMINI_EMBED_MODEL,
    GEMINI_MODEL,
    GEMINI_MODEL_FALLBACK,
    GEMINI_TIMEOUT_MS,
    MAX_CONTEXT_CHARS,
    MAX_OUTPUT_TOKENS,
)
from src.core.logging_config import log

load_dotenv()

SYSTEM_INSTRUCTION = """You are **UPSC Prep AI**, a specialized tutor for Indian Civil Services aspirants (UPSC CSE).

Rules:
- Use ONLY the provided study material for factual claims.
- If material is insufficient, state that clearly; add brief syllabus context only when certain.
- Structure: headings, bullets, **Prelims** / **Mains** pointers where useful.
- Cite sources using the exact filename shown in brackets, e.g. [1] pdf:Spectrum.pdf.
- Be accurate, concise, Indian English. Never invent statistics or quotes.
- Follow the **answer style references** in the user message when provided (structure/tone only)."""


class GeminiError(Exception):
    pass


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY not set. Copy .env.example to .env")
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
    )


def _extract_text(response) -> str:
    if not response:
        return ""
    text = getattr(response, "text", None)
    if text:
        return text.strip()
    # Fallback parse candidates
    try:
        parts = []
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if content and content.parts:
                for p in content.parts:
                    if getattr(p, "text", None):
                        parts.append(p.text)
        return "\n".join(parts).strip()
    except Exception:
        return ""


def generate_text(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.25,
    max_tokens: int | None = None,
    retries: int = 1,
) -> str:
    prompt = prompt[:MAX_CONTEXT_CHARS + 5000]  # hard cap on prompt size
    client = get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens or MAX_OUTPUT_TOKENS,
        system_instruction=system or SYSTEM_INSTRUCTION,
    )
    last_err: Exception | None = None

    models_to_try = [model or GEMINI_MODEL]
    if GEMINI_MODEL_FALLBACK and GEMINI_MODEL_FALLBACK not in models_to_try:
        models_to_try.append(GEMINI_MODEL_FALLBACK)

    for model_name in models_to_try:
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                text = _extract_text(response)
                if text:
                    if model_name != models_to_try[0]:
                        log.info("Used fallback model %s", model_name)
                    return text
                finish = None
                if response.candidates:
                    finish = getattr(response.candidates[0], "finish_reason", None)
                log.warning(
                    "Empty response model=%s finish=%s attempt=%s",
                    model_name,
                    finish,
                    attempt + 1,
                )
                last_err = GeminiError(f"Empty model response (finish_reason={finish})")
            except Exception as exc:
                last_err = exc
                log.warning("Gemini %s attempt %s: %s", model_name, attempt + 1, exc)
                err = str(exc)
                if "404" in err or "NOT_FOUND" in err:
                    break  # try fallback model
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    time.sleep(2 ** attempt)
                elif attempt < retries - 1:
                    time.sleep(1)

    raise GeminiError(str(last_err) if last_err else "Generation failed")


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if not texts:
        return []
    client = get_client()
    result = client.models.embed_content(
        model=GEMINI_EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in result.embeddings]
