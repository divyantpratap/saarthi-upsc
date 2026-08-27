# Saarthi v2 — working plan

> **HANDOFF — Codex owns everything below.** Claude has stopped all background
> work; no process of its is running and nothing will contend for the API key or
> the repo. Every task is self-contained: file paths, commands and verification
> are stated inline so none of it needs re-deriving.

**Last updated:** 2026-08-27 20:15 IST
**Live:** https://saarthi-upsc.vercel.app · **Branch:** `main` (auto-deploys)
**Local:** `npm run dev --prefix web` · **Python:** `.venv/bin/python`

---

## Start here

Work the tasks in order. T1 is the only one that unblocks the product; T2–T8 are
independent and can be done in any order or in parallel.

| # | Task | Needs Gemini quota? |
|---|---|---|
| T1 | Build and commit the Tier A index | **yes** |
| T2 | Rate-limit the public endpoints | no |
| T3 | Test the reliability layer | no |
| T4 | Retire Streamlit from `main` | no |
| T5 | Custom mock tests in the UI | no |
| T6 | Tier B backfill | **yes** |
| T7 | Responsive + accessibility pass | no |
| T8 | Report the model that actually answers | no |

---

## T1 · Build and commit the Tier A index — *unblocks the product*

The deployed app carries a **798-chunk dev index** whose only quotable source is
`sample_study_notes.txt`. Answers are honest about having no material, but the
app cannot demo until this lands.

**The constraint, measured across two exhausted keys:** the Gemini free tier
yields roughly **500 embed requests per key per day**. Tier A is **9,486
chunks**. This is a property of the API key, not of who runs the script — the
same limit applies to any agent. `ingest/.build/embeddings.sqlite3` already
holds **940 vectors (9.9%)**, content-addressed, so nothing is ever re-embedded.

| Route | Cost | Time |
|---|---|---|
| Billed key | ~$0.36 (2.4M tokens @ $0.15/1M) | ~2 hours |
| Free tier, whole corpus | free | ~19 days |
| Free tier, Constitution only (1,212 chunks) | free | ~2 days |

```bash
# Whole Tier A corpus — needs a billed key to finish in one run
.venv/bin/python ingest/build_index.py --only-open

# Or concentrate a free day's quota on the highest-value source
.venv/bin/python ingest/build_index.py --only-open --collections constitution
```

Re-running is always safe and resumes from the cache. On exhaustion the script
exits 0 with `DailyQuotaExhausted` and a message — that is expected, not a bug.

**When it completes:**
1. Check `web/public/index/meta.json` — `count` should match the run, and `dims`
   must be `768`.
2. `npm run test:retrieval --prefix web` — the golden-retrieval harness gates on
   a real open index and currently skips.
3. Commit `web/public/index/` and push. Vercel redeploys automatically.
4. Confirm live: `curl -s https://saarthi-upsc.vercel.app/api/status` should show
   the new `chunks` and `openChunks`.

**Corpus source of truth:** `bash ingest/fetch_open_corpus.sh` re-downloads the
Constitution and 21 NCERT titles into gitignored `data/pdfs/`. Only the derived
index ships; the PDFs never enter the repo.

## Now in progress

| Task | Owner | State |
|---|---|---|
| T1 · Tier A index | Codex | claimed; quota attempt after safety checks |
| T2 · Public endpoint rate limits | Codex | implementing |
| T3 · Reliability tests | Codex | claimed |
| T4 · Retire Streamlit | Codex | claimed; preserve legacy branch first |
| T5 · Custom mock tests | Codex | claimed |
| T6 · Tier B backfill | Codex | claimed; runs only after T1 writer exits |
| T7 · Responsive + accessibility | Codex | claimed |
| T8 · Answering-model status | Codex | claimed |

## Done

- [x] **Index pipeline** — `ingest/build_index.py`, `ingest/tiers.py`. Chunks,
      embeds at 768 dims, emits `meta.json` / `vectors.f16.bin` /
      `chunks.{a,b}.json.gz` into `web/public/index/`.
- [x] **Embedding progress accounting** — cache hits and duplicate chunks are
      reported separately; only 13 current-corpus vectors are reusable.
- [x] **Chunker bug** — texts shorter than `CHUNK_SIZE` emitted ~120
      near-duplicate crumbs. 6 PDFs produced 55,748 chunks instead of 1,752.
      Fixed in `src/ingest/chunker.py`; tests in `tests/test_chunker.py`.
- [x] **Tiering by path, not filename** — filename matching promoted a coaching
      compilation and a file matching "parliament" to publishable. Now a
      directory allowlist (`ncert`, `constitution`, `open`, `govt`).
      Tests in `tests/test_tiers.py`.
- [x] **Open corpus** — Constitution of India (404pp, to the 105th Amendment)
      plus 21 NCERT titles. 9,486 quotable passages after the label audit.
      Fetch with `bash ingest/fetch_open_corpus.sh` (gitignored; only the index
      ships).
- [x] **NCERT source-label audit** — corrected eight code/title mappings,
      replaced an accidental Psychology download with *Indian Constitution at
      Work*, and made fetch directories code-addressed and locale-stable.
      `bash ingest/fetch_open_corpus.sh --prune` recoverably moves stale folders
      to ignored `data/quarantine/`; `tests/test_open_corpus_manifest.py` guards
      the mapping.
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

## T2–T8 · Remaining work (no Gemini quota required)

Each item is self-contained. Claim one by adding a row to **Now in progress**.

### T2 · Guard the public endpoints against abuse — *highest value of these*

