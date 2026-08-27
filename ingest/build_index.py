"""Build the shipped retrieval index.

Runs locally, never on Vercel. Walks the corpus, chunks it with the same
splitter the Streamlit app used, embeds every chunk with Gemini at 768
dimensions, and emits artifacts the TypeScript runtime loads directly:

    meta.json        dims, model, counts, per-source manifest
    vectors.f16.bin  float16, row-major, one row per chunk
    chunks.a.json.gz Tier A: full text (freely redistributable)
    chunks.b.json.gz Tier B: citations + keyword signature, no prose

Embedding is the expensive half: one request per chunk against a 100/min free
tier ceiling. The job is rate-limited, honours the API's own retryDelay, and
checkpoints after every batch so a crash or a 429 storm never loses work.

    python ingest/build_index.py --limit 40      # quick smoke build
    python ingest/build_index.py                 # full corpus
    python ingest/build_index.py --resume        # continue after interruption
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ingest"))

from dotenv import load_dotenv

load_dotenv()

from settings import DATA_DIR, GEMINI_EMBED_MODEL, MAX_PAGES_FULL, PDF_DIR  # noqa: E402
from src.ingest.chunker import chunk_text  # noqa: E402
from src.ingest.pdf_parser import list_pdfs, pdf_to_documents  # noqa: E402
from tiers import OPEN, RESTRICTED, classify  # noqa: E402

OUT_DIR = ROOT / "web" / "public" / "index"
BUILD_DIR = ROOT / "ingest" / ".build"
EMBED_DIMS = 768
BATCH_SIZE = 10
# The free tier documents 100 embed requests/min. An earlier run paced at 55
# after a per-day cap was misread as a per-minute one; a fresh key then took 300
# requests at that rate without a single rejection, so the headroom is real.
# Backoff and the content-addressed cache make overshooting cheap to discover.
REQUESTS_PER_MINUTE = int(__import__("os").getenv("EMBED_RPM", "85"))
KEYWORD_SIGNATURE_SIZE = 18

_STOPWORDS = frozenset(
    """a an and are as at be by for from has have in is it its of on or that the
    to was were will with which this these those they their there than then such
    can could should would may might must not but also into over under about""".split()
)
_TOKEN = re.compile(r"[a-z][a-z0-9]{2,}")


# ---------------------------------------------------------------- collection


def _keyword_signature(text: str, size: int = KEYWORD_SIGNATURE_SIZE) -> list[str]:
    """Top terms for a chunk, for lexical matching without shipping the prose.

    Tier B chunks travel without their text, so BM25 would otherwise be blind to
    every commercial title. A bag of the most frequent content words keeps those
    chunks findable while carrying no reconstructable sentence.
    """
    counts = Counter(t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS)
    return [term for term, _ in counts.most_common(size)]


def collect_chunks(limit: int | None = None) -> list[dict]:
    """Chunk the whole corpus deterministically, tier by tier."""
    chunks: list[dict] = []

    for txt_path in sorted(DATA_DIR.glob("*.txt")):
        if txt_path.name == "sample_urls.txt":
            continue
        text = txt_path.read_text(encoding="utf-8")
        if not text.strip():
            continue
        for chunk in chunk_text(
            text,
            f"notes:{txt_path.name}",
            {"type": "notes", "filename": txt_path.name, "subject": "Notes"},
        ):
            chunk["tier"] = classify(txt_path.name, "notes")
            chunks.append(chunk)

    pdfs = list_pdfs(PDF_DIR)
    if limit:
        pdfs = pdfs[:limit]
    for pdf_path in pdfs:
        try:
            display_name = str(pdf_path.relative_to(PDF_DIR))
        except ValueError:
            display_name = pdf_path.name
        tier = classify(display_name, "pdf")
        # Open material is what the app actually quotes, so read it whole. A
        # truncated Constitution would silently lose two-thirds of its articles.
        # Restricted titles stay capped: they ship as citations either way.
        max_pages = None if tier == OPEN else MAX_PAGES_FULL
        for document in pdf_to_documents(pdf_path, max_pages=max_pages):
            for chunk in chunk_text(
                document["text"], document["source"], document["metadata"]
            ):
                chunk["tier"] = tier
                chunks.append(chunk)

    chunks.sort(key=lambda c: c["id"])  # stable order => stable checkpoints
    return chunks


def corpus_fingerprint(chunks: list[dict]) -> str:
    digest = hashlib.sha256()
    digest.update(f"{GEMINI_EMBED_MODEL}:{EMBED_DIMS}:{len(chunks)}".encode())
    for chunk in chunks[::37]:  # sample: full hashing of 8k chunks buys nothing
        digest.update(chunk["id"].encode())
    return digest.hexdigest()[:16]


# ----------------------------------------------------------------- embedding


class RateLimiter:
    """Sliding-window limiter; the free tier counts one request per chunk."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._times: list[float] = []

    def acquire(self, count: int) -> None:
        """Block until `count` more requests fit inside the trailing minute.

        The window is never cleared wholesale: dropping the history after a
        pause made the limiter believe the minute was empty, so it burst
        straight back into the quota it had just been throttled by.
        """
        while True:
            now = time.monotonic()
            self._times = [t for t in self._times if now - t < 60.0]
            if len(self._times) + count <= self.per_minute:
                break
            sleep_for = max(0.5, 60.0 - (now - self._times[0]) + 0.5)
            print(f"    rate limit: pausing {sleep_for:.0f}s", flush=True)
            time.sleep(sleep_for)
        self._times.extend([time.monotonic()] * count)


