"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useSyncExternalStore } from "react";

import { IndexStatus } from "./IndexStatus";
import { SidebarPanels } from "./SidebarPanels";

const NARROW = "(max-width: 900px)";

/*
 * The viewport is external state. Reading it through a store rather than an
 * effect keeps the first paint correct and, unlike the previous version, keeps
 * responding when the window is resized.
 */
function subscribeToWidth(listener: () => void) {
  const query = window.matchMedia(NARROW);
  query.addEventListener("change", listener);
  return () => query.removeEventListener("change", listener);
}

const isNarrowNow = () => window.matchMedia(NARROW).matches;
const isNarrowOnServer = () => false;

const NAV = [
  { href: "/", label: "Ask Saarthi", glyph: "◉" },
  { href: "/drill", label: "Prelims drill", glyph: "✎" },
  { href: "/mock", label: "Mock tests", glyph: "✓" },
  { href: "/library", label: "Source library", glyph: "▤" },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const narrow = useSyncExternalStore(
    subscribeToWidth,
    isNarrowNow,
    isNarrowOnServer,
  );
  // Collapsed by default on small screens, where an 18rem rail would eat the
  // page — until the reader says otherwise, and then their choice wins.
  const [override, setOverride] = useState<boolean | null>(null);
  const open = override ?? !narrow;

  return (
    <div className="flex h-full">
      {/*
       * The toggle lives outside the sidebar, so it survives collapse. The
       * Streamlit build hid the only expand control along with the header,
       * which made a closed sidebar unrecoverable without a reload.
       */}
      <button
        type="button"
        onClick={() => setOverride(!open)}
        aria-expanded={open}
        aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
        className="fixed top-4 left-4 z-50 grid h-9 w-9 place-items-center rounded-lg border border-line bg-surface text-muted shadow-sm transition hover:text-ink hover:border-line-strong"
        style={{ left: open ? "17.25rem" : "1rem" }}
      >
        <span className="text-sm leading-none">{open ? "‹" : "›"}</span>
      </button>

      <aside
        className={`${
          open ? "w-[18rem]" : "w-0"
        } shrink-0 overflow-hidden border-r border-line bg-sunken transition-[width] duration-200`}
      >
        <div className="flex h-full w-[18rem] flex-col px-4 py-5">
          <Link href="/" className="mb-7 flex items-center gap-3 px-1">
            <span className="grid h-9 w-9 place-items-center rounded-[10px] bg-brand font-display text-xl text-white">
              S
            </span>
            <span>
              <b className="block text-[17px] font-semibold tracking-tight">
                Saarthi
              </b>
              <small className="block text-[10px] uppercase tracking-[0.09em] text-muted">
                UPSC study intelligence
              </small>
            </span>
          </Link>

          <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.11em] text-faint">
            Workspace
          </p>
          <nav className="flex flex-col gap-1">
            {NAV.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2.5 rounded-[10px] px-3 py-2.5 text-sm font-medium transition ${
                    active
                      ? "bg-brand text-white shadow-sm"
                      : "text-[#33413c] hover:bg-[#e2e4df]"
                  }`}
                >
                  <span className="w-3 text-center text-xs opacity-80">
                    {item.glyph}
                  </span>
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <IndexStatus />
          <div className="mt-auto pt-4">
            <SidebarPanels />
          </div>
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
