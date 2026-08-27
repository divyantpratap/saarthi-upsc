"use client";

import { useEffect, useState } from "react";

import { UploadPanel } from "@/components/UploadPanel";

interface Source {
  key: string;
  file: string;
  subject: string;
  tier: "A" | "B";
  chunks: number;
}

export default function LibraryPage() {
  const [sources, setSources] = useState<Source[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/sources")
      .then((response) => response.json())
      .then((data) =>
        data.ok ? setSources(data.sources) : setError(data.error),
      )
      .catch((cause) => setError(String(cause)));
  }, []);

  const quotable = sources?.filter((source) => source.tier === "A") ?? [];
  const referenceOnly = sources?.filter((source) => source.tier === "B") ?? [];

  return (
    <div className="mx-auto max-w-3xl px-6 pb-16 pt-6">
      <header className="border-b border-line pb-5 pl-10">
        <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-saffron">
          What Saarthi reads
        </p>
        <h1 className="mt-2 font-display text-[38px] leading-tight tracking-[-0.03em]">
          Source library
        </h1>
        <p className="mt-2 max-w-xl text-[14.5px] leading-relaxed text-muted">
          Every passage in the index, and which of them Saarthi may quote back to
          you.
        </p>
      </header>

      {error && (
        <p className="mt-6 rounded-xl border border-[#e4c9c3] bg-wrong-tint px-4 py-3 text-[13px] text-wrong">
          {error}
        </p>
      )}

      {!sources && !error && (
        <div className="mt-6 flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-14 animate-pulse rounded-xl border border-line bg-surface/60"
            />
          ))}
        </div>
      )}

      {sources && (
        <>
          <SourceGroup
            title="Quotable sources"
            caption="Freely redistributable. Saarthi shows these passages in full."
            sources={quotable}
          />
          <SourceGroup
            title="Reference-only sources"
            caption="Matched and cited by page, but never reproduced — open your own copy."
            sources={referenceOnly}
          />
          <UploadPanel />
        </>
      )}
    </div>
  );
}

function SourceGroup({
  title,
  caption,
  sources,
}: {
  title: string;
  caption: string;
  sources: Source[];
}) {
  if (!sources.length) return null;
  return (
    <section className="mt-7">
      <h2 className="text-[11px] font-bold uppercase tracking-[0.09em] text-faint">
        {title} · {sources.length}
      </h2>
      <p className="mt-1 text-[12.5px] text-muted">{caption}</p>
      <ul className="mt-3 flex flex-col gap-1.5">
        {sources.map((source) => (
          <li
            key={source.key}
            className="flex items-center justify-between gap-4 rounded-xl border border-line bg-surface px-3.5 py-3"
          >
            <span className="min-w-0">
              <b className="block truncate text-[13.5px] font-medium">
                {source.file}
              </b>
              <span className="text-[11px] uppercase tracking-[0.07em] text-faint">
                {source.subject}
              </span>
            </span>
            <span className="shrink-0 rounded-full bg-sunken px-2.5 py-1 text-[11px] text-muted">
              {source.chunks.toLocaleString()} passages
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
