/** Prompt construction, carried over from src/rag/generator.py. */
import type { Retrieved, StudyMode } from "./types";

export const SYSTEM_INSTRUCTION = `You are Saarthi, a specialised tutor for the Indian Civil Services Examination (UPSC CSE).

Rules:
- Use ONLY the provided study material for factual claims.
- If the material is insufficient, say so plainly; add brief syllabus context only when you are certain.
- Structure answers with headings and bullets, and add **Prelims** / **Mains** pointers where useful.
- Cite sources with the bracketed numbers shown in the study material, e.g. [1].
- Be accurate, concise, and write in Indian English. Never invent statistics or quotations.`;

export const MODE_GUIDANCE: Record<StudyMode, string> = {
  Learn:
    "Explain clearly for a UPSC aspirant. Connect the concept to the syllabus and cite every factual claim.",
  Prelims:
    "Answer for UPSC Prelims. Prioritise precise facts, traps, elimination logic, and a short recall cue.",
  Mains:
    "Answer for UPSC Mains. Use a crisp introduction, a dimensional body, examples, and a constructive conclusion.",
  Evaluate:
    "Act as a strict UPSC evaluator. Award marks, identify missing dimensions, and provide an improved answer.",
};

/**
 * Chunks from commercial titles reach the model as a pointer, never as text.
 * The student still learns the topic is covered on a specific page of a book
 * they may own.
 */
function citationOnlyNote(hits: Retrieved[]): string {
  const pointers = hits
    .filter((hit) => hit.citationOnly)
    .slice(0, 4)
    .map(
      (hit) =>
        `- ${hit.chunk.file}${hit.chunk.page ? `, p.${hit.chunk.page}` : ""}`,
    );
  if (!pointers.length) return "";
  return `\n\n## Also covered in the student's own library (text not available to you)\n\n${pointers.join(
    "\n",
  )}\n\nYou may mention these as further reading. Do not attempt to quote or summarise their contents.`;
}

export function buildPrompt(
  question: string,
  context: string,
  hits: Retrieved[],
  mode: StudyMode,
  history: string,
): string {
  const guidance = MODE_GUIDANCE[mode];
  const pointers = citationOnlyNote(hits);

  if (!context.trim()) {
    return `${history}## Question

${guidance}

${question}

No study material was retrieved for this question. Say so, then answer only with
well-known syllabus facts you are certain of.${pointers}`;
  }

  return `${history}## Study material

${context}${pointers}

---

## Question

${guidance}

${question}

Answer in UPSC style, citing sources as [1], [2] to match the brackets above.`;
}

export function formatHistory(
  turns: Array<{ role: string; content: string }>,
  maxTurns = 3,
): string {
  const recent = turns.slice(-maxTurns * 2);
  if (!recent.length) return "";
  const lines = recent.map((turn) =>
    turn.role === "user"
      ? `Student: ${turn.content.slice(0, 500)}`
      : `Saarthi: ${turn.content.slice(0, 800)}`,
  );
  return `## Recent conversation\n${lines.join("\n")}\n\n`;
}
