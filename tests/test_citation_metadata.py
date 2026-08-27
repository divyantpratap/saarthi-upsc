import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ingest.chunker import chunk_text


def test_chunks_preserve_page_and_paragraph_metadata():
    chunks = chunk_text(
        "First paragraph with a complete fact.\n\nSecond paragraph with another fact.",
        "pdf:test.pdf",
        {"filename": "test.pdf", "page_number": 12, "subject": "Polity"},
    )
    assert chunks
    assert chunks[0]["metadata"]["page_number"] == 12
    assert chunks[0]["metadata"]["paragraph_index"] == 1
    assert chunks[0]["metadata"]["filename"] == "test.pdf"
