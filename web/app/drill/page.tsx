"use client";

import { useState } from "react";

import { QuizCard } from "@/components/QuizCard";
import { SUBJECTS } from "@/lib/question-bank";
import type { Mcq } from "@/lib/types";
import { readApiKey } from "@/lib/use-api-key";

const COUNTS = [3, 5, 10];

export default function DrillPage() {
  const [topic, setTopic] = useState("Fundamental Rights");
  const [count, setCount] = useState(5);
  const [questions, setQuestions] = useState<Mcq[] | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [grounded, setGrounded] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [busy, setBusy] = useState(false);
  const [score, setScore] = useState({ right: 0, answered: 0 });

  const start = async () => {
    setBusy(true);
    setQuestions(null);
    setNotice(null);
    setScore({ right: 0, answered: 0 });
    try {
      const response = await fetch("/api/drill", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ topic, count, apiKey: readApiKey() }),
      });
      if (!response.ok) {
        const message = (await response.text()).trim();
        setNotice(message || `Could not start the drill (${response.status}).`);
        setQuestions([]);
        return;
      }
      const data = await response.json();
      setQuestions(data.questions ?? []);
      setNotice(data.notice ?? null);
      setGrounded(Boolean(data.grounded));
      setGenerated(Boolean(data.generated));
    } catch (error) {
      setNotice(`Could not start the drill: ${String(error)}`);
      setQuestions([]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-6 pb-16 pt-6">
      <header className="border-b border-line pb-5 pl-10">
        <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-saffron">
          Deliberate practice
        </p>
        <h1 className="mt-2 font-display text-[38px] leading-tight tracking-[-0.03em]">
          Prelims drill
        </h1>
        <p className="mt-2 max-w-lg text-[14.5px] leading-relaxed text-muted">
          Attempt one question at a time. Check your answer when you are ready —
          nothing is revealed before you commit to an option.
        </p>
      </header>

      <section className="mt-6 rounded-2xl border border-line bg-surface p-4">
        <label
          htmlFor="topic"
          className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-faint"
        >
          Topic
        </label>
        <input
          id="topic"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && void start()}
          placeholder="e.g. Fundamental Rights, Monetary policy, Monsoon"
          className="mt-1.5 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-[14.5px] outline-none transition focus:border-brand"
        />

        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {SUBJECTS.map((subject) => (
            <button
              key={subject}
              type="button"
              onClick={() => setTopic(subject)}
              className="rounded-full border border-line px-2.5 py-1 text-[11.5px] text-muted transition hover:border-brand-line hover:text-brand"
            >
              {subject}
            </button>
          ))}
        </div>

        <div className="mt-4 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-0.5 rounded-lg border border-line bg-sunken p-0.5">
            {COUNTS.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setCount(option)}
                aria-pressed={count === option}
                className={`rounded-[7px] px-3 py-1.5 text-[12px] font-medium transition ${
                  count === option
                    ? "bg-surface text-ink shadow-sm"
                    : "text-muted hover:text-ink"
                }`}
              >
                {option} Qs
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => void start()}
            disabled={busy || !topic.trim()}
            className="rounded-[11px] bg-brand px-5 py-2.5 text-[13.5px] font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Writing questions…" : questions ? "New drill" : "Start drill"}
          </button>
        </div>
      </section>

      {notice && (
        <p className="mt-4 rounded-xl border border-[#eddcc6] bg-saffron-tint px-3.5 py-2.5 text-[12.5px] text-[#8a5220]">
          {notice}
        </p>
      )}

      {questions && questions.length > 0 && (
        <>
          <div className="mt-6 flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-[0.09em] text-faint">
              {grounded
                ? "Written from your library"
                : generated
                  ? "Written for this topic"
                  : "Saarthi question bank"}
            </p>
            {score.answered > 0 && (
              <p className="text-[12.5px] font-semibold text-muted">
                {score.right} / {score.answered} correct
              </p>
            )}
          </div>

          <div className="mt-3 flex flex-col gap-4">
            {questions.map((question, index) => (
              <QuizCard
                key={`${question.question.slice(0, 40)}-${index}`}
                question={question}
                index={index}
                total={questions.length}
                onAnswered={(right) =>
                  setScore((current) => ({
                    right: current.right + (right ? 1 : 0),
                    answered: current.answered + 1,
                  }))
                }
              />
            ))}
          </div>

          {score.answered === questions.length && (
            <div className="rise mt-5 rounded-2xl border border-brand-line bg-correct-tint p-5 text-center">
              <p className="font-display text-[28px] text-brand-dark">
                {score.right} / {questions.length}
              </p>
              <p className="mt-1 text-[13px] text-muted">
                Drill complete. Change the topic above to keep going.
              </p>
            </div>
          )}
        </>
      )}

      {busy && (
        <div className="mt-6 flex flex-col gap-4">
          {Array.from({ length: count }).map((_, i) => (
            <div
              key={i}
              className="h-40 animate-pulse rounded-2xl border border-line bg-surface/60"
            />
          ))}
        </div>
      )}
    </div>
  );
}
