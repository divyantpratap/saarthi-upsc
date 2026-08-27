"""The NCERT code-to-title map is part of the citation contract.

The download endpoint accepts any valid book code, so a typo can succeed while
quietly filing Psychology under Polity. Keep the corrected mappings explicit.
"""
from __future__ import annotations

from pathlib import Path


MANIFEST = Path(__file__).resolve().parent.parent / "ingest" / "ncert_books.txt"


def _books() -> dict[str, tuple[str, str]]:
    rows = [line.split("|", 2) for line in MANIFEST.read_text().splitlines() if line]
    return {code: (subject, title) for code, subject, title in rows}


def test_manifest_has_21_unique_books():
    books = _books()
    assert len(books) == 21


def test_codes_match_their_ncert_titles():
    books = _books()
    assert books["keps2dd"] == ("Polity", "Class XI — Indian Constitution at Work")
    assert books["keps1dd"] == ("Polity", "Class XI — Political Theory")
    assert "kepy1dd" not in books  # Psychology, not a UPSC Polity source

    assert books["kegy2dd"] == (
        "Geography",
        "Class XI — Fundamentals of Physical Geography",
    )
    assert books["kegy1dd"] == ("Geography", "Class XI — India Physical Environment")

    assert books["jess3dd"] == (
        "Social Science",
        "Class X — India and the Contemporary World II",
    )
    assert books["jess1dd"] == ("Social Science", "Class X — Contemporary India II")
    assert books["jess4dd"] == ("Social Science", "Class X — Democratic Politics II")
    assert books["jess2dd"] == (
        "Social Science",
        "Class X — Understanding Economic Development",
    )
