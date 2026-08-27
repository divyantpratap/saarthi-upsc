/**
 * Gemini access with retries that actually retry.
 *
 * The Streamlit version called its generator with `retries=1`, which in Python
 * means `range(1)` — a single attempt. It slept on a 429 and then gave up, so
 * one transient rate-limit surfaced to students as "the answer model is
 * temporarily busy". Here every call gets real attempts, the wait comes from the
 * `retryDelay` the API itself returns, and the fallback model is required to
 * differ from the primary or it is not a fallback at all.
 */
import { GoogleGenAI, ThinkingLevel } from "@google/genai";

/**
 * Read an env var, treating blank as unset.
 *
 * `??` only falls back on undefined, so a variable present-but-empty — the
 * normal result of clearing a row in a hosting dashboard — passed straight
 * through. An empty GEMINI_MODEL reached the SDK as the model name and every
 * answer failed with "model is required and must be a string"; an empty
 * GEMINI_EMBED_DIMS would have become Number("") = 0 and broken retrieval more
 * quietly still.
 */
export function envOr(name: string, fallback: string): string {
  const value = process.env[name]?.trim();
  return value ? value : fallback;
}

export const MODEL = envOr("GEMINI_MODEL", "gemini-3.7-flash");
export const FALLBACK_MODEL = envOr("GEMINI_MODEL_FALLBACK", "gemini-3.6-flash");
/** Last rung, tried only when both newer models are unavailable. */
export const LAST_RESORT_MODEL = envOr("GEMINI_MODEL_LAST_RESORT", "gemini-2.5-flash");
export const EMBED_MODEL = envOr("GEMINI_EMBED_MODEL", "gemini-embedding-001");
export const EMBED_DIMS = Number(envOr("GEMINI_EMBED_DIMS", "768"));

const MAX_ATTEMPTS = 4;
const MAX_BACKOFF_MS = 30_000;
/**
 * Cap each call so an overloaded model fails over quickly. Without this the SDK
 * retries a 503 internally for ~90s before surfacing it, which reads to a
 * student as the app having hung. Two models at 25s each still fits inside the
 * 60s Vercel function budget.
 */
const REQUEST_TIMEOUT_MS = Number(envOr("GEMINI_TIMEOUT_MS", "25000"));

/**
 * Hold back the opening of an answer until this many characters have arrived.
 *
 * gemini-3.7-flash drops connections under launch demand, usually within the
 * first hundred characters. Yielding immediately meant a dropped stream left
 * the reader with a 77-character stub that could not be retried, because
 * restarting would rewrite text they had already seen. Buffering to a commit
 * point keeps early failures invisible and recoverable; the delay is a fraction
 * of a second of generation.
 */
const COMMIT_THRESHOLD = 300;

/**
 * Structured generation gets a tighter budget than streaming, because it must
 * fit a whole three-model chain inside Vercel's 60s function limit. Three
 * attempts at 18s leaves headroom; at the streaming timeout it would be killed
 * mid-chain and the reader would get the fallback bank instead of a real drill.
 */
const JSON_TIMEOUT_MS = 18_000;
const EMBED_TIMEOUT_MS = 15_000;

/**
 * Answering a UPSC question from retrieved passages is synthesis, not deep
 * reasoning — extended thinking mostly buys latency here. Only Gemini 3 models
 * accept the setting, so older ones configured via env are left alone.
 */
function thinkingFor(model: string) {
  return model.startsWith("gemini-3")
    ? { thinkingConfig: { thinkingLevel: ThinkingLevel.LOW } }
    : {};
}

/** Raised when a stream died after the reader already had part of the answer. */
export class PartialAnswer extends Error {
  constructor(readonly detail: string) {
    super(detail);
    this.name = "PartialAnswer";
  }
}

export class GeminiError extends Error {
  constructor(
    message: string,
    readonly rateLimited: boolean,
  ) {
    super(message);
    this.name = "GeminiError";
  }
}

