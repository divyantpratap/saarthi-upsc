"use client";

import { useState } from "react";

import { addMockTest, type LocalMockTest } from "@/lib/local-library";
import type { Mcq } from "@/lib/types";

const EMPTY_OPTIONS = ["", "", "", ""];

export function CustomTestBuilder({
  onSaved,
  onCancel,
}: {
  onSaved: (test: LocalMockTest) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [minutes, setMinutes] = useState(20);
  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState<string[]>(EMPTY_OPTIONS);
  const [answerIndex, setAnswerIndex] = useState(0);
  const [explanation, setExplanation] = useState("");
  const [sourceRef, setSourceRef] = useState("");
  const [questions, setQuestions] = useState<Mcq[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const resetQuestion = () => {
    setQuestion("");
    setOptions(EMPTY_OPTIONS);
    setAnswerIndex(0);
    setExplanation("");
    setSourceRef("");
  };

  const addQuestion = () => {
    const cleanOptions = options.map((option) => option.trim());
    if (!question.trim() || cleanOptions.some((option) => !option)) {
      setError("Add the question and all four options.");
      return;
    }
    if (!explanation.trim()) {
      setError("Add an explanation so the test remains useful after marking.");
      return;
    }

    setQuestions((current) => [
      ...current,
      {
        question: question.trim(),
        options: cleanOptions,
        answerIndex,
        explanation: explanation.trim(),
        sourceRef: sourceRef.trim(),
        subject: subject.trim() || "Custom",
      },
    ]);
    setError(null);
    resetQuestion();
  };

  const save = async () => {
    if (!title.trim() || !subject.trim()) {
      setError("Give the test a title and subject.");
      return;
    }
    if (!questions.length) {
      setError("Add at least one question before saving the test.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const saved = await addMockTest({
        title: title.trim(),
        subject: subject.trim(),
        minutes,
        questions,
      });
      onSaved(saved);
    } catch (saveError) {
      setError(`Could not save this test: ${String(saveError)}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      aria-labelledby="custom-test-heading"
      className="mt-6 rounded-2xl border border-brand-line bg-surface p-4 sm:p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="custom-test-heading" className="font-display text-2xl">
            Create a custom test
          </h2>
          <p className="mt-1 text-[13px] text-muted">
            Saved only in this browser, alongside your source library.
          </p>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-line px-3 py-1.5 text-xs text-muted hover:text-ink"
        >
          Cancel
        </button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-[1fr_1fr_7rem]">
        <label className="text-xs font-semibold text-muted">
          Test title
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. Polity revision set"
            className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
          />
        </label>
        <label className="text-xs font-semibold text-muted">
          Subject
          <input
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            placeholder="Indian Polity"
            className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
          />
        </label>
        <label className="text-xs font-semibold text-muted">
          Minutes
          <input
            type="number"
            min={1}
            max={300}
            value={minutes}
            onChange={(event) =>
              setMinutes(Math.min(300, Math.max(1, Number(event.target.value) || 1)))
            }
            className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
          />
        </label>
      </div>

      <fieldset className="mt-6 border-t border-line pt-5">
        <legend className="px-2 text-[11px] font-bold uppercase tracking-[0.1em] text-saffron">
          Question {questions.length + 1}
        </legend>
        <label className="mt-1 block text-xs font-semibold text-muted">
          Question
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
          />
        </label>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {options.map((option, index) => (
            <label key={index} className="text-xs font-semibold text-muted">
              Option {"ABCD"[index]}
              <input
                value={option}
                onChange={(event) =>
                  setOptions((current) =>
                    current.map((value, optionIndex) =>
                      optionIndex === index ? event.target.value : value,
                    ),
                  )
                }
                className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
              />
            </label>
          ))}
        </div>

        <div className="mt-3 grid gap-3 sm:grid-cols-[9rem_1fr]">
          <label className="text-xs font-semibold text-muted">
            Correct option
            <select
              value={answerIndex}
              onChange={(event) => setAnswerIndex(Number(event.target.value))}
              className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
            >
              {[0, 1, 2, 3].map((index) => (
                <option key={index} value={index}>
                  {"ABCD"[index]}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs font-semibold text-muted">
            Source (optional)
            <input
              value={sourceRef}
              onChange={(event) => setSourceRef(event.target.value)}
              placeholder="Book, chapter, page"
              className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
            />
          </label>
        </div>

        <label className="mt-3 block text-xs font-semibold text-muted">
          Explanation
          <textarea
            value={explanation}
            onChange={(event) => setExplanation(event.target.value)}
            rows={3}
            placeholder="Explain the answer and why the distractors fail."
            className="mt-1 block w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm font-normal text-ink"
          />
        </label>
        <button
          type="button"
          onClick={addQuestion}
          className="mt-3 rounded-[10px] border border-brand-line px-4 py-2 text-[13px] font-semibold text-brand hover:bg-brand-tint"
        >
          Add question
        </button>
      </fieldset>

      {questions.length > 0 && (
        <div className="mt-5 border-t border-line pt-4">
          <p className="text-xs font-semibold text-muted">
            {questions.length} question{questions.length === 1 ? "" : "s"} ready
          </p>
          <ol className="mt-2 space-y-2">
            {questions.map((item, index) => (
              <li
                key={`${item.question}-${index}`}
                className="flex items-start justify-between gap-3 rounded-lg bg-paper px-3 py-2 text-sm"
              >
                <span className="line-clamp-2">
                  {index + 1}. {item.question}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setQuestions((current) =>
                      current.filter((_, questionIndex) => questionIndex !== index),
                    )
                  }
                  aria-label={`Remove question ${index + 1}`}
                  className="shrink-0 text-xs font-semibold text-wrong"
                >
                  Remove
                </button>
              </li>
            ))}
          </ol>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-4 rounded-lg bg-wrong-tint px-3 py-2 text-xs text-wrong">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={() => void save()}
        disabled={saving}
        className="mt-5 w-full rounded-[11px] bg-brand px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50 sm:w-auto"
      >
        {saving ? "Saving…" : "Save custom test"}
      </button>
    </section>
  );
}
