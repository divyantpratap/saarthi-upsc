/**
 * Text splitter, kept in parity with src/ingest/chunker.py.
 *
 * Uploaded documents are chunked in the browser with the same sizes and
 * boundary rules the offline pipeline uses, so a passage from your own PDF
 * behaves like a passage from the bundled index.
 *
 * The Python original had a termination bug: once a text was consumed it
 * stepped back by the overlap and kept going, emitting ~CHUNK_OVERLAP
 * near-duplicate crumbs one character apart. The `end >= text.length` guard
 * below is that fix, and it matters more here — a PDF page is usually shorter
 * than CHUNK_SIZE, which is exactly the case that triggered it.
 */

export const CHUNK_SIZE = 1000;
export const CHUNK_OVERLAP = 120;

export interface TextChunk {
  text: string;
  page?: number;
  index: number;
}

export function chunkText(
  raw: string,
  { page, startIndex = 0 }: { page?: number; startIndex?: number } = {},
): TextChunk[] {
  // Normalise inside paragraphs but keep paragraph breaks: they carry the
  // citation boundaries shown to students.
  const text = raw
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.split(/\s+/).join(" ").trim())
    .filter(Boolean)
    .join("\n\n");

  if (!text) return [];

  const chunks: TextChunk[] = [];
  let start = 0;
  let index = startIndex;

  while (start < text.length) {
    const targetEnd = Math.min(start + CHUNK_SIZE, text.length);
    let end = targetEnd;

    if (targetEnd < text.length) {
      // Look for a boundary only in the back half of the window, so a full stop
      // near the start can never shrink a chunk to a crumb.
      const floor = start + Math.floor(CHUNK_SIZE / 2);
      const paragraphEnd = text.lastIndexOf("\n\n", targetEnd);
      const sentenceEnd = Math.max(
        text.lastIndexOf(". ", targetEnd),
        text.lastIndexOf("? ", targetEnd),
      );
      if (paragraphEnd >= floor) end = paragraphEnd;
      else if (sentenceEnd >= floor) end = sentenceEnd + 1;
    }

    const piece = text.slice(start, end).trim();
    if (piece) chunks.push({ text: piece, page, index: index++ });

    // Text consumed. Stepping back by the overlap here would re-emit its tail
    // forever, one character at a time.
    if (end >= text.length) break;
    start = Math.max(end - CHUNK_OVERLAP, start + 1);
  }

  return chunks;
}
