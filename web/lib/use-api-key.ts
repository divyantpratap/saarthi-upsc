"use client";

import { useCallback, useSyncExternalStore } from "react";

const STORAGE_KEY = "saarthi.byok";

/*
 * sessionStorage is external state, so it is read through a store rather than
 * copied into React state inside an effect. That keeps server and client render
 * consistent and lets every mounted consumer update together when the key
 * changes.
 */
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    // Private browsing or blocked storage: BYOK just stays off.
    return "";
  }
}

/** Nothing is stored during SSR, and the client reconciles on hydration. */
function getServerSnapshot(): string {
  return "";
}

function write(value: string): void {
  try {
    if (value) sessionStorage.setItem(STORAGE_KEY, value);
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* non-fatal */
  }
  emit();
}

/**
 * A visitor's own Gemini key, held for this tab only.
 *
 * sessionStorage rather than localStorage on purpose: the key should not
 * outlive the tab. It is sent with each request and never persisted
 * server-side, matching the contract the Streamlit build made.
 */
export function useApiKey() {
  const apiKey = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const setApiKey = useCallback((value: string) => write(value), []);
  const clearApiKey = useCallback(() => write(""), []);
  return { apiKey, setApiKey, clearApiKey };
}

/** Read once, imperatively, for request payloads. */
export function readApiKey(): string | undefined {
  return getSnapshot() || undefined;
}
