import { describe, expect, it } from "vitest";

import { limitSharedKeyRequest, requestIp, TokenBucket } from "./rate-limit";

describe("TokenBucket", () => {
  it("allows the configured burst and then rejects", () => {
    const bucket = new TokenBucket();

    expect(bucket.take("ask:1", 2, 10_000, 0).allowed).toBe(true);
    expect(bucket.take("ask:1", 2, 10_000, 0).allowed).toBe(true);
    expect(bucket.take("ask:1", 2, 10_000, 0)).toMatchObject({
      allowed: false,
      remaining: 0,
      retryAfterSeconds: 5,
    });
  });

  it("refills continuously over the policy window", () => {
    const bucket = new TokenBucket();
    bucket.take("drill:1", 2, 10_000, 0);
    bucket.take("drill:1", 2, 10_000, 0);

    expect(bucket.take("drill:1", 2, 10_000, 4_999).allowed).toBe(false);
    expect(bucket.take("drill:1", 2, 10_000, 5_000).allowed).toBe(true);
  });

  it("keeps endpoint and IP buckets independent", () => {
    const bucket = new TokenBucket();
    bucket.take("ask:1", 1, 10_000, 0);

    expect(bucket.take("ask:1", 1, 10_000, 0).allowed).toBe(false);
    expect(bucket.take("ask:2", 1, 10_000, 0).allowed).toBe(true);
    expect(bucket.take("drill:1", 1, 10_000, 0).allowed).toBe(true);
  });
});

describe("requestIp", () => {
  it("uses the first Vercel forwarding hop", () => {
    const request = new Request("https://example.test", {
      headers: { "x-forwarded-for": "203.0.113.7, 10.0.0.1" },
    });
    expect(requestIp(request)).toBe("203.0.113.7");
  });

  it("has a stable fallback when no proxy header is present", () => {
    expect(requestIp(new Request("https://example.test"))).toBe("unknown");
  });
});

describe("limitSharedKeyRequest", () => {
  it("always exempts a visitor-supplied Gemini key", () => {
    const request = new Request("https://example.test", {
      headers: { "x-forwarded-for": "203.0.113.9" },
    });

    expect(limitSharedKeyRequest(request, "ask", 0, 0, " visitor-key ")).toBeNull();
  });
});
