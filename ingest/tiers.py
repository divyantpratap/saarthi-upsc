"""Corpus tiering: what may be published verbatim, and what may not.

Tier A  freely redistributable (government / open-licence). Chunk text ships
        in the public repo and the hosted demo quotes it directly.
Tier B  everything else. Only vectors and citation metadata ship publicly, so
        every book stays searchable without its pages being republished.

Tier is decided by **where a file lives**, never by what it is called. An
earlier version matched filenames against patterns like "ncert" and
"parliament", and promoted two files it should not have:
`NCERT_Science-compilaton.compressed.pdf` (a coaching compilation that merely
cites NCERT) and `UPSC_Decoding_Syllabus_www.iasparliament.com.pdf` (which
matched "parliament"). A filename heuristic fails open — the wrong direction
when the consequence is republishing someone's book. A path allowlist fails
closed: a misfiled title stays citation-only, which costs nothing.
"""
from __future__ import annotations

from pathlib import PurePosixPath

OPEN = "A"
RESTRICTED = "B"

#: Directories under data/pdfs/ whose contents are cleared for verbatim
#: publication. Add one only after confirming the material's licence.
OPEN_ROOTS = frozenset({"ncert", "constitution", "open", "govt"})


def classify(display_name: str, doc_type: str = "pdf") -> str:
    """Return the publication tier for a source.

    ``display_name`` is the path relative to the PDF root, so its first segment
    identifies the collection a file was filed under. Notes authored for this
    repo and scraped government pages are open by construction.
    """
    if doc_type in ("notes", "web"):
        return OPEN

    parts = PurePosixPath(display_name.replace("\\", "/")).parts
    if len(parts) < 2:
        return RESTRICTED  # loose in the root: unclassified, so not publishable
    return OPEN if parts[0].lower() in OPEN_ROOTS else RESTRICTED