def _retry_delay(exc: Exception) -> float:
    """Use the delay the API asked for; it knows when the window reopens."""
    match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)s", str(exc))
    return float(match.group(1)) + 1.0 if match else 0.0


class DailyQuotaExhausted(RuntimeError):
    """The per-day free-tier allowance is gone; no amount of waiting helps today."""


def _is_daily_quota(exc: Exception) -> bool:
    return "PerDay" in str(exc)


def _normalize(vector: list[float]) -> list[float]:
    """gemini-embedding-001 only returns unit vectors at full 3072 dims."""
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else vector


def embed_batch(client, texts: list[str], limiter: RateLimiter) -> list[list[float]]:
    from google.genai import types

    for attempt in range(8):
        limiter.acquire(len(texts))
        try:
            result = client.models.embed_content(
                model=GEMINI_EMBED_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=EMBED_DIMS,
                ),
            )
            return [_normalize(e.values) for e in result.embeddings]
        except Exception as exc:
            message = str(exc)
            if "429" not in message and "RESOURCE_EXHAUSTED" not in message:
                raise
            # A per-day quota does not reopen in 60 seconds. Backing off against
            # it just burns hours to arrive at the same place.
            if _is_daily_quota(exc):
                raise DailyQuotaExhausted(str(exc)) from exc
            wait = max(_retry_delay(exc), min(120.0, 15.0 * (attempt + 1)))
            print(f"    429 (attempt {attempt + 1}) — waiting {wait:.0f}s", flush=True)
            time.sleep(wait)
    raise RuntimeError("rate limited beyond the batch retry budget")


def _cache() -> sqlite3.Connection:
    """Content-addressed vector cache.

    Keyed by the hash of the chunk text, not by its position, so adding a source
    to the corpus only embeds the new material. A positional checkpoint would
    invalidate every vector the moment a single PDF joined the library.
    """
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(BUILD_DIR / "embeddings.sqlite3")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS vectors ("
        "  hash TEXT NOT NULL, model TEXT NOT NULL, dims INTEGER NOT NULL,"
        "  vec BLOB NOT NULL, PRIMARY KEY (hash, model, dims))"
    )
    return conn


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _embedding_work(
    chunks: list[dict], hashes: list[str], cached: set[str]
) -> tuple[dict[str, str], int, int]:
    """Split the corpus into cached, duplicate, and unique uncached work."""
    pending: dict[str, str] = {}
    cached_chunks = 0
    for chunk, digest in zip(chunks, hashes):
        if digest in cached:
            cached_chunks += 1
        elif digest not in pending:
            pending[digest] = chunk["text"]
    duplicate_chunks = len(chunks) - cached_chunks - len(pending)
    return pending, cached_chunks, duplicate_chunks


