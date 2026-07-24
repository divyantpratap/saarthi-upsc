# Saarthi

A study assistant for UPSC aspirants that answers from real source material instead of guessing. Ask a question and it pulls the relevant passages from a study library, then writes a grounded answer in the mode you need (Learn, Prelims, Mains, or Evaluate).

> Live demo: [Streamlit Community Cloud — link after deploy](https://share.streamlit.io)

## Why I built it

Most study chatbots hallucinate. For exam prep, a confident wrong answer is worse than no answer. Saarthi is built around retrieval so every answer is tied back to the material it came from — routing, hybrid retrieval, context limits, and failure handling included.

## How it works

```
Question -> Router (heuristic)
   |- DIRECT  : keyword (BM25) lookup for "what does book X say about Y"
   |- RAG     : vector search over chunked material in ChromaDB
   |- HYBRID  : both paths when the question is ambiguous
```

- **Hybrid retrieval** — keyword for book lookups, vectors for concepts
- **Grounding** — answers from retrieved passages, not model memory
- **Study modes** — Learn / Prelims / Mains / Evaluate
- **Resilience** — retries, context caps, empty-response handling

## Tech

Python · Streamlit · ChromaDB · rank-bm25 · PyMuPDF · BeautifulSoup · Google Gemini (Flash) · Docker · pytest

## Run locally

```bash
git clone https://github.com/divyantpratap/saarthi-upsc.git
cd saarthi-upsc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # set GEMINI_API_KEY

# optional: build a demo index from bundled public notes
EMBEDDING_BACKEND=gemini python scripts/build_demo_index.py

streamlit run app.py
```

## Knowledge base

Copyrighted study books stay out of the repo. Bring your own PDFs under `data/pdfs/` and run `python scripts/build_all.py`.

The live demo auto-builds a small index from bundled public study notes (`data/sample_study_notes.txt`) using Gemini embeddings on first launch.

## Streamlit Community Cloud

1. Deploy from this repo, main file `app.py`
2. Secrets (Settings → Secrets):

```toml
GEMINI_API_KEY = "your_key"
EMBEDDING_BACKEND = "gemini"
GEMINI_MODEL = "gemini-2.5-flash"
```

## Tests

```bash
pytest tests/ -q
```

## License

MIT. See [LICENSE](LICENSE).
