/**
 * Prelims drill generation.
 *
 * Returns structured MCQ objects, not markdown. The Streamlit build asked the
 * model for prose, which arrived with every answer already revealed — there was
 * nothing left to attempt.
 */
import { Type } from "@google/genai";

import { embedQuery, generateJson, GeminiError } from "@/lib/gemini";
import { fallbackQuestions } from "@/lib/question-bank";
import { formatContext, retrieve } from "@/lib/retrieve";
import type { Mcq } from "@/lib/types";

export const runtime = "nodejs";
export const maxDuration = 60;

const MCQ_SCHEMA = {
  type: Type.ARRAY,
  items: {
    type: Type.OBJECT,
    properties: {
      question: { type: Type.STRING },
      options: { type: Type.ARRAY, items: { type: Type.STRING } },
      answerIndex: { type: Type.INTEGER },
      explanation: { type: Type.STRING },
      sourceRef: { type: Type.STRING },
      subject: { type: Type.STRING },
    },
    required: [
      "question",
      "options",
      "answerIndex",
      "explanation",
      "sourceRef",
      "subject",
    ],
  },
};

const SYSTEM = `You write UPSC Prelims multiple-choice questions at genuine exam standard.

Rules:
- Exactly four options per question, in a single flat list.
- answerIndex is the zero-based index of the correct option.
- The explanation must say why the correct option is right AND why each distractor is wrong.
- Ground every factual claim in the supplied study material. If the material is thin, ask about well-established syllabus facts instead of inventing specifics.
- Never reference the study material by bracket number in the question text itself.`;

/** A model can return four-ish options or an out-of-range index; drop those. */
function isUsable(candidate: Mcq): boolean {
  return (
    typeof candidate.question === "string" &&
    candidate.question.trim().length > 10 &&
    Array.isArray(candidate.options) &&
    candidate.options.length === 4 &&
    candidate.options.every((o) => typeof o === "string" && o.trim()) &&
    Number.isInteger(candidate.answerIndex) &&
    candidate.answerIndex >= 0 &&
    candidate.answerIndex < 4 &&
    typeof candidate.explanation === "string" &&
    candidate.explanation.trim().length > 20
  );
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    topic?: string;
    count?: number;
    apiKey?: string;
  };
  const topic = (body.topic ?? "").trim() || "Indian Polity";
  const count = Math.min(Math.max(body.count ?? 5, 1), 10);

  try {
    let queryVector: Float32Array | undefined;
    try {
      queryVector = await embedQuery(topic, body.apiKey);
    } catch {
      // Lexical-only retrieval still grounds the questions.
    }
    const hits = await retrieve(topic, { topK: 6, queryVector });
    const context = formatContext(hits, 9000);

    const questions = await generateJson<Mcq[]>(
      `${
        context
          ? `## Study material\n\n${context}\n\n---\n\n`
          : "No study material was retrieved; use well-established syllabus facts.\n\n"
      }Write ${count} UPSC Prelims MCQs on: ${topic}`,
      { system: SYSTEM, schema: MCQ_SCHEMA, apiKey: body.apiKey },
    );

    const usable = (Array.isArray(questions) ? questions : []).filter(isUsable);
    if (!usable.length) throw new GeminiError("No usable questions.", false);

    return Response.json({
      questions: usable.slice(0, count),
      topic,
      generated: true,
      grounded: Boolean(context),
    });
  } catch (error) {
    // A drill must always start. Written questions beat an error page.
    console.error(`[drill] falling back to the bank: ${String(error).slice(0, 200)}`);
    const rateLimited = error instanceof GeminiError && error.rateLimited;
    return Response.json({
      questions: fallbackQuestions(topic, count),
      topic,
      generated: false,
      grounded: false,
      notice: rateLimited
        ? "Gemini is rate-limited right now — these are Saarthi's own vetted questions."
        : "Generated questions were unavailable — these are Saarthi's own vetted questions.",
    });
  }
}