def embed_all(chunks: list[dict], resume: bool = True) -> list[list[float]]:
    from google import genai
    import numpy as np

    conn = _cache()
    if not resume:
        conn.execute("DELETE FROM vectors WHERE model=? AND dims=?", (GEMINI_EMBED_MODEL, EMBED_DIMS))
        conn.commit()

    hashes = [_text_hash(chunk["text"]) for chunk in chunks]
    cached = {
        row[0]
        for row in conn.execute(
            "SELECT hash FROM vectors WHERE model=? AND dims=?",
            (GEMINI_EMBED_MODEL, EMBED_DIMS),
        )
    }

    # De-duplicate: repeated boilerplate across a corpus is common and each
    # duplicate would otherwise cost a request. Report it separately from real
    # cache hits so a handoff never overstates quota progress.
    pending, cached_chunks, duplicate_chunks = _embedding_work(chunks, hashes, cached)
    print(
        f"  {cached_chunks:,} cached chunks  ·  {duplicate_chunks:,} duplicates"
        f"  ·  {len(pending):,} unique chunks to embed"
    )

    if pending:
        client = genai.Client()
        limiter = RateLimiter(REQUESTS_PER_MINUTE)
        started = time.monotonic()
        items = list(pending.items())

        for start in range(0, len(items), BATCH_SIZE):
            batch = items[start : start + BATCH_SIZE]
            for cooldown in (300, 600, 900, None):
                try:
                    vectors = embed_batch(client, [t for _, t in batch], limiter)
                    break
                except DailyQuotaExhausted:
                    print(
                        f"\n  Daily free-tier embedding quota is exhausted."
                        f"\n  {start:,} of {len(items):,} embedded and cached."
                        f"\n  Re-run after the quota resets (00:00 Pacific), or set a"
                        f" billed GEMINI_API_KEY to finish now.",
                        flush=True,
                    )
                    raise SystemExit(0)
                except RuntimeError:
                    if cooldown is None:
                        print(
                            f"\n  Quota is still saturated. {start:,} of {len(items):,} "
                            f"embedded and cached — re-run to continue.",
                            flush=True,
                        )
                        raise SystemExit(0)
                    print(f"    quota saturated — cooling down {cooldown // 60} min", flush=True)
                    time.sleep(cooldown)
            conn.executemany(
                "INSERT OR REPLACE INTO vectors (hash, model, dims, vec) VALUES (?,?,?,?)",
                [
                    (digest, GEMINI_EMBED_MODEL, EMBED_DIMS,
                     np.asarray(vector, dtype=np.float32).tobytes())
                    for (digest, _), vector in zip(batch, vectors)
                ],
            )
            conn.commit()

            done = start + len(batch)
            elapsed = time.monotonic() - started
            rate = done / elapsed if elapsed > 0 else 0
            remaining = (len(items) - done) / rate / 60 if rate > 0 else 0
            print(f"  embedded {done:,}/{len(items):,}  ({remaining:.0f} min remaining)", flush=True)

    stored = {
        row[0]: np.frombuffer(row[1], dtype=np.float32)
        for row in conn.execute(
            "SELECT hash, vec FROM vectors WHERE model=? AND dims=?",
            (GEMINI_EMBED_MODEL, EMBED_DIMS),
        )
    }
    missing = [d for d in hashes if d not in stored]
    if missing:
        raise SystemExit(f"{len(missing):,} chunks never embedded; re-run to continue")
    return [stored[digest].tolist() for digest in hashes]


# ------------------------------------------------------------------- emitting


