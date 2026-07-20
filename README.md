# Saarthi

A study assistant for UPSC aspirants that answers from real source material instead of guessing. Ask it a question and it pulls the relevant passages from a library of study books, then writes a grounded answer in the mode you need (learn, prelims, mains, or evaluate).

> Live demo: [add link once deployed]

<!-- Add a screenshot or short GIF of the app here. A visual on the README roughly doubles how long people spend on a repo. -->
<!-- ![Saarthi screenshot](docs/screenshot.png) -->

## Why I built it

Most study chatbots hallucinate, and for exam prep a confident wrong answer is worse than no answer because it costs you marks. Saarthi is built around retrieval so every answer is tied back to the material it came from. It was also my way of working through the harder parts of a real RAG system: routing, hybrid retrieval, context limits, and failure handling.

## How it works

Saarthi routes each question down one of three paths, then hands the retrieved context to a Gemini Flash model to write the answer.

```
Question -> Router (heuristic)
   |- DIRECT  : keyword (BM25) lookup over a book catalog, for "what does book X say about Y"
   |- RAG     : vector search over chunked material in ChromaDB, for conceptual questions
   |- HYBRID  : both paths together when the question is ambiguous
```

A few things I paid attention to:

- **Hybrid retrieval.** Pure vector search is weak at direct "find this in this book" lookups, and pure keyword search misses conceptual questions. Routing between them handles both.
- **Grounding.** Answers are built from retrieved passages, not the model's memory, so they stay tied to the source.
- **Resilience.** Retries, context-length caps, and handling for empty model responses, so a single bad API call does not take the app down.
- **Study modes.** Learn, Prelims, Mains, and Evaluate each change how the answer is framed, from facts and elimination logic for prelims to strict marking for evaluate.

## Tech

Python, Streamlit (multi-page UI), ChromaDB for the vector store, sentence-transformers for local embeddings (Gemini embeddings optional), rank-bm25 for keyword lookup, PyMuPDF and BeautifulSoup for ingesting PDFs and web pages, and Google Gemini (Flash) for generation. Packaged with Docker, with a small pytest suite and health checks.

## Run it locally

```bash
git clone <your-repo-url>
cd saarthi
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
# open .env and set GEMINI_API_KEY

# add your own study PDFs to data/pdfs/, then build the index:
python scripts/build_all.py      # takes a few minutes the first time

streamlit run app.py             # open http://localhost:8501
```

## A note on the knowledge base

This repo ships with the code, not the study material. The books I used for my own prep are copyrighted, so they are kept out of the repo (see `.gitignore`). To run Saarthi you bring your own PDFs: drop them in `data/pdfs/` and run the build step above.

For the public live demo, the plan is a small knowledge base built only from open, public-domain sources (for example the text of the Constitution of India and government press releases), so anyone can try it without any copyrighted content involved.

## Deploy

See [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) for deploying to Railway, plus free alternatives (Streamlit Community Cloud, Hugging Face Spaces) that suit a Streamlit app like this well.

## Tests

```bash
pytest tests/ -q
```

## License

MIT. See [LICENSE](LICENSE).