`/api/ask` and `/api/drill` are public, unauthenticated, and spend a shared
Gemini key. One person looping requests exhausts the daily quota and takes the
app down for everyone; today's outage showed how little headroom there is.

Add a lightweight per-IP token bucket (client IP is in the `x-forwarded-for`
header on Vercel). In-memory per lambda is imperfect but enough to stop casual
abuse — no external store. Suggested: 20 requests / 10 min for `/api/ask`, 10
for `/api/drill`. Return 429 with a plain message the UI can render, and exempt
requests that carry a caller's own key (`body.apiKey`), since those spend the
visitor's quota rather than ours.

### T3 · Test the reliability layer

`web/lib/gemini.ts` broke in production four separate ways today and none of it
is covered. Everything below is unit-testable with a stubbed `GoogleGenAI`:

- `isOverloaded` classifies 500/502/503/504, `UNAVAILABLE`, `DEADLINE_EXCEEDED`,
  and the bare `TypeError: terminated` that undici raises on a dropped socket.
  That last one shipped as fatal and skipped failover entirely.
- `modelChain` de-duplicates, drops blanks, and throws when nothing is usable.
- `generateStream` buffers to `COMMIT_THRESHOLD` before yielding; a failure
  below it fails over silently, above it calls `onRestart` while another model
  remains, and raises `PartialAnswer` on the last rung.
- `generateJson` respects `JSON_DEADLINE_MS` and skips a model with under
  `MIN_ATTEMPT_MS` left.

### T4 · Retire Streamlit from `main`

Move `app.py`, `pages/`, `settings.py` and the Streamlit-only bits of `src/` to
a `streamlit-legacy` branch, then delete from `main`.

Delete the root `.env.example`, `requirements.txt`, `Procfile`, `railway.toml`
and `Dockerfile` as part of this. They are why Vercel's import wizard detected
the project as **Python** and offered eight bogus environment variables scraped
from `.env.example` — one of which (`GEMINI_MODEL=""`) caused the first
production outage. Keep `ingest/requirements.txt` for the offline pipeline.

### T5 · Custom mock tests in the UI

Issue (xi), second half. `/mock` currently serves only the built-in bank. Add
creation of a custom test that persists to the same IndexedDB store as uploads
(`web/lib/local-library.ts`) — a new object store, same DB. Reuse `QuizCard` as
is; it is already self-contained per question.

### T6 · Tier B backfill — *needs quota*

16,342 restricted chunks, roughly 5h of embedding, now viable on the working
key. `ingest/build_index.py` with no `--only-open`. Gives citation-only coverage
of the 63 commercial titles. Independent of everything else; the cache is
content-addressed so Tier A vectors are reused.

### T7 · Responsive and accessibility pass

The UI was built and verified at 1440×900 only. Needs checking at 375px and
768px — particularly the sidebar overlay behaviour below the 900px breakpoint in
`AppShell.tsx`, and the drill's option rows.

Accessibility on `QuizCard.tsx`: the verdict after "Check answer" is announced
to nobody — it needs `aria-live`. Also confirm the option rows are reachable and
selectable by keyboard, and that focus is visible throughout.

### T8 · Report the model that actually answers

`/api/status` returns `answerModel: MODEL` — the *configured* primary. Since
`gemini-3.7-flash` is currently failing nearly every request and answers come
from `gemini-3.6-flash`, the sidebar badge states something untrue. Either
report the last model that successfully served, or label it "configured" and let
the per-answer attribution (already correct) stand alone.

---

### T9 · CI does not cover the Next.js app at all

`.github/workflows/ci.yml` runs `pytest` and nothing else — zero mentions of
`web/`. Every regression fixed today (the blank-env-var outage, the mid-stream
failover, the undici classification) would sail through CI untouched, and once
T4 retires Streamlit the workflow will be testing almost nothing.

Add a second job for the web app: `npm ci`, `npm run lint`, `npx tsc --noEmit`,
`npx vitest run`, `npm run build`, with `working-directory: web`. No secrets
needed — the build makes no Gemini calls.

### T10 · Decide what happens to the Streamlit deployment

`saarthi-upsc.streamlit.app` is still live and serving the old code, with all
eleven original bugs. Two deployments under near-identical names is a poor look
if anyone follows a stale link. Either delete the app from Streamlit Community
Cloud, or leave a one-line notice pointing at the Vercel URL. Pairs with T4.

### Housekeeping, not tasks

- **Rotate the Gemini keys.** One was pasted into a chat transcript, and both
  sit in local `.env` / `web/.env.local` (gitignored, never committed).
  https://aistudio.google.com/apikey
- **Vercel still holds the first key**, whose daily *embed* quota is spent.
  Query embeddings are one request per question, so semantic retrieval on the
  live site is verified working — but it is not the key with headroom.

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
- **NCERT identity comes from its book code, not the display title.** Managed
  directory names now begin with the code, and the fetcher verifies every PDF
  prefix before reuse. The corrected corpus fingerprint is
  `e73f35fe3ee3ad47` (9,486 open chunks).

## Verification

```bash
.venv/bin/python -m pytest tests/ -q     # 24 tests
npx vitest run --prefix web              # chunker parity
npm run lint --prefix web && npx tsc --noEmit
npm run build --prefix web
```

Last full run (14:57 IST): 24 Python tests passed; 7 Vitest tests passed and
the 10 bundled-index cases were correctly gated; ESLint, TypeScript, shell
syntax, diff checks, and an isolated Next.js production build all passed.
