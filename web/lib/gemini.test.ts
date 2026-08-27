import { beforeEach, describe, expect, it, vi } from "vitest";

const sdk = vi.hoisted(() => ({
  constructed: vi.fn(),
  embedContent: vi.fn(),
  generateContent: vi.fn(),
  generateContentStream: vi.fn(),
}));

vi.mock("@google/genai", () => ({
  GoogleGenAI: class {
    models = {
      embedContent: sdk.embedContent,
      generateContent: sdk.generateContent,
      generateContentStream: sdk.generateContentStream,
    };

    constructor(options: unknown) {
      sdk.constructed(options);
    }
  },
  ThinkingLevel: { LOW: "LOW" },
}));

import {
  FALLBACK_MODEL,
  generateJson,
  generateStream,
  isOverloaded,
  LAST_RESORT_MODEL,
  MODEL,
  modelChain,
  PartialAnswer,
  resetModelMemory,
} from "./gemini";

async function* chunks(...values: Array<string | Error>) {
  for (const value of values) {
    if (value instanceof Error) throw value;
    yield { text: value };
  }
}

async function collect(stream: AsyncGenerator<string>): Promise<string> {
  let output = "";
  for await (const value of stream) output += value;
  return output;
}

beforeEach(() => {
  vi.clearAllMocks();
  // generateStream and generateJson remember which model last answered, so a
  // warm lambda can skip a model that is down. That memory outlives a request
  // by design and would otherwise carry between tests and reorder the chain.
  resetModelMemory();
  vi.spyOn(console, "warn").mockImplementation(() => undefined);
  vi.spyOn(console, "error").mockImplementation(() => undefined);
});

describe("isOverloaded", () => {
  it.each([
    "500 INTERNAL",
    "502 bad gateway",
    "503 UNAVAILABLE",
    "504 gateway timeout",
    "DEADLINE_EXCEEDED",
    "TypeError: terminated",
    "fetch failed",
    "read ECONNRESET",
    "socket hang up",
  ])("recognises a failover-worthy error: %s", (message) => {
    expect(isOverloaded(new Error(message))).toBe(true);
  });

  it("does not classify quota exhaustion as overload", () => {
    expect(isOverloaded(new Error("429 RESOURCE_EXHAUSTED"))).toBe(false);
  });
});

describe("modelChain", () => {
  it("trims blanks and removes duplicates without changing order", () => {
    expect(modelChain(" primary ", "primary", " fallback ")).toEqual([
      "primary",
      "fallback",
    ]);
  });

  it("rejects an entirely blank chain", () => {
    expect(() => modelChain("", " ", "")).toThrow("No Gemini model configured");
  });
});

describe("generateStream", () => {
  it("hides a pre-commit failure and cleanly fails over", async () => {
    sdk.generateContentStream.mockImplementation(
      ({ model }: { model: string }) =>
        model === MODEL
          ? chunks("too short", new Error("503 UNAVAILABLE"))
          : chunks("complete fallback answer"),
    );
    const restarted = vi.fn();

    const output = await collect(
      generateStream("prompt", {
        system: "system",
        apiKey: "test-key",
        onRestart: restarted,
      }),
    );

    expect(output).toBe("complete fallback answer");
    expect(restarted).not.toHaveBeenCalled();
    expect(sdk.generateContentStream).toHaveBeenCalledTimes(2);
    expect(sdk.generateContentStream.mock.calls[1][0].model).toBe(FALLBACK_MODEL);
  });

  it("signals a reset when a committed answer restarts on the fallback", async () => {
    sdk.generateContentStream.mockImplementation(
      ({ model }: { model: string }) =>
        model === MODEL
          ? chunks("x".repeat(300), new Error("socket hang up"))
          : chunks("replacement answer"),
    );
    const restarted = vi.fn();

    const output = await collect(
      generateStream("prompt", {
        system: "system",
        apiKey: "test-key",
        onRestart: restarted,
      }),
    );

    expect(output).toBe(`${"x".repeat(300)}replacement answer`);
    expect(restarted).toHaveBeenCalledTimes(1);
  });

  it("preserves the final rung as a PartialAnswer after commit", async () => {
    sdk.generateContentStream.mockImplementation(({ model }: { model: string }) =>
      chunks(model.repeat(30).slice(0, 300).padEnd(300, "x"), new Error("terminated")),
    );

    await expect(
      collect(
        generateStream("prompt", {
          system: "system",
          apiKey: "test-key",
        }),
      ),
    ).rejects.toBeInstanceOf(PartialAnswer);

    expect(sdk.generateContentStream).toHaveBeenCalledTimes(3);
    expect(sdk.generateContentStream.mock.calls[2][0].model).toBe(
      LAST_RESORT_MODEL,
    );
  });
});

describe("generateJson", () => {
  it("honours the wall deadline and skips attempts below the minimum budget", async () => {
    let now = 0;
    vi.spyOn(Date, "now").mockImplementation(() => now);
    sdk.generateContent.mockImplementation(async () => {
      now = 45_001;
      throw new Error("503 UNAVAILABLE");
    });

    await expect(
      generateJson("prompt", {
        system: "system",
        schema: {},
        apiKey: "test-key",
      }),
    ).rejects.toThrow("503 UNAVAILABLE");

    expect(sdk.generateContent).toHaveBeenCalledTimes(1);
    expect(sdk.constructed).toHaveBeenCalledWith({
      apiKey: "test-key",
      httpOptions: { timeout: 50_000 },
    });
  });
});
