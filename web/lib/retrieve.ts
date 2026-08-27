/**
 * Hybrid retrieval over the bundled index: BM25 for lexical recall, cosine for
 * semantic recall, merged with Reciprocal Rank Fusion.
 *
 * RRF rather than a weighted score sum, because BM25 scores and cosine
 * similarities live on different scales and any fixed weighting between them
 * drifts as the corpus changes. RRF only needs the ranks.
 */
import { loadIndex } from "./index-store";
import { hasText, type Chunk, type Retrieved } from "./types";

const STOPWORDS = new Set(
  `a an and are as at be by for from has have in is it its of on or that the to
   was were will with which this these those they their there than then such can
   could should would may might must not but also into over under about`.split(
    /\s+/,
  ),
);
const TOKEN = /[a-z][a-z0-9]{2,}/g;

const K1 = 1.2;
const B = 0.75;
const RRF_K = 60;
/** Candidates each retriever contributes before fusion. */
const CANDIDATES = 40;

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(TOKEN) ?? []).filter((t) => !STOPWORDS.has(t));
}

interface Bm25Index {
  postings: Map<string, Array<[docId: number, tf: number]>>;
  docLength: Float32Array;
  averageLength: number;
  total: number;
}

function chunkTerms(chunk: Chunk): string[] {
  // Tier B ships a keyword signature instead of prose, so it stays searchable
  // without its pages being republished.
  return hasText(chunk) ? tokenize(chunk.text) : chunk.terms;
}

function buildBm25(chunks: Chunk[]): Bm25Index {
  const postings = new Map<string, Array<[number, number]>>();
  const docLength = new Float32Array(chunks.length);
  let lengthSum = 0;

  chunks.forEach((chunk, docId) => {
    if (!chunk) return;
    const terms = chunkTerms(chunk);
    docLength[docId] = terms.length;
    lengthSum += terms.length;

    const frequency = new Map<string, number>();
    for (const term of terms) frequency.set(term, (frequency.get(term) ?? 0) + 1);
    for (const [term, tf] of frequency) {
      let list = postings.get(term);
      if (!list) postings.set(term, (list = []));
      list.push([docId, tf]);
    }
  });

  return {
    postings,
    docLength,
    averageLength: chunks.length ? lengthSum / chunks.length : 1,
    total: chunks.length,
  };
}

let bm25Cache: Bm25Index | null = null;

function bm25Search(index: Bm25Index, query: string, limit: number): number[] {
  const scores = new Map<number, number>();

  for (const term of new Set(tokenize(query))) {
    const list = index.postings.get(term);
    if (!list) continue;
    const idf = Math.log(
      1 + (index.total - list.length + 0.5) / (list.length + 0.5),
    );
    for (const [docId, tf] of list) {
      const norm =
        tf +
        K1 * (1 - B + (B * index.docLength[docId]) / index.averageLength);
      scores.set(docId, (scores.get(docId) ?? 0) + (idf * tf * (K1 + 1)) / norm);
    }
  }

  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([docId]) => docId);
}

function cosineSearch(
  vectors: Float32Array,
  dims: number,
  count: number,
  query: Float32Array,
  limit: number,
): Array<[docId: number, score: number]> {
  // Index vectors and the query are both L2-normalised, so a dot product is the
  // cosine similarity outright.
  const scored: Array<[number, number]> = [];
  for (let docId = 0; docId < count; docId++) {
    const base = docId * dims;
    let dot = 0;
    for (let d = 0; d < dims; d++) dot += vectors[base + d] * query[d];
    scored.push([docId, dot]);
  }
  scored.sort((a, b) => b[1] - a[1]);
  return scored.slice(0, limit);
}

function reciprocalRankFusion(rankings: number[][]): Array<[number, number]> {
  const fused = new Map<number, number>();
  for (const ranking of rankings) {
    ranking.forEach((docId, position) => {
      fused.set(docId, (fused.get(docId) ?? 0) + 1 / (RRF_K + position + 1));
    });
  }
  return [...fused.entries()].sort((a, b) => b[1] - a[1]);
}

export interface RetrieveOptions {
  topK?: number;
  /** Omit to run lexical-only — used when the query embedding call fails. */
  queryVector?: Float32Array;
}

export async function retrieve(
  query: string,
  { topK = 6, queryVector }: RetrieveOptions = {},
): Promise<Retrieved[]> {
  const { meta, chunks, vectors } = await loadIndex();
  if (!meta.count) return [];

  if (!bm25Cache) bm25Cache = buildBm25(chunks);

  const rankings: number[][] = [bm25Search(bm25Cache, query, CANDIDATES)];
  const similarity = new Map<number, number>();

  if (queryVector) {
    if (queryVector.length !== meta.dims) {
      throw new Error(
        `query vector is ${queryVector.length}-d but the index is ${meta.dims}-d — ` +
          `the embed model changed since the index was built (${meta.embedModel})`,
      );
    }
    const dense = cosineSearch(
      vectors,
      meta.dims,
      meta.count,
      queryVector,
      CANDIDATES,
    );
    for (const [docId, score] of dense) similarity.set(docId, score);
    rankings.push(dense.map(([docId]) => docId));
  }

  return reciprocalRankFusion(rankings)
    .slice(0, topK)
    .map(([docId, score]) => {
      const chunk = chunks[docId];
      const open = hasText(chunk);
      return {
        chunk,
        score: similarity.get(docId) ?? score,
        text: open ? chunk.text : undefined,
        citationOnly: !open,
      };
    })
    .filter((hit) => hit.chunk !== undefined);
}

/** Everything the model is allowed to read, numbered so it can cite by index. */
export function formatContext(hits: Retrieved[], maxChars = 12000): string {
  const parts: string[] = [];
  let size = 0;
  hits.forEach((hit, i) => {
    if (!hit.text) return; // citation-only chunks never reach the prompt
    const label = `[${i + 1}] ${hit.chunk.file}${
      hit.chunk.page ? `, p.${hit.chunk.page}` : ""
    }`;
    const block = `${label}\n${hit.text}`;
    if (size + block.length > maxChars) return;
    parts.push(block);
    size += block.length;
  });
  return parts.join("\n\n---\n\n");
}

/** Test seam: the caches outlive a request by design. */
export function resetRetrievalCaches(): void {
  bm25Cache = null;
}
