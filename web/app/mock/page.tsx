"use client";

import { useEffect, useMemo, useState } from "react";

import { CustomTestBuilder } from "@/components/CustomTestBuilder";
import { QuizCard } from "@/components/QuizCard";
import {
  listMockTests,
  removeMockTest,
  type LocalMockTest,
} from "@/lib/local-library";
import { QUESTIONS, SUBJECTS } from "@/lib/question-bank";
import type { Mcq } from "@/lib/types";

/** UPSC Prelims marking: +2 for a correct answer, −1/3 of that for a wrong one. */
const CORRECT_MARK = 2;
const NEGATIVE_MARK = 2 / 3;

interface Test {
  id: string;
  title: string;
  kind: string;
  subject: string;
  minutes: number;
  questions: Mcq[];
  custom?: boolean;
}

function buildTests(): Test[] {
  const sectional = SUBJECTS.map((subject) => ({
    id: `sectional-${subject.toLowerCase().replace(/\W+/g, "-")}`,
    title: `${subject} — Sectional`,
    kind: "Sectional",
    subject,
    minutes: 10,
    questions: QUESTIONS.filter((question) => question.subject === subject),
  })).filter((test) => test.questions.length > 0);

  return [
    ...sectional,
    {
      id: "full-gs-1",
      title: "GS Paper I — Full-length starter",
      kind: "Full length",
      subject: "Mixed GS",
      minutes: 20,
      questions: QUESTIONS,
    },
  ];
}

export default function MockPage() {
  const builtInTests = useMemo(() => buildTests(), []);
  const [customTests, setCustomTests] = useState<LocalMockTest[]>([]);
  const [building, setBuilding] = useState(false);
  const [storageNotice, setStorageNotice] = useState<string | null>(null);
  const [active, setActive] = useState<Test | null>(null);
  const [score, setScore] = useState({ right: 0, wrong: 0 });

  useEffect(() => {
    let cancelled = false;
    listMockTests()
      .then((saved) => {
        if (!cancelled) setCustomTests(saved);
      })
      .catch((error) => {
        if (!cancelled) {
          setStorageNotice(`Saved tests are unavailable: ${String(error)}`);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tests: Test[] = [
    ...customTests.map((test) => ({ ...test, kind: "Custom", custom: true })),
    ...builtInTests,
  ];

  if (active) {
    const attempted = score.right + score.wrong;
    const marks = score.right * CORRECT_MARK - score.wrong * NEGATIVE_MARK;

    return (
      <div className="mx-auto max-w-3xl px-6 pb-16 pt-6">
        <header className="flex flex-col gap-4 border-b border-line pb-5 pl-10 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="font-display text-[30px] leading-tight tracking-[-0.03em]">
              {active.title}
            </h1>
            <p className="mt-1 text-[13px] text-muted">
              {active.questions.length} questions · +{CORRECT_MARK} correct · −
              {NEGATIVE_MARK.toFixed(2)} incorrect
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setActive(null);
              setScore({ right: 0, wrong: 0 });
            }}
            className="shrink-0 rounded-[10px] border border-line bg-surface px-3.5 py-2 text-[12.5px] font-medium text-muted transition hover:text-ink"
          >
            Exit test
          </button>
        </header>

        {attempted > 0 && (
          <div className="mt-5 flex items-center justify-between rounded-xl border border-brand-line bg-correct-tint px-4 py-3">
            <span className="text-[13px] text-muted">
              {attempted} of {active.questions.length} attempted
            </span>
            <span className="font-display text-[20px] text-brand-dark">
              {marks.toFixed(2)} marks
            </span>
          </div>
        )}

        <div className="mt-4 flex flex-col gap-4">
          {active.questions.map((question, index) => (
            <QuizCard
              key={`${question.question.slice(0, 48)}-${index}`}
              question={question}
              index={index}
              total={active.questions.length}
              onAnswered={(correct) =>
                setScore((current) => ({
                  right: current.right + (correct ? 1 : 0),
                  wrong: current.wrong + (correct ? 0 : 1),
                }))
              }
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 pb-16 pt-6">
      <header className="border-b border-line pb-5 pl-10">
        <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-saffron">
          Exam simulation
        </p>
        <h1 className="mt-2 font-display text-[38px] leading-tight tracking-[-0.03em]">
          Mock tests
        </h1>
        <p className="mt-2 max-w-lg text-[14.5px] leading-relaxed text-muted">
          Build speed and judgement under UPSC conditions, with negative marking
          and a written explanation for every question.
        </p>
      </header>

      <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-brand-line bg-brand-tint p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-[15px] font-semibold text-brand-dark">
            Bring your own question set
          </h2>
          <p className="mt-1 text-[12.5px] leading-relaxed text-muted">
            Create a reusable mock that stays private in this browser.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setBuilding((current) => !current)}
          aria-expanded={building}
          className="shrink-0 rounded-[10px] bg-brand px-4 py-2.5 text-[13px] font-semibold text-white hover:bg-brand-dark"
        >
          {building ? "Close builder" : "Create custom test"}
        </button>
      </div>

      {building && (
        <CustomTestBuilder
          onCancel={() => setBuilding(false)}
          onSaved={(test) => {
            setCustomTests((current) => [test, ...current]);
            setBuilding(false);
            setStorageNotice("Custom test saved in this browser.");
          }}
        />
      )}

      {storageNotice && (
        <p role="status" className="mt-4 rounded-xl bg-sunken px-3.5 py-2.5 text-xs text-muted">
          {storageNotice}
        </p>
      )}

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {tests.map((test) => (
          <article
            key={test.id}
            className="group flex flex-col rounded-2xl border border-line bg-surface p-4 transition hover:border-brand-line hover:shadow-sm"
          >
            <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-brand">
              {test.kind}
            </span>
            <b className="mt-2 block text-[15px]">{test.title}</b>
            <p className="mt-2 flex gap-1.5">
              <span className="rounded-full bg-sunken px-2 py-0.5 text-[11px] text-muted">
                {test.questions.length} questions
              </span>
              <span className="rounded-full bg-sunken px-2 py-0.5 text-[11px] text-muted">
                {test.minutes} min
              </span>
            </p>
            <div className="mt-auto flex items-center justify-between gap-3 pt-3">
              <button
                type="button"
                onClick={() => {
                  setActive(test);
                  setScore({ right: 0, wrong: 0 });
                }}
                className="text-[12.5px] font-semibold text-brand"
              >
                Begin test →
              </button>
              {test.custom && (
                <button
                  type="button"
                  onClick={() => {
                    void removeMockTest(test.id)
                      .then(() =>
                        setCustomTests((current) =>
                          current.filter((item) => item.id !== test.id),
                        ),
                      )
                      .catch((error) =>
                        setStorageNotice(`Could not delete test: ${String(error)}`),
                      );
                  }}
                  aria-label={`Delete ${test.title}`}
                  className="text-xs font-semibold text-wrong"
                >
                  Delete
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
