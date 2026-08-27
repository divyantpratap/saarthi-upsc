import json

import ingest.build_index as build_index
from ingest.build_index import _embedding_work


def test_embedding_work_separates_cache_hits_from_duplicates():
    chunks = [
        {"text": "cached first"},
        {"text": "cached duplicate"},
        {"text": "new first"},
        {"text": "new duplicate"},
        {"text": "another new"},
    ]
    hashes = ["cached", "cached", "new", "new", "other"]

    pending, cached_chunks, duplicate_chunks = _embedding_work(
        chunks, hashes, {"cached"}
    )

    assert cached_chunks == 2
    assert duplicate_chunks == 1
    assert pending == {"new": "new first", "other": "another new"}


def test_lexical_emit_has_no_dense_matrix(tmp_path, monkeypatch):
    monkeypatch.setattr(build_index, "OUT_DIR", tmp_path)
    chunks = [
        {
            "tier": "A",
            "text": "Article 32 guarantees constitutional remedies.",
            "metadata": {
                "source": "pdf:constitution/test.pdf",
                "filename": "constitution/test.pdf",
                "subject": "Polity",
                "page_number": 1,
                "paragraph_index": 1,
            },
        }
    ]

    build_index.emit(chunks, None, "test-fingerprint")

    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["count"] == 1
    assert meta["vectorCount"] == 0
    assert meta["retrievalMode"] == "lexical"
    assert (tmp_path / "vectors.f16.bin").read_bytes() == b""
