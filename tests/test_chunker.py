"""The splitter must terminate and must always move forward.

Page-level ingestion feeds the splitter many texts shorter than CHUNK_SIZE.
Before this was fixed, each of those emitted the whole text once and then
dribbled out ~CHUNK_OVERLAP near-duplicate fragments, advancing one character
at a time.
"""
from __future__ import annotations

from settings import CHUNK_OVERLAP, CHUNK_SIZE
from src.ingest.chunker import chunk_text


def test_short_text_yields_exactly_one_chunk():
    text = "The Constitution of India was adopted on 26 November 1949."
    chunks = chunk_text(text, "pdf:test", {"page_number": 1})
    assert len(chunks) == 1
    assert chunks[0]["text"] == text


def test_text_just_under_chunk_size_is_not_fragmented():
    text = ("Article 32 is the heart and soul of the Constitution. " * 15).strip()
    assert len(text) < CHUNK_SIZE
    assert len(chunk_text(text, "pdf:test")) == 1


def test_long_text_splits_without_fragment_tail():
    text = ("Directive Principles are non-justiciable guidelines. " * 200).strip()
    chunks = chunk_text(text, "pdf:test")
    expected_max = len(text) // (CHUNK_SIZE - CHUNK_OVERLAP) + 2
    assert len(chunks) <= expected_max
    # A trailing run of overlap-sized crumbs is the signature of the old bug.
    assert all(len(c["text"]) > CHUNK_OVERLAP for c in chunks[:-1])


def test_every_chunk_carries_its_page_citation():
    text = ("Fundamental Rights are enshrined in Part III. " * 60).strip()
    chunks = chunk_text(text, "pdf:polity.pdf", {"page_number": 412, "subject": "Polity"})
    assert chunks
    assert all(c["metadata"]["page_number"] == 412 for c in chunks)
    assert all(c["metadata"]["source"] == "pdf:polity.pdf" for c in chunks)


def test_empty_and_whitespace_text_yield_nothing():
    assert chunk_text("", "pdf:test") == []
    assert chunk_text("   \n\n  ", "pdf:test") == []


def test_chunk_ids_are_unique():
    text = ("The Finance Commission is constituted under Article 280. " * 120).strip()
    chunks = chunk_text(text, "pdf:economy.pdf")
    assert len({c["id"] for c in chunks}) == len(chunks)
