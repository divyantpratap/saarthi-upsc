"use client";

import { useState } from "react";

import { useApiKey } from "@/lib/use-api-key";

type PanelId = "key" | "about";

/**
 * One accordion, one open panel.
 *
 * The Streamlit sidebar used two independent expanders, so opening the second
 * left the first open underneath it and the rail grew unbounded. A single piece
 * of state makes that impossible.
 */
export function SidebarPanels() {
  const [openPanel, setOpenPanel] = useState<PanelId | null>(null);
  const { apiKey, setApiKey, clearApiKey } = useApiKey();

  const toggle = (panel: PanelId) =>
    setOpenPanel((current) => (current === panel ? null : panel));

  return (
    <div className="flex flex-col gap-1.5">
      <Panel
        id="key"
        label="API key & privacy"
        open={openPanel === "key"}
        onToggle={toggle}
      >
        <p className="text-[11.5px] leading-relaxed text-muted">
          Optional. Use your own Gemini key and it stays in this browser tab
          only — never written to disk, logs, or the server.
        </p>
        <input
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="AIza…"
          autoComplete="off"
          className="mt-2 w-full rounded-lg border border-line bg-surface px-2.5 py-2 text-xs outline-none transition focus:border-brand"
        />
        {apiKey ? (
          <button
            type="button"
            onClick={clearApiKey}
            className="mt-2 w-full rounded-lg border border-line bg-surface px-2 py-1.5 text-[11px] font-medium text-muted transition hover:text-ink"
          >
            Forget my key
          </button>
        ) : (
          <p className="mt-2 text-[10.5px] text-faint">
            Using the shared demo key.
          </p>
        )}
        <p className="mt-2 text-[10.5px] text-faint">
          Do not enter personal or account information.
        </p>
      </Panel>

      <Panel
        id="about"
        label="How Saarthi answers"
        open={openPanel === "about"}
        onToggle={toggle}
      >
        <p className="text-[11.5px] leading-relaxed text-muted">
          Every question runs keyword search and semantic search over a prebuilt
          index, then the top passages are sent to Gemini. The passages behind
          each answer are listed with it, so you can check the source rather than
          trust the model.
        </p>
      </Panel>
    </div>
  );
}

function Panel({
  id,
  label,
  open,
  onToggle,
  children,
}: {
  id: PanelId;
  label: string;
  open: boolean;
  onToggle: (id: PanelId) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface/70">
      <button
        type="button"
        onClick={() => onToggle(id)}
        aria-expanded={open}
        className="flex w-full items-center justify-between px-3 py-2.5 text-left text-[12.5px] font-medium text-[#33413c] transition hover:bg-[#e9ebe6]"
      >
        {label}
        <span
          className={`text-[10px] text-faint transition-transform ${
            open ? "rotate-90" : ""
          }`}
        >
          ›
        </span>
      </button>
      {open && <div className="border-t border-line px-3 py-2.5">{children}</div>}
    </div>
  );
}
