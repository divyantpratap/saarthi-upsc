import { describe, expect, it } from "vitest";

import { hasSemanticIndex } from "./index-store";
import type { IndexMeta } from "./types";

function meta(overrides: Partial<IndexMeta> = {}): IndexMeta {
  return {
    version: 1,
    fingerprint: "test",
    embedModel: "gemini-embedding-001",
    dims: 768,
    count: 10,
    openCount: 10,
    restrictedCount: 0,
    builtAt: "2026-08-27T00:00:00Z",
    sources: {},
    ...overrides,
  };
}

describe("hasSemanticIndex", () => {
  it("recognises a lexical-only artifact", () => {
    expect(hasSemanticIndex(meta({ vectorCount: 0 }))).toBe(false);
  });

  it("recognises a complete hybrid artifact", () => {
    expect(hasSemanticIndex(meta({ vectorCount: 10 }))).toBe(true);
  });

  it("keeps legacy full-vector metadata compatible", () => {
    expect(hasSemanticIndex(meta())).toBe(true);
  });
});
