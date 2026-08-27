"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { SourceList } from "@/components/SourceList";
import { ask, type Citation } from "@/lib/ask-client";
import type { StudyMode } from "@/lib/types";

const MODES: StudyMode[] = ["Learn", "Prelims", "Mains", "Evaluate"];

/**
 * Workflows that need their own screen link to it. The Streamlit build pushed
 * "Prelims drill" through the chat box, so the drill arrived as a wall of
 * markdown underneath the cards that launched it.
 */
const WORKFLOWS = [
  {
    title: "Prelims drill",
    body: "Attempt MCQs one at a time, check each answer, and read why the other options fail.",
    href: "/drill",
    cta: "Open drill",
  },
  {
    title: "Mock tests",
    body: "Full and sectional papers with UPSC negative marking and a reviewed score.",
    href: "/mock",
    cta: "Browse tests",
  },
] as const;

const PROMPTS = [
  "Explain the basic structure doctrine with key cases and a memory framework.",
  "Write a 150-word GS-II answer: constitutional morality is the soul of the Constitution.",
  "Help me revise the emergency provisions of the Constitution in 10 minutes.",
] as const;

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Citation[];
  notice?: string;
  error?: boolean;
  mode?: StudyMode;
  model?: string;
}

export default function AskPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [mode, setMode] = useState<StudyMode>("Learn");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const submit = useCallback(
    async (question: string) => {
      if (!question.trim() || busy) return;
      setBusy(true);
      setDraft("");

      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      setMessages((current) => [
        ...current,
        { role: "user", content: question },
        { role: "assistant", content: "", mode },
      ]);

      const patch = (update: (message: Message) => Message) =>
        setMessages((current) => {
          const next = [...current];
          next[next.length - 1] = update(next[next.length - 1]);
          return next;
        });

      try {
        await ask(question, mode, history, {
          onSources: (sources) => patch((m) => ({ ...m, sources })),
          onNotice: (notice) => patch((m) => ({ ...m, notice })),
          onModel: (model) => patch((m) => ({ ...m, model })),
          onText: (delta) =>
            patch((m) => ({ ...m, content: m.content + delta })),
          onError: (message) =>
            patch((m) => ({ ...m, content: message, error: true })),
        });
      } catch (error) {
        patch((m) => ({ ...m, content: String(error), error: true }));
      } finally {
        setBusy(false);
        endRef.current?.scrollIntoView({ behavior: "smooth" });
      }
    },
    [busy, messages, mode],
  );

  const empty = messages.length === 0;

  return (
    <div className="mx-auto flex min-h-full max-w-3xl flex-col px-6 pb-10 pt-6">
      <header className="mb-5 flex items-center justify-between border-b border-line pb-3 pl-10">
        <p className="text-[13px] text-muted">
          Saarthi / <b className="text-ink">{empty ? "New chat" : mode} </b>
        </p>
        <div className="flex gap-0.5 rounded-lg border border-line bg-sunken p-0.5">
          {MODES.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setMode(option)}
              aria-pressed={mode === option}
              className={`rounded-[7px] px-3 py-1.5 text-[12px] font-medium transition ${
                mode === option
                  ? "bg-surface text-ink shadow-sm"
                  : "text-muted hover:text-ink"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      </header>

      {empty ? (
        <section className="py-10 text-center">
          <p className="text-[11px] font-bold uppercase tracking-[0.13em] text-saffron">
            Built only for UPSC CSE
          </p>
          <h1 className="mx-auto mt-3 max-w-xl font-display text-[42px] leading-[1.05] tracking-[-0.035em]">
            What will you master today?
          </h1>
          <p className="mx-auto mt-3 max-w-md text-[15px] leading-relaxed text-muted">
            Ask from your study library and get the exact source passage behind
            every response.
          </p>
        </section>
      ) : (
        <div className="flex flex-col gap-6">
          {messages.map((message, i) =>
            message.role === "user" ? (
              <div key={i} className="flex justify-end">
                <p className="max-w-[82%] rounded-[18px] rounded-br-[4px] border border-line bg-[#e9ebe6] px-4 py-2.5 text-[14.5px] leading-relaxed">
                  {message.content}
                </p>
              </div>
            ) : (
              <article key={i} className="rise">
                {message.notice && (
                  <p className="mb-2 inline-block rounded-full bg-saffron-tint px-2.5 py-1 text-[10.5px] font-medium text-saffron">
                    {message.notice}
                  </p>
                )}
                {message.content ? (
                  <div
                    className={`prose-answer ${
                      message.error
                        ? "rounded-xl border border-[#e4c9c3] bg-wrong-tint px-4 py-3 text-[13.5px] text-wrong"
                        : ""
                    }`}
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="flex items-center gap-2 text-[13px] text-muted">
                    <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-brand" />
                    Finding the strongest passages…
                  </p>
                )}
                {!message.error && (
                  <>
                    {message.model && (
                      <p className="mt-2 text-[10.5px] text-faint">
                        {message.mode} · answered by {message.model}
                      </p>
                    )}
                    <SourceList sources={message.sources ?? []} />
                  </>
                )}
              </article>
            ),
          )}
          <div ref={endRef} />
        </div>
      )}

      <div className="sticky bottom-0 mt-6 bg-paper pt-3">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void submit(draft);
          }}
          className="rounded-[18px] border border-line-strong bg-surface p-3 shadow-[0_12px_35px_rgba(32,45,39,0.10)]"
        >
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit(draft);
              }
            }}
            rows={2}
            placeholder={`Ask a UPSC question in ${mode} mode…`}
            className="w-full resize-none bg-transparent px-1 py-1 text-[15.5px] outline-none placeholder:text-faint"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="mt-1.5 w-full rounded-[11px] bg-brand py-2.5 text-[14px] font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Thinking…" : "Ask Saarthi →"}
          </button>
        </form>
      </div>

      {empty && (
        <>
          <p className="mb-2.5 mt-8 text-[11px] font-bold uppercase tracking-[0.09em] text-faint">
            Or start a guided workflow
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {WORKFLOWS.map((workflow) => (
              <Link
                key={workflow.href}
                href={workflow.href}
                className="group rounded-2xl border border-line bg-surface p-4 transition hover:border-brand-line hover:shadow-sm"
              >
                <b className="text-[14px]">{workflow.title}</b>
                <p className="mt-1.5 text-[13px] leading-relaxed text-muted">
                  {workflow.body}
                </p>
                <span className="mt-3 inline-block text-[12.5px] font-semibold text-brand">
                  {workflow.cta} →
                </span>
              </Link>
            ))}
          </div>

          <p className="mb-2.5 mt-6 text-[11px] font-bold uppercase tracking-[0.09em] text-faint">
            Or try a question
          </p>
          <div className="flex flex-col gap-2">
            {PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => void submit(prompt)}
                className="rounded-xl border border-line bg-surface px-3.5 py-2.5 text-left text-[13px] text-muted transition hover:border-brand-line hover:text-ink"
              >
                {prompt}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
