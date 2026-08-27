"""Tiering decides what gets republished, so it must fail closed.

Anything not explicitly filed under an open collection stays citation-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingest"))

from tiers import OPEN, RESTRICTED, classify  # noqa: E402


def test_open_collections_are_quotable():
    assert classify("ncert/Polity_Class_XI/keps101.pdf") == OPEN
    assert classify("constitution/Constitution_of_India.pdf") == OPEN
    assert classify("open/some_government_report.pdf") == OPEN


def test_commercial_titles_are_citation_only():
    assert classify("AFCAT/Arihant AFCAT.pdf") == RESTRICTED
    assert classify("pdf books/Sapiens A Graphic History.pdf") == RESTRICTED
    assert classify("General Knowledge/vision ias may-2021.pdf") == RESTRICTED


def test_names_that_merely_mention_open_sources_stay_restricted():
    """The regression that motivated the path allowlist.

    Both of these were promoted to quotable by filename matching: the first
    only cites NCERT, and the second matched the word "parliament" inside a
    coaching site's domain.
    """
    assert classify("Science & Environment/NCERT_Science-compilaton.pdf") == RESTRICTED
    assert classify("UPSC_Decoding_Syllabus_www.iasparliament.com.pdf") == RESTRICTED


def test_unfiled_root_level_pdfs_are_restricted():
    assert classify("something_unsorted.pdf") == RESTRICTED


def test_authored_notes_and_scraped_pages_are_open():
    assert classify("sample_study_notes.txt", "notes") == OPEN
    assert classify("https://pib.gov.in/release", "web") == OPEN


def test_open_root_matching_is_case_insensitive():
    assert classify("NCERT/Polity/keps101.pdf") == OPEN
