interface Bucket {
  tokens: number;
  updatedAt: number;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
}

/**
 * A small in-memory token bucket for one Vercel function instance.
 *
 * It deliberately has no external datastore dependency. The limit is therefore
 * a useful abuse brake, not a globally exact billing boundary: cold starts and
 * independently scaled instances each begin with a fresh bucket.
 */
export class TokenBucket {
  private readonly buckets = new Map<string, Bucket>();
  private operations = 0;

  take(
    key: string,
    capacity: number,
    windowMs: number,
    now = Date.now(),
  ): RateLimitResult {
    if (capacity <= 0 || windowMs <= 0) {
      throw new Error("Rate-limit capacity and window must be positive.");
    }

    const refillPerMs = capacity / windowMs;
    const previous = this.buckets.get(key);
    const elapsed = previous ? Math.max(0, now - previous.updatedAt) : 0;
    const available = previous
      ? Math.min(capacity, previous.tokens + elapsed * refillPerMs)
      : capacity;

    const allowed = available >= 1;
    const tokens = allowed ? available - 1 : available;
    this.buckets.set(key, { tokens, updatedAt: now });

    // Keep a long-lived warm function from accumulating abandoned IPs forever.
    this.operations += 1;
    if (this.operations % 256 === 0) {
      for (const [bucketKey, bucket] of this.buckets) {
        if (now - bucket.updatedAt > windowMs * 2) this.buckets.delete(bucketKey);
      }
    }

    return {
      allowed,
      remaining: Math.floor(tokens),
      retryAfterSeconds: allowed
        ? 0
        : Math.max(1, Math.ceil((1 - tokens) / refillPerMs / 1000)),
    };
  }
}

const publicBuckets = new TokenBucket();

export function requestIp(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  return forwarded || request.headers.get("x-real-ip")?.trim() || "unknown";
}

/** BYOK traffic does not consume Saarthi's shared Gemini quota. */
export function limitSharedKeyRequest(
  request: Request,
  scope: string,
  capacity: number,
  windowMs: number,
  apiKey?: string,
): Response | null {
  if (apiKey?.trim()) return null;

  const result = publicBuckets.take(
    `${scope}:${requestIp(request)}`,
    capacity,
    windowMs,
  );
  if (result.allowed) return null;

  return new Response(
    "Too many requests from this connection. Wait a moment, or use your own Gemini key.",
    {
      status: 429,
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "retry-after": String(result.retryAfterSeconds),
        "cache-control": "no-store",
      },
    },
  );
}
