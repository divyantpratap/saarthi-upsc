"use client";

import { readApiKey } from "./use-api-key";
import type { StudyMode } from "./types";

export interface Citation {
  file: string;
  subject: string;
  page: number | null;
  paragraph: number | null;
  relevance: number;
  preview: string | null;
  citationOnly: boolean;
}

export interface AskHandlers {
  onSources?: (sources: Citation[], route: string) => void;
  onText?: (delta: string) => void;
  onNotice?: (notice: string) => void;
  onModel?: (model: string) => void;
  onError?: (message: string, rateLimited: boolean) => void;
}

type Frame =
  | { type: "sources"; value: Citation[]; route: string }
  | { type: "text"; value: string }
  | { type: "notice"; value: string }
  | { type: "model"; value: string }
  | { type: "error"; value: string; rateLimited: boolean }
  | { type: "done" };

/** Consumes the NDJSON stream from /api/ask, frame by frame. */
export async function ask(
  question: string,
  mode: StudyMode,
  history: Array<{ role: string; content: string }>,
  handlers: AskHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question, mode, history, apiKey: readApiKey() }),
    signal,
  });

  if (!response.body) {
    handlers.onError?.("No response from the server.", false);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const handle = (frame: Frame) => {
    switch (frame.type) {
      case "sources":
        handlers.onSources?.(frame.value, frame.route);
        break;
      case "text":
        handlers.onText?.(frame.value);
        break;
      case "notice":
        handlers.onNotice?.(frame.value);
        break;
      case "model":
        handlers.onModel?.(frame.value);
        break;
      case "error":
        handlers.onError?.(frame.value, frame.rateLimited);
        break;
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.trim()) handle(JSON.parse(line) as Frame);
    }
  }
  if (buffer.trim()) handle(JSON.parse(buffer) as Frame);
}
