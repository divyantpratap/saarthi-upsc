"use client";

import { useEffect, useState } from "react";

/**
 * Rotating status while an answer is being written.
 *
 * A grounded answer takes real time — retrieval, then a model that sometimes
 * has to fail over before it starts writing. A single frozen "Thinking…" makes
 * that read as a hang. These say what is actually happening, in order, so the
 * wait has shape.
 */
const STAGES = [
  "Consulting the source library…",
  "Cross-referencing NCERT…",
  "Marshalling the marginalia…",
  "Combobulating the clauses…",
  "Interrogating the index…",
  "Deliberating like a Drafting Committee…",
  "Triangulating the syllabus…",
  "Weighing the precedents…",
  "Annotating in the margins…",
  "Composing in exam hand…",
] as const;

const INTERVAL_MS = 2600;

export function ThinkingStatus({ compact = false }: { compact?: boolean }) {
  const stage = useStage(true);

  return (
    <p
      className={`flex items-center gap-2 text-muted ${
        compact ? "text-[12.5px]" : "text-[13px]"
      }`}
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="inline-block h-2 w-2 shrink-0 animate-pulse rounded-full bg-brand" />
      <span key={stage} className="rise">
        {STAGES[stage]}
      </span>
    </p>
  );
}

/**
 * Which line to show, derived from how long we have been waiting.
 *
 * The elapsed time is the source of truth rather than an incrementing counter,
 * so nothing has to be reset when a request ends — the next one simply starts
 * its own clock.
 */
function useStage(active: boolean): number {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!active) return;
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - started), 400);
    return () => clearInterval(timer);
  }, [active]);

  if (!active) return 0;
  return Math.min(Math.floor(elapsed / INTERVAL_MS), STAGES.length - 1);
}

/** The composer button label, kept in step with the status line. */
export function useThinkingLabel(busy: boolean): string {
  const stage = useStage(busy);
  return busy ? STAGES[stage] : "Ask Saarthi  →";
}
