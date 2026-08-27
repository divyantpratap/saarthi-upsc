# Saarthi v2 — working plan

Live status of the Next.js rebuild. Kept current as work lands so a second
agent can pick up any unclaimed task without re-deriving context.

**Last updated:** 2026-08-27 14:47 IST
**Branch:** `main` · **Deploy target:** Vercel · **Local:** `npm run dev --prefix web`

---

## ⛔ Blocked: daily embedding quota exhausted

The Tier A embed run is **stopped**, not running. It reached 190 of 9,542 chunks
before the API returned:

```
quotaId: EmbedContentRequestsPerDayPerProjectPerModel-FreeTier
```

That is a **per-day** cap, not per-minute — no amount of pacing or backoff gets
past it today. An earlier revision of this file blamed a per-minute ceiling;
that was wrong. `build_index.py` now raises `DailyQuotaExhausted` and exits
cleanly instead of burning hours in cooldown.

**To unblock, either:**
- wait for the reset (00:00 Pacific) and re-run `ingest/build_index.py --only-open`, or
- point `GEMINI_API_KEY` at a billed project and re-run now.

The 190 vectors already earned are banked in `ingest/.build/embeddings.sqlite3`
and will be reused — stopping costs nothing.

**Note for Codex:** the Tier A artifact is not coming today unless the key is
switched. The golden-retrieval harness can be validated against the current
798-chunk dev index in `web/public/index/` in the meantime; the NCERT label
audit is unblocked and safe to do now, since no embed job is running.

## Now in progress

| Task | Owner | State |
|---|---|---|
| Golden retrieval check (10 questions) | Codex | harness ready; unblock by running against the dev index |
| NCERT source-label audit | Codex | mapping mislabeled download codes — safe to move files now |

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

1. **Rebuild + commit the index** — blocked on the daily quota above. When it
   resets: `.venv/bin/python ingest/build_index.py --only-open`, confirm
   `meta.json` counts, commit `web/public/index/`. The committed index is
   currently a 798-chunk dev build, so the deployed app can barely quote
   anything.
2. **Golden retrieval check** — harness is implemented in
   `web/lib/retrieve.golden.test.ts`. Run `npm run test:retrieval --prefix web`
   after the Tier A rebuild; it fails fast while the 3-open-chunk dev index is
   still committed and makes no embedding API calls.
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

- **Free-tier embedding has a per-day cap**, and it is the real bottleneck —
  `EmbedContentRequestsPerDayPerProjectPerModel-FreeTier`. Per-minute pacing
  (55 req/min, set in `build_index.py`) matters too, but the daily cap is what
  stops a full corpus build. Budget roughly one day per few hundred chunks on a
  free key, or use a billed project. `DailyQuotaExhausted` exits immediately
  rather than retrying into a wall.
- **Tier B never ships prose.** Only vectors, citations, and a keyword
  signature. `tests/test_tiers.py` guards this; do not relax it.
- **`GEMINI_EMBED_DIMS` must match `meta.json`.** `retrieve.ts` throws rather
  than returning silently wrong cosine scores.
- **Several NCERT directory labels do not match their PDFs.** Examples found:
  `keps1dd` contains *Political Theory* (not *Indian Constitution at Work*),
  `kepy1dd` contains Psychology, and the Class X `jess*` subjects are rotated.
  Codex is auditing the manifest. Do not rename corpus directories until the
  active embed process exits; vectors are content-addressed and can be reused.

## Verification

```bash
.venv/bin/python -m pytest tests/ -q     # 21 tests
npx vitest run --prefix web              # chunker parity
npm run lint --prefix web && npx tsc --noEmit
npm run build --prefix web
```
