# Saarthi v2 — working plan

Live status of the Next.js rebuild. Kept current as work lands so a second
agent can pick up any unclaimed task without re-deriving context.

**Last updated:** 2026-08-27 14:35 IST
**Branch:** `main` · **Deploy target:** Vercel · **Local:** `npm run dev --prefix web`

---

## Now in progress

| Task | Owner | State |
|---|---|---|
| Tier A embedding run (9,542 chunks) | background job | running, ~3h, resumable |

The embed job writes to `ingest/.build/embeddings.sqlite3` (content-addressed).
**Do not run `ingest/build_index.py` concurrently** — two writers will fight over
the rate limit and both will stall. Re-running after it finishes is cheap:
cached vectors are reused.

---

## Done

- [x] **Index pipeline** — `ingest/build_index.py`, `ingest/tiers.py`. Chunks,
      embeds at 768 dims, emits `meta.json` / `vectors.f16.bin` /
      `chunks.{a,b}.json.gz` into `web/public/index/`.
- [x] **Chunker bug** — texts shorter than `CHUNK_SIZE` emitted ~120
      near-duplicate crumbs. 6 PDFs produced 55,748 chunks instead of 1,752.
      Fixed in `src/ingest/chunker.py`; tests in `tests/test_chunker.py`.
- [x] **Tiering by path, not filename** — filename matching promoted a coaching
      compilation and a file matching "parliament" to publishable. Now a
      directory allowlist (`ncert`, `constitution`, `open`, `govt`).
      Tests in `tests/test_tiers.py`.
- [x] **Open corpus** — Constitution of India (404pp, to the 105th Amendment)
      plus 21 NCERT titles. 9,542 quotable passages. Fetch with
      `bash ingest/fetch_open_corpus.sh` (gitignored; only the index ships).
- [x] **Retrieval layer** — `web/lib/retrieve.ts`: BM25 + cosine, fused with
      RRF. No chromadb, no vector database.
- [x] **Model layer** — `web/lib/gemini.ts`. Real retries, backoff from the
      API's own `retryDelay`, failover across 404/500/502/503/504,
      `thinkingLevel: LOW`, per-operation timeouts.
- [x] **App shell** — working sidebar toggle, single controlled accordion,
      active nav state, live index readout.
- [x] **Ask** — `/api/ask` streams NDJSON (sources → model → text → done).
- [x] **Prelims drill** — `/drill` + `/api/drill`. Structured JSON via
      `responseSchema`, falls back to the vetted bank on 429 or bad JSON.
- [x] **Mock tests** — `/mock`, UPSC negative marking.
- [x] **Uploads** — `/library`. Parsed in-browser with pdfjs (pinned past
      GHSA-hq66-cqwq-w95j), chunked, stored in IndexedDB, matched with BM25 and
      sent as context. Verified: 7-page PDF → 22 passages.

---

## Next up

1. **Rebuild + commit the index** — once the embed run finishes, run
   `.venv/bin/python ingest/build_index.py --only-open`, confirm `meta.json`
   counts, commit `web/public/index/`. Currently the committed index is a
   798-chunk dev build.
2. **Golden retrieval check** — ten known questions, assert the expected source
   lands top-3. No harness exists yet.
3. **Deploy to Vercel** — project from `web/`, env vars per below, confirm a
   cold start answers with zero indexing embed calls.

## Upcoming

4. **Tier B backfill** — 16,342 restricted chunks, another ~5h of embedding.
   Adds citation-only coverage of the 63 commercial titles. Not blocking.
5. **Custom mock tests in the UI** — issue (xi), second half. Same IndexedDB
   store as uploads.
6. **Retire Streamlit** — move `app.py` / `pages/` to a `streamlit-legacy`
   branch and delete from `main`.

---

## Environment

```
GEMINI_MODEL=gemini-3.7-flash
GEMINI_MODEL_FALLBACK=gemini-3.6-flash      # must differ from the primary
GEMINI_EMBED_MODEL=gemini-embedding-001
GEMINI_EMBED_DIMS=768                        # must match meta.json
GEMINI_TIMEOUT_MS=25000
```

`gemini-3.7-flash` is currently returning 503/504 under launch demand — measured
failing after 92s while 3.6-flash answered in 5s. Failover handles it and the UI
names the model that actually answered.

## Constraints worth knowing

- **Free-tier embedding** is the bottleneck: ~55 req/min sustained. Bursting at
  90 tripped a quota window that took six minutes to clear. `RateLimiter` in
  `build_index.py` paces under it and cools down for 5/10/15 min before giving
  up cleanly.
- **Tier B never ships prose.** Only vectors, citations, and a keyword
  signature. `tests/test_tiers.py` guards this; do not relax it.
- **`GEMINI_EMBED_DIMS` must match `meta.json`.** `retrieve.ts` throws rather
  than returning silently wrong cosine scores.

## Verification

```bash
.venv/bin/python -m pytest tests/ -q     # 21 tests
npx vitest run --prefix web              # chunker parity
npm run lint --prefix web && npx tsc --noEmit
npm run build --prefix web
```
