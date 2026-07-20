# UPSC Prep AI

Production-ready hybrid tutor for UPSC CSE: **Gemini 3.5 Flash** (falls back to 2.5 Flash) + **direct book lookup** + **deep RAG** + **one-shot answer style guides**.

## Features

| Feature | Description |
|---------|-------------|
| **DIRECT** | BM25 over 28-book catalog (~8s answers) |
| **RAG** | 8k+ chunks, filtered vector search |
| **HYBRID** | Both paths for ambiguous questions |
| **Resilience** | Retries, context limits, empty-response handling |
| **Ops** | Health checks, structured logs, Docker |

## Quick start

```powershell
cd c:\Users\divya\Music\DP_Projects\UPSC
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set GEMINI_API_KEY

python scripts\build_catalog.py
python scripts\build_all.py   # optional ~4 min

.\run.bat
# Open http://localhost:8501
```

## Production

```powershell
# Health (exit 0 = OK)
python scripts\health_check.py

# Tests
pytest tests/ -q

# Docker
docker compose up --build
```

## Configuration

See `.env.example`. Key variables:

- `GEMINI_API_KEY` — required
- `GEMINI_MODEL` — default `gemini-3.5-flash` (free tier; same class as 2.5 Flash)
- `data/references/answer_examples.json` — edit to add your preferred answer formats
- `EMBEDDING_BACKEND` — `local` (default) or `gemini`
- `RAG_MAX_DISTANCE` — relevance cutoff (default `0.72`)
- `TOP_K_RAG` — chunks per deep query (default `6`)

## Data layout

- `data/pdfs/` — your books (32 PDFs)
- `data/references/catalog.json` — direct lookup index
- `chroma_db/` — RAG vector store
- `logs/app.log` — application logs

## Architecture

```
Question → Router (heuristic)
    ├─ DIRECT  → catalog BM25 → Gemini
    ├─ RAG     → Chroma + filter → Gemini
    └─ HYBRID  → both → Gemini
```

## Skipped PDFs

5 scanned/empty PDFs are skipped during ingest (no extractable text). Re-scan or OCR to include them.
