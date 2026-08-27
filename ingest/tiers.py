"""Corpus tiering: what may be published verbatim, and what may not.

Tier A  freely redistributable (government / open-licence). Chunk text ships
        in the public repo and the hosted demo quotes it directly.
Tier B  commercial titles. Only vectors and citation metadata ship publicly, so
        every book stays searchable without its pages being republished.
Tier C  is not a build-time tier: it is Tier B resolved against local PDFs when
        the app runs on a machine that legitimately holds them.
"""
from __future__ import annotations

import re

# Government, constitutional and open-licence material.
_OPEN_MARKERS = re.compile(
    r"ncert|constitution[_\s-]?of[_\s-]?india|bare[_\s-]?act|"
    r"economic[_\s-]?survey|india[_\s-]?year[_\s-]?book|yearbook|"
    r"union[_\s-]?budget|budget[_\s-]?speech|pib|press[_\s-]?information|"
    r"gazette|annual[_\s-]?report|census|niti[_\s-]?aayog|"
    r"parliament|lok[_\s-]?sabha|rajya[_\s-]?sabha|supreme[_\s-]?court",
    re.I,
)

OPEN = "A"
RESTRICTED = "B"


def classify(display_name: str, doc_type: str = "pdf") -> str:
    """Return the publication tier for a source.

    Notes and scraped government pages authored for this repo are open by
    construction. PDFs are open only when the filename identifies them as
    government or constitutional material; anything unrecognised is treated as
    restricted, because guessing wrong in that direction republishes a book.
    """
    if doc_type in ("notes", "web"):
        return OPEN
    return OPEN if _OPEN_MARKERS.search(display_name) else RESTRICTED
