"use client";

import { useState } from "react";

import type { Mcq } from "@/lib/types";

/**
 * One question, one independent piece of state.
 *
 * Deliberately self-contained: nothing here reads or writes a sibling's state,
 * so checking question 3 can never reveal or reset question 4.
 */
export function QuizCard({
  question,
  index,
  total,
  onAnswered,
}: {
  question: Mcq;
  index: number;
  total: number;
  onAnswered?: (correct: boolean) => void;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const [checked, setChecked] = useState(false);

  const correct = checked && selected === question.answerIndex;

  const check = () => {
    if (selected === null || checked) return;
    setChecked(true);
    onAnswered?.(selected === question.answerIndex);
  };

  return (
    <article className="rise rounded-2xl border border-line bg-surface p-5">
      <header className="flex items-baseline justify-between gap-3">
        <span className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-saffron">
          Question {index + 1} of {total}
        </span>
        <span className="text-[10.5px] uppercase tracking-[0.08em] text-faint">
          {question.subject}
        </span>
      </header>

      <p
        id={`question-${index}`}
        className="mt-3 whitespace-pre-line text-[16px] leading-relaxed text-ink"
      >
        {question.question}
      </p>

      {/* One option per row — never side by side. */}
      <fieldset
        aria-labelledby={`question-${index}`}
        className="mt-4 flex flex-col gap-2"
      >
        <legend className="sr-only">Choose one answer</legend>
        {question.options.map((option, optionIndex) => {
          const isAnswer = optionIndex === question.answerIndex;
          const isPicked = optionIndex === selected;

          let tone = "border-line bg-surface hover:border-line-strong";
          if (checked && isAnswer) {
            tone = "border-brand-line bg-correct-tint";
          } else if (checked && isPicked) {
            tone = "border-[#e4c9c3] bg-wrong-tint";
          } else if (isPicked) {
            tone = "border-brand bg-brand-tint";
          }

          return (
            <label
              key={optionIndex}
              className={`flex cursor-pointer items-start gap-3 rounded-xl border px-3.5 py-3 transition focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-brand ${tone} ${
                checked ? "cursor-default" : ""
              }`}
            >
              <input
                type="radio"
                name={`q-${index}`}
                checked={isPicked}
                disabled={checked}
                onChange={() => setSelected(optionIndex)}
                className="mt-[3px] h-4 w-4 shrink-0 accent-[#1f6b54]"
              />
              <span className="text-[14px] leading-relaxed">
                <b className="mr-1.5 font-semibold text-muted">
                  {"ABCD"[optionIndex]}.
                </b>
                {option}
              </span>
              {checked && isAnswer && (
                <span className="ml-auto shrink-0 text-[11px] font-semibold text-correct">
                  Correct
                </span>
              )}
            </label>
          );
        })}
      </fieldset>

      {!checked ? (
        <button
          type="button"
          onClick={check}
          disabled={selected === null}
          className="mt-4 rounded-[11px] bg-brand px-5 py-2.5 text-[13.5px] font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-40"
        >
          Check answer
        </button>
      ) : (
        <div className="mt-4" role="status" aria-live="polite" aria-atomic="true">
          <p
            className={`inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[12.5px] font-bold ${
              correct
                ? "bg-correct-tint text-correct"
                : "bg-wrong-tint text-wrong"
            }`}
          >
            {correct ? "✓ Right answer" : "✕ Wrong answer"}
          </p>
          {!correct && (
            <p className="mt-2.5 text-[13px] text-muted">
              Correct answer:{" "}
              <b className="text-ink">
                {"ABCD"[question.answerIndex]}.{" "}
                {question.options[question.answerIndex]}
              </b>
            </p>
          )}

          <div className="mt-3 rounded-xl border border-line bg-paper px-4 py-3">
            <p className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-faint">
              Explanation
            </p>
            <p className="mt-1.5 whitespace-pre-line text-[13.5px] leading-relaxed text-[#3d4744]">
              {question.explanation}
            </p>
            {question.sourceRef && (
              <p className="mt-2.5 border-t border-line pt-2 text-[11.5px] text-saffron">
                {question.sourceRef}
              </p>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