/**
 * A visitor's own key, when supplied, is used for that request and never
 * retained — the same contract the Streamlit BYOK box made.
 */
export function client(apiKey?: string, timeoutMs = REQUEST_TIMEOUT_MS): GoogleGenAI {
  const key = (apiKey || process.env.GEMINI_API_KEY || "").trim();
  if (!key) throw new GeminiError("No Gemini API key configured.", false);
  return new GoogleGenAI({ apiKey: key, httpOptions: { timeout: timeoutMs } });
}

function isRateLimit(error: unknown): boolean {
  const message = String(error);
  return message.includes("429") || message.includes("RESOURCE_EXHAUSTED");
}

/**
 * The model is up but swamped, or the call timed out waiting on it. Newly
 * released models do this under launch demand. Waiting is pointless when a
 * sibling model is healthy — move on rather than retry the same one.
 */
function isOverloaded(error: unknown): boolean {
  const message = String(error);
  return (
    /\b(500|502|503|504)\b/.test(message) ||
    message.includes("UNAVAILABLE") ||
    // Google's own deadline, distinct from our client-side timeout below.
    message.includes("DEADLINE_EXCEEDED") ||
    message.includes("INTERNAL") ||
    message.includes("overloaded") ||
    message.includes("aborted") ||
    message.includes("timeout") ||
    // undici surfaces a dropped socket as a bare "terminated" TypeError, with
    // no status code to match on. Left unclassified it read as fatal, so a
    // dropped connection skipped failover entirely.
    message.includes("terminated") ||
    message.includes("fetch failed") ||
    message.includes("ECONNRESET") ||
    message.includes("socket hang up")
  );
}

