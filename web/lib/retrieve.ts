/**
 * Hybrid retrieval over the bundled index: BM25 for lexical recall, cosine for
 * semantic recall, merged with Reciprocal Rank Fusion.
 *
 * RRF rather than a weighted score sum, because BM25 scores and cosine
 * similarities live on different scales and any fixed weighting between them
 * drifts as the corpus changes. RRF only needs the ranks.
 */
import { loadIndex } from "./index-store";
import { bm25Search, buildBm25, tokenize, type Bm25Index } from "./tokenize";
import { hasText, type Chunk, type Retrieved } from "./types";

const RRF_K = 60;
/** Candidates each retriever contributes before fusion. */
const CANDIDATES = 40;

function chunkTerms(chunk: Chunk): string[] {
  // Tier B ships a keyword signature instead of prose, so it stays searchable
  // without its pages being republished.
  return hasText(chunk) ? tokenize(chunk.text) : chunk.terms;
}

let bm25Cache: Bm25Index | null = null;

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

  if (!bm25Cache) bm25Cache = buildBm25(chunks.map(chunkTerms));

  const rankings: number[][] = [
    bm25Search(bm25Cache, query, CANDIDATES).map(([docId]) => docId),
  ];
  const similarity = new Map<number, number>();

  if (queryVector && vectors) {
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
