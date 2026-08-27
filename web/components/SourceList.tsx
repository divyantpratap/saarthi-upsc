"use client";

import { useState } from "react";

import type { Citation } from "@/lib/ask-client";

/**
 * The passages behind an answer.
 *
 * Sources from commercial titles are shown as a location without their text —
 * the student is pointed at the page in a book they may own, rather than served
 * a reproduction of it.
 */
export function SourceList({ sources }: { sources: Citation[] }) {
  const [open, setOpen] = useState(false);
  if (!sources.length) return null;

  const quotable = sources.filter((source) => !source.citationOnly).length;

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5 text-[11.5px] font-medium text-muted transition hover:border-line-strong hover:text-ink"
      >
        <span className={`text-[9px] transition-transform ${open ? "rotate-90" : ""}`}>
          ›
        </span>
        {sources.length} source{sources.length === 1 ? "" : "s"}
        {quotable < sources.length && (
          <span className="text-faint">· {quotable} quotable</span>
        )}
      </button>

      {open && (
        <div className="mt-2 flex flex-col gap-2">
          {sources.map((source, i) => (
            <article
              key={`${source.file}-${source.page}-${i}`}
              className="rounded-xl border border-line bg-surface px-3.5 py-3"
            >
              <header className="flex items-baseline justify-between gap-3">
                <span className="text-[12px] font-semibold text-ink">
                  [{i + 1}] {source.file}
                </span>
                <span className="shrink-0 whitespace-nowrap text-[11px] text-saffron">
                  {source.page ? `Page ${source.page}` : "Reference"}
                  {source.relevance ? ` · ${source.relevance}% match` : ""}
                </span>
              </header>
              <p className="mt-0.5 text-[10px] uppercase tracking-[0.08em] text-faint">
                {source.subject || "UPSC source"}
              </p>
              {source.preview ? (
                <p className="mt-2 font-display text-[13.5px] leading-relaxed text-[#47514d]">
                  {source.preview}…
                </p>
              ) : (
                <p className="mt-2 rounded-lg bg-sunken px-2.5 py-2 text-[11.5px] leading-relaxed text-muted">
                  Matched in your library. The passage is not reproduced here —
                  open this page in your own copy.
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
