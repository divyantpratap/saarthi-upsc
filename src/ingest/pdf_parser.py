"""Fast PDF text extraction with PyMuPDF and page limits."""
from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

from settings import MAX_PAGES_FULL, MAX_PAGES_PREVIEW, MIN_CHARS_PER_PDF, PDF_DIR


def _guess_subject(filename: str) -> str:
    name = filename.lower()
    rules = [
        (r"polity|governance|constitution", "Polity"),
        (r"history|medieval|modern india|basham|spectrum", "History"),
        (r"geograph|majid|world geo|indian geo", "Geography"),
        (r"econom|verma", "Economy"),
        (r"science|csat|disha", "Science & CSAT"),
        (r"ethic", "Ethics"),
        (r"international|ir\b", "International Relations"),
        (r"security|internal", "Security"),
        (r"disaster", "Disaster Management"),
        (r"syllabus|pyq|mains|pre gs", "Exam Strategy"),
        (r"magazine|secure", "Current Affairs"),
        (r"social", "Social Issues"),
    ]
    for pattern, subject in rules:
        if re.search(pattern, name):
            return subject
    return "General Studies"


def extract_pdf_text(path: Path, max_pages: int | None = None) -> str:
    doc = fitz.open(path)
    limit = min(len(doc), max_pages) if max_pages else len(doc)
    parts = []
    for i in range(limit):
        page = doc.load_page(i)
        text = page.get_text("text")
        if text and text.strip():
            parts.append(text.strip())
    doc.close()
    return "\n\n".join(parts)


def list_pdfs(directory: Path | None = None) -> list[Path]:
    directory = directory or PDF_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return sorted(directory.rglob("*.pdf"))


def pdf_to_document(path: Path, max_pages: int | None = MAX_PAGES_FULL) -> dict | None:
    try:
        text = extract_pdf_text(path, max_pages=max_pages)
        if len(text.strip()) < MIN_CHARS_PER_PDF:
            return None
        return {
            "text": text,
            "source": f"pdf:{path.name}",
            "metadata": {
                "type": "pdf",
                "filename": path.name,
                "subject": _guess_subject(path.name),
                "pages_used": str(max_pages or "all"),
            },
        }
    except Exception as exc:
        print(f"  [skip] {path.name}: {exc}")
        return None


def pdf_to_documents(path: Path, max_pages: int | None = MAX_PAGES_FULL) -> list[dict]:
    """Extract one document per PDF page so citations retain an exact location."""
    documents: list[dict] = []
    try:
        pdf = fitz.open(path)
        limit = min(len(pdf), max_pages) if max_pages else len(pdf)
        try:
            display_name = str(path.relative_to(PDF_DIR))
        except ValueError:
            display_name = path.name
        subject = _guess_subject(display_name)
        for page_index in range(limit):
            text = pdf.load_page(page_index).get_text("text").strip()
            if not text:
                continue
            documents.append(
                {
                    "text": text,
                    "source": f"pdf:{display_name}",
                    "metadata": {
                        "type": "pdf",
                        "filename": display_name,
                        "subject": subject,
                        "page_number": page_index + 1,
                        "total_pages": len(pdf),
                    },
                }
            )
        pdf.close()
    except Exception as exc:
        print(f"  [skip] {path.name}: {exc}")
    return documents


def pdf_preview(path: Path, max_pages: int = MAX_PAGES_PREVIEW) -> str:
    return extract_pdf_text(path, max_pages=max_pages)
