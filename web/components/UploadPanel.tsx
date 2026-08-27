"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { chunkText } from "@/lib/chunk";
import {
  addDocument,
  listDocuments,
  removeDocument,
  type LocalDocument,
} from "@/lib/local-library";

const MAX_BYTES = 40 * 1024 * 1024;

/**
 * Parses a PDF entirely in the browser.
 *
 * This path is fed files by whoever is using the page, and PDF.js has carried
 * arbitrary-JS-execution advisories against malicious documents. pdfjs-dist is
 * pinned past the known one (>= 6.2.108), and v6 removed script evaluation
 * altogether, so there is no eval switch left to turn off here.
 */
async function extractPages(file: File): Promise<Array<{ page: number; text: string }>> {
  const pdfjs = await import("pdfjs-dist");
  pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.min.mjs",
    import.meta.url,
  ).toString();

  const buffer = await file.arrayBuffer();
  const loadingTask = pdfjs.getDocument({
    data: new Uint8Array(buffer),
    disableAutoFetch: true,
  });
  const pdf = await loadingTask.promise;

  const pages: Array<{ page: number; text: string }> = [];
  for (let number = 1; number <= pdf.numPages; number++) {
    const page = await pdf.getPage(number);
    const content = await page.getTextContent();
    const text = content.items
      .map((item) => ("str" in item ? item.str : ""))
      .join(" ")
      .trim();
    if (text) pages.push({ page: number, text });
    page.cleanup();
  }
  await loadingTask.destroy();
  return pages;
}

export function UploadPanel() {
  const [documents, setDocuments] = useState<LocalDocument[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(() => {
    listDocuments().then(setDocuments).catch(() => setDocuments([]));
  }, []);

  useEffect(refresh, [refresh]);

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    setError(null);

    for (const file of Array.from(files)) {
      try {
        if (file.size > MAX_BYTES) {
          throw new Error(
            `${file.name} is ${(file.size / 1e6).toFixed(0)}MB — the limit is 40MB.`,
          );
        }
        setStatus(`Reading ${file.name}…`);
        const pages = await extractPages(file);
        if (!pages.length) {
          throw new Error(
            `${file.name} has no selectable text. Scanned PDFs need OCR first.`,
          );
        }

        setStatus(`Indexing ${file.name}…`);
        const pieces: Array<{ text: string; page?: number }> = [];
        let index = 0;
        for (const { page, text } of pages) {
          const chunks = chunkText(text, { page, startIndex: index });
          index += chunks.length;
          pieces.push(...chunks.map((c) => ({ text: c.text, page: c.page })));
        }

        await addDocument(file.name, pages.length, pieces);
        setStatus(`Added ${file.name} — ${pieces.length} passages.`);
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
        setStatus(null);
      }
    }

    setBusy(false);
    refresh();
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <section className="mt-7">
      <h2 className="text-[11px] font-bold uppercase tracking-[0.09em] text-faint">
        Your uploads · {documents.length}
      </h2>
      <p className="mt-1 text-[12.5px] text-muted">
        Added in this browser only. Nothing is uploaded to a server, and clearing
        site data removes them.
      </p>

      <div className="mt-3 rounded-2xl border border-dashed border-line-strong bg-surface/60 p-4 text-center">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          disabled={busy}
          onChange={(event) => void handleFiles(event.target.files)}
          className="block w-full text-[12.5px] text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-brand file:px-4 file:py-2 file:text-[12.5px] file:font-semibold file:text-white hover:file:bg-brand-dark disabled:opacity-50"
        />
        {status && <p className="mt-2.5 text-[12px] text-brand">{status}</p>}
        {error && (
          <p className="mt-2.5 rounded-lg bg-wrong-tint px-3 py-2 text-[12px] text-wrong">
            {error}
          </p>
        )}
      </div>

      {documents.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1.5">
          {documents.map((document) => (
            <li
              key={document.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-line bg-surface px-3.5 py-3"
            >
              <span className="min-w-0">
                <b className="block truncate text-[13.5px] font-medium">
                  {document.name}
                </b>
                <span className="text-[11px] text-faint">
                  {document.pages} pages · {document.chunks.toLocaleString()}{" "}
                  passages
                </span>
              </span>
              <button
                type="button"
                onClick={() => void removeDocument(document.id).then(refresh)}
                className="shrink-0 rounded-lg border border-line px-2.5 py-1.5 text-[11.5px] text-muted transition hover:border-[#e4c9c3] hover:text-wrong"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
