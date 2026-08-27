import { describe, expect, it } from "vitest";

import { chunkText, CHUNK_OVERLAP, CHUNK_SIZE } from "./chunk";

describe("chunkText", () => {
  it("returns a single chunk for text shorter than the window", () => {
    const text = "The Constitution of India was adopted on 26 November 1949.";
    const chunks = chunkText(text);
    expect(chunks).toHaveLength(1);
    expect(chunks[0].text).toBe(text);
  });

  it("does not fragment text sitting just under the window", () => {
    const text = "Article 32 is the heart and soul of the Constitution. ".repeat(15).trim();
    expect(text.length).toBeLessThan(CHUNK_SIZE);
    expect(chunkText(text)).toHaveLength(1);
  });

  it("splits long text without a tail of crumbs", () => {
    const text = "Directive Principles are non-justiciable guidelines. ".repeat(200).trim();
    const chunks = chunkText(text);
    expect(chunks.length).toBeLessThanOrEqual(
      Math.ceil(text.length / (CHUNK_SIZE - CHUNK_OVERLAP)) + 2,
    );
    // A run of overlap-sized fragments is the signature of the original bug.
    for (const chunk of chunks.slice(0, -1)) {
      expect(chunk.text.length).toBeGreaterThan(CHUNK_OVERLAP);
    }
  });

  it("always terminates on pathological input", () => {
    expect(chunkText(".".repeat(5000)).length).toBeLessThan(100);
    expect(chunkText(". ".repeat(3000)).length).toBeLessThan(100);
  });

  it("carries the page number onto every chunk", () => {
    const text = "Fundamental Rights are enshrined in Part III. ".repeat(80).trim();
    const chunks = chunkText(text, { page: 412 });
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks.every((chunk) => chunk.page === 412)).toBe(true);
  });

  it("yields nothing for empty or whitespace input", () => {
    expect(chunkText("")).toEqual([]);
    expect(chunkText("   \n\n  ")).toEqual([]);
  });

  it("continues numbering across calls so page chunks stay ordered", () => {
    const first = chunkText("Page one text.", { page: 1 });
    const second = chunkText("Page two text.", { page: 2, startIndex: first.length });
    expect(second[0].index).toBe(first.length);
  });
});
