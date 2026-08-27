import { afterEach, describe, expect, it } from "vitest";

import { envOr } from "./gemini";

const NAME = "SAARTHI_TEST_VAR";

afterEach(() => {
  delete process.env[NAME];
});

describe("envOr", () => {
  it("uses the configured value", () => {
    process.env[NAME] = "gemini-3.6-flash";
    expect(envOr(NAME, "fallback")).toBe("gemini-3.6-flash");
  });

  it("falls back when the variable is absent", () => {
    expect(envOr(NAME, "fallback")).toBe("fallback");
  });

  it("falls back when the variable is present but blank", () => {
    // Clearing a row in a hosting dashboard leaves the key set to "". This is
    // the case that shipped an empty model name to the API in production.
    process.env[NAME] = "";
    expect(envOr(NAME, "fallback")).toBe("fallback");
  });

  it("falls back when the variable is only whitespace", () => {
    process.env[NAME] = "   ";
    expect(envOr(NAME, "fallback")).toBe("fallback");
  });

  it("trims surrounding whitespace from a real value", () => {
    process.env[NAME] = "  gemini-3.7-flash  ";
    expect(envOr(NAME, "fallback")).toBe("gemini-3.7-flash");
  });
});
