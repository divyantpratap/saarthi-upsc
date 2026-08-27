# Saarthi v2 — working plan

Live status of the Next.js rebuild. Kept current as work lands so a second
agent can pick up any unclaimed task without re-deriving context.

**Last updated:** 2026-08-27 14:57 IST
**Branch:** `main` · **Deploy target:** Vercel · **Local:** `npm run dev --prefix web`

---

## ⛔ Blocked: daily embedding quota exhausted

The Tier A embed run is **stopped**, not running. The API returned:

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

The SQLite cache contains 190 vectors total, but only 13 match the corrected
9,486-chunk corpus. They are banked in `ingest/.build/embeddings.sqlite3` and
will be reused. Duplicate chunks are now reported separately from actual cache
hits so progress is not overstated again.

**Note for the next agent:** the Tier A artifact is not coming today unless the
key is switched. All ten golden queries pass top-three against the corrected
raw corpus's BM25 ranking. The strict bundled-index assertions correctly wait
for the rebuilt open index; the current 798-chunk dev artifact contains only
three open chunks.

## Now in progress

| Task | Owner | State |
|---|---|---|
| Golden retrieval check (10 questions) | Codex | raw corpus 10/10; awaiting bundled artifact gate |
| Vercel deploy (dev index) | Claude | ✅ **live** at https://saarthi-upsc.vercel.app |

### ✅ Deployed — https://saarthi-upsc.vercel.app

Live on `divyantpratap's projects` (Hobby), root directory `web`, redeploying on
every push to `main`. `GEMINI_API_KEY` is the only environment variable set.

Three production bugs surfaced only after deploying, all fixed:

1. **Blank env vars.** `GEMINI_MODEL` existed in Vercel as `""`. `??` only falls
   back on `undefined`, so the empty string reached the SDK as the model name
   and every answer failed with *"model is required and must be a string"*.
   `envOr()` now treats blank as unset; `GEMINI_EMBED_DIMS` had the same flaw
   and would have become `Number("") = 0`, breaking cosine scoring silently.
2. **No mid-stream failover.** `withRetry` only guarded opening the stream, so a
   503 arriving after the first token escaped it. Streams now buffer to a
   300-character commit point, and a later drop emits a `reset` frame so the
   client discards the fragment and the answer restarts on the next model.
3. **Dropped sockets read as fatal.** undici reports these as a bare
   `TypeError: terminated` with no status code, so `isOverloaded` missed them
   and skipped failover entirely.

4. **Fixed per-call timeouts on structured output.** Measured live: 3.7-flash
   503s at ~11s, 3.6-flash returned in 43.6s once and 5.7s the next, 2.5-flash
   in 8-14s. An 18s cap killed 3.6-flash mid-response, so the drill served the
   fallback bank while a working model was still generating. `generateJson` now
   runs against a 50s wall-clock deadline and hands each model whatever remains.

**Measured on the live deployment, after all four fixes:**

| Path | Before | After |
|---|---|---|
| `/api/ask` | 2/4 complete | **4/4**, and 6/6 on an earlier run |
| `/api/drill` | 2/3 generated | **5/5 generated**, no bank fallback |

`gemini-3.7-flash` remains unstable under launch demand — it is still the
configured primary, and the chain walks down to `gemini-3.6-flash` and
`gemini-2.5-flash` when it fails. The UI names the model that actually answered.

**Claude → Codex:** the deploy builds from pushed `main`, so your uncommitted
corpus work is unaffected. Once the index is rebuilt and pushed, Vercel
redeploys automatically — no Vercel action needed from you.

---

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

## Next up

1. **Rebuild + commit the index** — blocked on the daily quota above. When it
   resets: `.venv/bin/python ingest/build_index.py --only-open`, confirm
   `meta.json` counts, commit `web/public/index/`. The committed index is
   currently a 798-chunk dev build, so the deployed app can barely quote
   anything.
2. **Golden retrieval check** — harness is implemented in
   `web/lib/retrieve.golden.test.ts`. Run `npm run test:retrieval --prefix web`
   after the Tier A rebuild; it fails fast while the 3-open-chunk dev index is
   still committed and makes no embedding API calls. The same ten lexical
   cases currently pass 10/10 against the corrected raw corpus.
3. **Deploy to Vercel** — project from `web/`, env vars per below, confirm a
   cold start answers with zero indexing embed calls.

## Backlog — unclaimed, ordered by value

Each item is self-contained. Claim one by adding a row to **Now in progress**.

### B1 · Guard the public endpoints against abuse — *highest value*

`/api/ask` and `/api/drill` are public, unauthenticated, and spend a shared
Gemini key. One person looping requests exhausts the daily quota and takes the
app down for everyone; today's outage showed how little headroom there is.

Add a lightweight per-IP token bucket (client IP is in the `x-forwarded-for`
header on Vercel). In-memory per lambda is imperfect but enough to stop casual
abuse — no external store. Suggested: 20 requests / 10 min for `/api/ask`, 10
for `/api/drill`. Return 429 with a plain message the UI can render, and exempt
requests that carry a caller's own key (`body.apiKey`), since those spend the
visitor's quota rather than ours.

### B2 · Test the reliability layer

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

### B3 · Retire Streamlit from `main`

Move `app.py`, `pages/`, `settings.py` and the Streamlit-only bits of `src/` to
a `streamlit-legacy` branch, then delete from `main`.

Delete the root `.env.example`, `requirements.txt`, `Procfile`, `railway.toml`
and `Dockerfile` as part of this. They are why Vercel's import wizard detected
the project as **Python** and offered eight bogus environment variables scraped
from `.env.example` — one of which (`GEMINI_MODEL=""`) caused the first
production outage. Keep `ingest/requirements.txt` for the offline pipeline.

### B4 · Custom mock tests in the UI

Issue (xi), second half. `/mock` currently serves only the built-in bank. Add
creation of a custom test that persists to the same IndexedDB store as uploads
(`web/lib/local-library.ts`) — a new object store, same DB. Reuse `QuizCard` as
is; it is already self-contained per question.

### B5 · Tier B backfill

16,342 restricted chunks, roughly 5h of embedding, now viable on the working
key. `ingest/build_index.py` with no `--only-open`. Gives citation-only coverage
of the 63 commercial titles. Independent of everything else; the cache is
content-addressed so Tier A vectors are reused.

### B6 · Responsive and accessibility pass

The UI was built and verified at 1440×900 only. Needs checking at 375px and
768px — particularly the sidebar overlay behaviour below the 900px breakpoint in
`AppShell.tsx`, and the drill's option rows.

Accessibility on `QuizCard.tsx`: the verdict after "Check answer" is announced
to nobody — it needs `aria-live`. Also confirm the option rows are reachable and
selectable by keyboard, and that focus is visible throughout.

### B7 · Report the model that actually answers

`/api/status` returns `answerModel: MODEL` — the *configured* primary. Since
`gemini-3.7-flash` is currently failing nearly every request and answers come
from `gemini-3.6-flash`, the sidebar badge states something untrue. Either
report the last model that successfully served, or label it "configured" and let
the per-answer attribution (already correct) stand alone.

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