/** Google tells us when the window reopens; prefer that over guessing. */
function retryDelayMs(error: unknown, attempt: number): number {
  const match = /retryDelay['"]?:\s*['"]?(\d+(?:\.\d+)?)s/.exec(String(error));
  if (match) return Math.min(Number(match[1]) * 1000 + 500, MAX_BACKOFF_MS);
  return Math.min(2 ** attempt * 1000, MAX_BACKOFF_MS);
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function withRetry<T>(
  operation: (model: string) => Promise<T>,
  models: string[],
): Promise<T> {
  let last: unknown;
  for (const model of models) {
    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      try {
        return await operation(model);
      } catch (error) {
        last = error;
        const summary = String(error).slice(0, 160).replace(/\s+/g, " ");
        // Wrong model, or a healthy-but-swamped one: neither improves by
        // retrying here, so hand off to the next model in the chain.
        if (/404|NOT_FOUND/.test(String(error))) {
          console.warn(`[gemini] ${model}: not found — trying next. ${summary}`);
          break;
        }
        if (isOverloaded(error)) {
          console.warn(`[gemini] ${model}: overloaded — trying next. ${summary}`);
          break;
        }
        if (!isRateLimit(error)) {
          console.error(`[gemini] ${model}: fatal. ${summary}`);
          throw error;
        }
        console.warn(`[gemini] ${model}: rate limited (attempt ${attempt + 1}).`);
        if (attempt < MAX_ATTEMPTS - 1) await sleep(retryDelayMs(error, attempt));
      }
    }
  }
  throw new GeminiError(String(last), isRateLimit(last));
}

/** Primary first, then the fallback — but only if it is genuinely different. */
function modelChain(primary = MODEL): string[] {
  const usable = [primary, FALLBACK_MODEL, LAST_RESORT_MODEL]
    .map((model) => model.trim())
    .filter((model, i, all) => model.length > 0 && all.indexOf(model) === i);
  if (!usable.length) throw new GeminiError("No Gemini model configured.", false);
  return usable;
}

export async function embedQuery(
  text: string,
  apiKey?: string,
): Promise<Float32Array> {
  const ai = client(apiKey, EMBED_TIMEOUT_MS);
  const response = await withRetry(
    (model) =>
      ai.models.embedContent({
        model,
        contents: text,
        config: { taskType: "RETRIEVAL_QUERY", outputDimensionality: EMBED_DIMS },
      }),
    [EMBED_MODEL],
  );

  const values = response.embeddings?.[0]?.values;
  if (!values?.length) throw new GeminiError("Empty embedding response.", false);

  // Below 3072 dims the model returns unnormalised vectors, and the index was
  // normalised at build time — skip this and every cosine score is wrong.
  const vector = Float32Array.from(values);
  let norm = 0;
  for (const v of vector) norm += v * v;
  norm = Math.sqrt(norm);
  if (norm > 0) for (let i = 0; i < vector.length; i++) vector[i] /= norm;
  return vector;
}

export async function* generateStream(
  prompt: string,
  { system, apiKey, temperature = 0.25, onModel, onRestart }: {
    system: string;
    apiKey?: string;
    temperature?: number;
    /** Which model actually served the answer, once the chain settles. */
    onModel?: (model: string) => void;
    /**
     * A partly-streamed answer is being abandoned for the next model. The
     * caller should discard what it has emitted so far.
     */
    onRestart?: () => void;
  },
): AsyncGenerator<string> {
  const ai = client(apiKey);
  const models = modelChain();
  let last: unknown;

  for (const model of models) {
    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      // Tracked per attempt: once tokens have reached the reader, switching
      // models would restart the answer mid-sentence.
      let produced = false;
      try {
        const stream = await ai.models.generateContentStream({
          model,
          contents: prompt,
          config: {
            systemInstruction: system,
            temperature,
            maxOutputTokens: 4096,
            ...thinkingFor(model),
          },
        });
        onModel?.(model);
        let buffered = "";
        for await (const chunk of stream) {
          if (!chunk.text) continue;
          if (produced) {
            yield chunk.text;
            continue;
          }
          buffered += chunk.text;
          if (buffered.length >= COMMIT_THRESHOLD) {
            produced = true;
            yield buffered;
            buffered = "";
          }
        }
        // A complete answer shorter than the commit point still counts.
        if (buffered) yield buffered;
        return;
      } catch (error) {
        last = error;
        const summary = String(error).slice(0, 160).replace(/\s+/g, " ");

        // Past the commit point the reader can already see text. Where a
        // healthier model remains, retract it and start over — a brief flicker
        // beats a truncated answer. On the last rung, keep what they have.
        if (produced) {
          const isLastModel = model === models[models.length - 1];
          console.warn(`[gemini] ${model}: failed mid-stream. ${summary}`);
          if (isLastModel) throw new PartialAnswer(summary);
          onRestart?.();
          break;
        }

        if (/404|NOT_FOUND/.test(String(error))) {
          console.warn(`[gemini] ${model}: not found — trying next. ${summary}`);
          break;
        }
        if (isOverloaded(error)) {
          console.warn(`[gemini] ${model}: overloaded — trying next. ${summary}`);
          break;
        }
        if (!isRateLimit(error)) {
          console.error(`[gemini] ${model}: fatal. ${summary}`);
          throw error;
        }
        console.warn(`[gemini] ${model}: rate limited (attempt ${attempt + 1}).`);
        if (attempt < MAX_ATTEMPTS - 1) await sleep(retryDelayMs(error, attempt));
      }
    }
  }
  throw new GeminiError(String(last), isRateLimit(last));
}

export async function generateJson<T>(
  prompt: string,
  { system, schema, apiKey }: { system: string; schema: object; apiKey?: string },
): Promise<T> {
  const ai = client(apiKey, JSON_TIMEOUT_MS);
  const response = await withRetry(
    (model) =>
      ai.models.generateContent({
        model,
        contents: prompt,
        config: {
          systemInstruction: system,
          temperature: 0.4,
          responseMimeType: "application/json",
          responseSchema: schema,
          maxOutputTokens: 4096,
          ...thinkingFor(model),
        },
      }),
    modelChain(),
  );

  const text = response.text;
  if (!text) throw new GeminiError("Empty structured response.", false);
  return JSON.parse(text) as T;
}