def emit(chunks: list[dict], vectors: list[list[float]], fingerprint: str) -> None:
    import numpy as np

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    matrix = np.asarray(vectors, dtype=np.float32).astype(np.float16)
    (OUT_DIR / "vectors.f16.bin").write_bytes(matrix.tobytes())

    tier_a, tier_b, manifest = [], [], {}
    for position, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        source = meta.get("source", "unknown")
        entry = {
            "i": position,
            "src": source,
            "file": meta.get("filename", source),
            "subj": meta.get("subject", ""),
            "page": meta.get("page_number"),
            "para": meta.get("paragraph_index"),
        }
        if chunk["tier"] == OPEN:
            entry["text"] = chunk["text"]
            tier_a.append(entry)
        else:
            # No prose leaves this branch — only what makes the chunk findable.
            entry["terms"] = _keyword_signature(chunk["text"])
            entry["chars"] = len(chunk["text"])
            tier_b.append(entry)

        record = manifest.setdefault(
            source,
            {
                "file": entry["file"],
                "subject": entry["subj"],
                "tier": chunk["tier"],
                "chunks": 0,
            },
        )
        record["chunks"] += 1

    for name, payload in (("chunks.a.json.gz", tier_a), ("chunks.b.json.gz", tier_b)):
        with gzip.open(OUT_DIR / name, "wt", encoding="utf-8") as sink:
            json.dump(payload, sink, ensure_ascii=False, separators=(",", ":"))

    (OUT_DIR / "meta.json").write_text(
        json.dumps(
            {
                "version": 1,
                "fingerprint": fingerprint,
                "embedModel": GEMINI_EMBED_MODEL,
                "dims": EMBED_DIMS,
                "count": len(chunks),
                "openCount": len(tier_a),
                "restrictedCount": len(tier_b),
                "builtAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sources": manifest,
            },
            indent=2,
        )
    )

    size = sum(f.stat().st_size for f in OUT_DIR.iterdir()) / 1e6
    print(
        f"\n  {len(chunks):,} chunks  ·  {len(tier_a):,} open / {len(tier_b):,} restricted"
        f"\n  {len(manifest)} sources  ·  {size:.1f} MB in {OUT_DIR.relative_to(ROOT)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="only read the first N PDFs")
    parser.add_argument("--rebuild", action="store_true", help="discard cached vectors")
    parser.add_argument("--only-open", action="store_true", help="Tier A material only")
    parser.add_argument(
        "--collections",
        nargs="+",
        metavar="NAME",
        help="limit to these top-level corpus folders, e.g. --collections constitution",
    )
    parser.add_argument("--chunks-only", action="store_true", help="skip embedding")
    args = parser.parse_args()

    print("Collecting chunks…")
    chunks = collect_chunks(limit=args.limit)
    if not chunks:
        raise SystemExit(f"No source material found under {DATA_DIR}")
    if args.only_open:
        chunks = [c for c in chunks if c["tier"] == OPEN]
        print(f"  restricted to Tier A: {len(chunks):,} chunks")
    if args.collections:
        # Free-tier quota is small enough that spreading it across the whole
        # corpus leaves nothing usable. Concentrating it on one collection
        # yields a demo that can actually cite something.
        wanted = {name.lower() for name in args.collections}
        chunks = [
            c for c in chunks
            if c["metadata"].get("filename", "").split("/")[0].lower() in wanted
        ]
        print(f"  restricted to {', '.join(sorted(wanted))}: {len(chunks):,} chunks")
        if not chunks:
            raise SystemExit("No chunks matched those collections.")
    fingerprint = corpus_fingerprint(chunks)
    open_count = sum(c["tier"] == OPEN for c in chunks)
    print(
        f"  {len(chunks):,} chunks  ·  {open_count:,} open"
        f"  ·  {len(chunks) - open_count:,} restricted  ·  {fingerprint}"
    )
    if args.chunks_only:
        return

    print(f"\nEmbedding with {GEMINI_EMBED_MODEL} at {EMBED_DIMS} dims…")
    vectors = embed_all(chunks, resume=not args.rebuild)
    if len(vectors) != len(chunks):
        raise SystemExit(f"vector/chunk mismatch: {len(vectors)} vs {len(chunks)}")

    print("\nWriting artifacts…")
    emit(chunks, vectors, fingerprint)


if __name__ == "__main__":
    main()
