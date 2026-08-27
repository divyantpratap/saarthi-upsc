/**
 * Shared tokenizer and BM25 scoring.
 *
 * Used by the server over the bundled index and by the browser over a
 * visitor's own uploads, so a passage ranks the same wherever it came from.
 * Kept free of node built-ins for that reason.
 */

const STOPWORDS = new Set(
  `a an and are as at be by for from has have in is it its of on or that the to
   was were will with which this these those they their there than then such can
   could should would may might must not but also into over under about`.split(
    /\s+/,
  ),
);
const TOKEN = /[a-z][a-z0-9]{2,}/g;

export const K1 = 1.2;
export const B = 0.75;

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(TOKEN) ?? []).filter((t) => !STOPWORDS.has(t));
}

export interface Bm25Index {
  postings: Map<string, Array<[docId: number, tf: number]>>;
  docLength: Float32Array;
  averageLength: number;
  total: number;
}

export function buildBm25(documentTerms: string[][]): Bm25Index {
  const postings = new Map<string, Array<[number, number]>>();
  const docLength = new Float32Array(documentTerms.length);
  let lengthSum = 0;

  documentTerms.forEach((terms, docId) => {
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
    averageLength: documentTerms.length ? lengthSum / documentTerms.length : 1,
    total: documentTerms.length,
  };
}

/** Ranked document ids, best first. */
export function bm25Search(
  index: Bm25Index,
  query: string,
  limit: number,
): Array<[docId: number, score: number]> {
  const scores = new Map<number, number>();

  for (const term of new Set(tokenize(query))) {
    const list = index.postings.get(term);
    if (!list) continue;
    const idf = Math.log(
      1 + (index.total - list.length + 0.5) / (list.length + 0.5),
    );
    for (const [docId, tf] of list) {
      const norm =
        tf + K1 * (1 - B + (B * index.docLength[docId]) / index.averageLength);
      scores.set(docId, (scores.get(docId) ?? 0) + (idf * tf * (K1 + 1)) / norm);
    }
  }

  return [...scores.entries()].sort((a, b) => b[1] - a[1]).slice(0, limit);
}
