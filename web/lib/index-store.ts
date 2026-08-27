/**
 * Loads the prebuilt index off disk, once per lambda.
 *
 * This is the whole reason the app no longer 429s at boot: the vectors were
 * computed offline and committed, so a cold start reads a file instead of
 * issuing thousands of embed requests.
 */
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import path from "node:path";

import type { Chunk, IndexMeta, OpenChunk, RestrictedChunk } from "./types";

const INDEX_DIR = path.join(process.cwd(), "public", "index");

export interface LoadedIndex {
  meta: IndexMeta;
  chunks: Chunk[];
  /** Row-major, `meta.dims` floats per chunk, L2-normalised at build time. */
  vectors: Float32Array;
}

/**
 * float16 → float32 via a 64K lookup table.
 *
 * Node 22 has no Float16Array, and decoding 12M values with Math.pow at cold
 * start is measurably slow. Building the table costs 256KB once.
 */
let f16Table: Float32Array | null = null;

function halfToFloatTable(): Float32Array {
  if (f16Table) return f16Table;
  const table = new Float32Array(65536);
  const view = new DataView(new ArrayBuffer(4));
  for (let h = 0; h < 65536; h++) {
    const sign = (h & 0x8000) << 16;
    const exponent = (h & 0x7c00) >> 10;
    const mantissa = h & 0x03ff;
    let bits: number;
    if (exponent === 0) {
      // Subnormal: renormalise into a float32 exponent.
      if (mantissa === 0) {
        bits = sign;
      } else {
        let e = -1;
        let m = mantissa;
        do {
          m <<= 1;
          e++;
        } while ((m & 0x0400) === 0);
        bits = sign | ((127 - 15 - e) << 23) | ((m & 0x03ff) << 13);
      }
    } else if (exponent === 0x1f) {
      bits = sign | 0x7f800000 | (mantissa << 13);
    } else {
      bits = sign | ((exponent - 15 + 127) << 23) | (mantissa << 13);
    }
    view.setUint32(0, bits >>> 0);
    table[h] = view.getFloat32(0);
  }
  f16Table = table;
  return table;
}

function decodeVectors(buffer: Buffer, expected: number): Float32Array {
  const halves = new Uint16Array(
    buffer.buffer,
    buffer.byteOffset,
    buffer.byteLength / 2,
  );
  const table = halfToFloatTable();
  const out = new Float32Array(halves.length);
  for (let i = 0; i < halves.length; i++) out[i] = table[halves[i]];
  if (out.length !== expected) {
    throw new Error(
      `index corrupt: ${out.length} floats, expected ${expected}. Rebuild with ingest/build_index.py`,
    );
  }
  return out;
}

async function readIndex(): Promise<LoadedIndex> {
  const [metaRaw, openRaw, restrictedRaw, vectorRaw] = await Promise.all([
    readFile(path.join(INDEX_DIR, "meta.json"), "utf8"),
    readFile(path.join(INDEX_DIR, "chunks.a.json.gz")),
    readFile(path.join(INDEX_DIR, "chunks.b.json.gz")),
    readFile(path.join(INDEX_DIR, "vectors.f16.bin")),
  ]);

  const meta = JSON.parse(metaRaw) as IndexMeta;
  const open = JSON.parse(gunzipSync(openRaw).toString("utf8")) as OpenChunk[];
  const restricted = JSON.parse(
    gunzipSync(restrictedRaw).toString("utf8"),
  ) as RestrictedChunk[];

  // `i` is the row this chunk occupies in the vector matrix.
  const chunks = new Array<Chunk>(meta.count);
  for (const chunk of [...open, ...restricted]) chunks[chunk.i] = chunk;

  const vectors = decodeVectors(vectorRaw, meta.count * meta.dims);
  return { meta, chunks, vectors };
}

/** Module-scope so warm invocations reuse the decoded matrix. */
let cached: Promise<LoadedIndex> | null = null;

export function loadIndex(): Promise<LoadedIndex> {
  if (!cached) {
    cached = readIndex().catch((error) => {
      cached = null; // a failed load must not poison every later request
      throw error;
    });
  }
  return cached;
}
