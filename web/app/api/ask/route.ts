/**
 * Streamed, source-grounded answers.
 *
 * Emits newline-delimited JSON so the client can render citations before the
 * first token arrives: one `sources` frame, then `text` frames, then `done`.
 */
import { embedQuery, GeminiError, generateStream } from "@/lib/gemini";
import { loadIndex } from "@/lib/index-store";
import { buildPrompt, formatHistory, SYSTEM_INSTRUCTION } from "@/lib/prompt";
import { formatContext, retrieve } from "@/lib/retrieve";
import { routeQuestion } from "@/lib/router";
import type { Retrieved, StudyMode } from "@/lib/types";

export const runtime = "nodejs";
export const maxDuration = 60;

interface AskBody {
  question?: string;
  mode?: StudyMode;
  history?: Array<{ role: string; content: string }>;
  apiKey?: string;
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

        const hits = await retrieve(question, {
          topK: route === "direct" ? 3 : 6,
          queryVector,
        });

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
