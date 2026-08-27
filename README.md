# Saarthi

Saarthi is a source-grounded UPSC study assistant. The Next.js app retrieves
from a prebuilt hybrid BM25/vector index, streams Gemini answers with citations,
generates Prelims drills, runs negatively marked mocks, and keeps a reader's
uploaded PDFs and custom tests private in their browser.

**Live:** https://saarthi-upsc.vercel.app

## Run the web app

```bash
npm ci --prefix web
npm run dev --prefix web
```

Create `web/.env.local` with `GEMINI_API_KEY` and the model settings documented
in `PLAN.md`. The app reads the committed artifacts under
`web/public/index/`; it performs no corpus indexing at boot or on Vercel.

## Build the offline index

Source PDFs remain gitignored. Install the isolated pipeline dependencies, fetch
the open corpus, and run the resumable builder:

```bash
python -m venv .venv
.venv/bin/pip install -r ingest/requirements.txt
bash ingest/fetch_open_corpus.sh
.venv/bin/python ingest/build_index.py --only-open
```

Tier A ships quotable prose. Tier B ships only vectors, citations, and keyword
signatures; restricted prose never enters the repository.

## Verify

```bash
.venv/bin/python -m pytest tests/ -q
npm run lint --prefix web
(cd web && npx tsc --noEmit)
npx vitest run --prefix web
npm run build --prefix web
```

MIT licensed. See `LICENSE`.
