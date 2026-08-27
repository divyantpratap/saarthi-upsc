/**
 * Streamed, source-grounded answers.
 *
 * Emits newline-delimited JSON so the client can render citations before the
 * first token arrives: one `sources` frame, then `text` frames, then `done`.
 */
import {
  embedQuery,
  GeminiError,
  generateStream,
  PartialAnswer,
} from "@/lib/gemini";
import { loadIndex } from "@/lib/index-store";
import { buildPrompt, formatHistory, SYSTEM_INSTRUCTION } from "@/lib/prompt";
import { formatContext, retrieve } from "@/lib/retrieve";
import { routeQuestion } from "@/lib/router";
import type { OpenChunk, Retrieved, StudyMode } from "@/lib/types";

export const runtime = "nodejs";
export const maxDuration = 60;

interface AskBody {
  question?: string;
  mode?: StudyMode;
  history?: Array<{ role: string; content: string }>;
  apiKey?: string;
  /** Passages the browser matched in the reader's own uploaded documents. */
  localMatches?: Array<{ docName: string; page?: number; text: string }>;
}

const MAX_LOCAL_CHARS = 4000;

/**
 * Uploads live in the reader's browser, so their matching passages arrive with
 * the request rather than being retrieved here. They are trimmed on the way in:
 * this is untrusted text heading into a prompt, and an oversized payload would
 * otherwise crowd out the grounded sources.
 */
function asRetrieved(
  matches: NonNullable<AskBody["localMatches"]>,
): Retrieved[] {
  let budget = MAX_LOCAL_CHARS;
  const out: Retrieved[] = [];
  for (const match of matches.slice(0, 3)) {
    const text = String(match.text ?? "").slice(0, Math.max(0, budget));
    if (!text.trim()) break;
    budget -= text.length;
    const chunk: OpenChunk = {
      i: -1,
      src: `upload:${match.docName}`,
      file: String(match.docName ?? "Your upload").slice(0, 200),
      subj: "Your upload",
      page: match.page ?? null,
      text,
    };
    out.push({ chunk, score: 0, text, citationOnly: false });
  }
  return out;
}

function citation(hit: Retrieved) {
  return {
    file: hit.chunk.file,
    subject: hit.chunk.subj,
    page: hit.chunk.page ?? null,
    paragraph: hit.chunk.para ?? null,
    relevance: Math.round(Math.max(0, Math.min(1, hit.score)) * 100),
    preview: hit.text ? hit.text.slice(0, 280) : null,
    citationOnly: hit.citationOnly,
  };
}

export async function POST(request: Request) {
  const body = (await request.json()) as AskBody;
  const question = (body.question ?? "").trim();
  const mode: StudyMode = body.mode ?? "Learn";

  if (!question) {
    return Response.json({ error: "Ask a question first." }, { status: 400 });
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (frame: unknown) =>
        controller.enqueue(encoder.encode(`${JSON.stringify(frame)}\n`));

      try {
        const { meta } = await loadIndex();
        const route = routeQuestion(question, meta.count > 0);

        // A failed query embedding degrades to lexical-only retrieval rather
        // than failing the request — BM25 alone still finds real passages.
        let queryVector: Float32Array | undefined;
        try {
          queryVector = await embedQuery(question, body.apiKey);
        } catch (error) {
          if (!(error instanceof GeminiError)) throw error;
          send({ type: "notice", value: "keyword-only retrieval" });
        }

        const retrieved = await retrieve(question, {
          topK: route === "direct" ? 3 : 6,
          queryVector,
        });
        // The reader's own material leads: they added it deliberately.
        const hits = [...asRetrieved(body.localMatches ?? []), ...retrieved];

        send({ type: "sources", value: hits.map(citation), route });

        const prompt = buildPrompt(
          question,
          formatContext(hits),
          hits,
          mode,
          formatHistory(body.history ?? []),
        );

        let produced = false;
        for await (const token of generateStream(prompt, {
          system: SYSTEM_INSTRUCTION,
          apiKey: body.apiKey,
          onModel: (model) => send({ type: "model", value: model }),
        })) {
          produced = true;
          send({ type: "text", value: token });
        }
        if (!produced) throw new GeminiError("Model returned nothing.", false);

        send({ type: "done" });
      } catch (error) {
        // The reader already has most of the answer; truncating it is a far
        // better outcome than replacing it with a red box.
        if (error instanceof PartialAnswer) {
          send({
            type: "notice",
            value: "The model dropped the connection — this answer is cut short.",
          });
          send({ type: "done" });
          return;
        }
        const rateLimited =
          error instanceof GeminiError ? error.rateLimited : false;
        send({
          type: "error",
          rateLimited,
          value: rateLimited
            ? "Gemini is rate-limiting this key. Wait a moment, or add your own key in the sidebar."
            : `Could not complete the answer: ${String(error)}`,
        });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "content-type": "application/x-ndjson; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
