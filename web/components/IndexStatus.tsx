"use client";

import { useEffect, useState } from "react";

interface Status {
  ok: boolean;
  chunks?: number;
  sources?: number;
  openSources?: number;
  configuredModel?: string;
  retrievalMode?: "lexical" | "hybrid";
  error?: string;
}

/**
 * A real readout, not a decorative badge. If the index failed to load, this
 * says so — the previous build showed "Sources grounded" regardless.
 */
export function IndexStatus() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/status")
      .then((response) => response.json())
      .then((data) => !cancelled && setStatus(data))
      .catch(() => !cancelled && setStatus({ ok: false }));
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status) {
    return (
      <div className="mt-5 rounded-xl border border-line bg-surface/60 px-3 py-2.5">
        <div className="h-2 w-24 animate-pulse rounded bg-line" />
      </div>
    );
  }

  if (!status.ok) {
    return (
      <div className="mt-5 rounded-xl border border-[#e4c9c3] bg-wrong-tint px-3 py-2.5">
        <p className="text-[12px] font-semibold text-wrong">Index unavailable</p>
        <p className="mt-1 text-[10.5px] leading-relaxed text-muted">
          Retrieval is offline, so answers would not be grounded. Run{" "}
          <code className="text-[10px]">ingest/build_index.py</code>.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-5 rounded-xl border border-line bg-surface/60 px-3 py-2.5">
      <p className="flex items-center gap-1.5 text-[12px] font-semibold text-ink">
        <span className="inline-block h-[7px] w-[7px] rounded-full bg-[#41a476]" />
        Source library ready
      </p>
      <p className="mt-1 text-[10.5px] leading-relaxed text-muted">
        {status.sources?.toLocaleString()} source
        {status.sources === 1 ? "" : "s"} ·{" "}
        {status.chunks?.toLocaleString()} passages indexed
      </p>
      <p className="mt-0.5 text-[10.5px] text-faint">
        {status.retrievalMode === "hybrid"
          ? "Keyword + semantic retrieval"
          : "Complete keyword index · semantic upgrade pending"}
      </p>
      <p className="mt-0.5 text-[10.5px] text-faint">
        Configured: {status.configuredModel}
      </p>
    </div>
  );
}
