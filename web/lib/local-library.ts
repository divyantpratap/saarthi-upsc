"use client";

/**
 * A visitor's own documents, held in their browser.
 *
 * Uploads never reach the server as files. They are parsed, chunked and stored
 * in IndexedDB on the reader's machine; at question time the top few matching
 * passages travel with the request as context and are cited as "Your upload".
 *
 * Matching here is lexical only. Embedding uploads would spend the same free
 * tier quota that the bundled index already competes for, and for a student's
 * own notes — where they tend to search for words the document actually uses —
 * BM25 is a fair trade for being instant and free.
 */
import { openDB, type DBSchema, type IDBPDatabase } from "idb";

import { bm25Search, buildBm25, tokenize } from "./tokenize";
import type { Mcq } from "./types";

export interface LocalDocument {
  id: string;
  name: string;
  addedAt: number;
  pages: number;
  chunks: number;
}

export interface LocalChunk {
  id: string;
  docId: string;
  docName: string;
  page?: number;
  text: string;
}

export interface LocalMockTest {
  id: string;
  title: string;
  subject: string;
  minutes: number;
  createdAt: number;
  questions: Mcq[];
}

interface SaarthiDB extends DBSchema {
  documents: { key: string; value: LocalDocument };
  chunks: { key: string; value: LocalChunk; indexes: { docId: string } };
  mockTests: { key: string; value: LocalMockTest };
}

const DB_NAME = "saarthi-library";
const DB_VERSION = 2;

let dbPromise: Promise<IDBPDatabase<SaarthiDB>> | null = null;

function db() {
  if (!dbPromise) {
    dbPromise = openDB<SaarthiDB>(DB_NAME, DB_VERSION, {
      upgrade(database, oldVersion) {
        if (oldVersion < 1) {
          database.createObjectStore("documents", { keyPath: "id" });
          const chunks = database.createObjectStore("chunks", { keyPath: "id" });
          chunks.createIndex("docId", "docId");
        }
        if (oldVersion < 2) {
          database.createObjectStore("mockTests", { keyPath: "id" });
        }
      },
    });
  }
  return dbPromise;
}

export async function addMockTest(
  input: Omit<LocalMockTest, "id" | "createdAt">,
): Promise<LocalMockTest> {
  const database = await db();
  const test: LocalMockTest = {
    ...input,
    id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: Date.now(),
  };
  await database.put("mockTests", test);
  return test;
}

export async function listMockTests(): Promise<LocalMockTest[]> {
  const database = await db();
  const tests = await database.getAll("mockTests");
  return tests.sort((a, b) => b.createdAt - a.createdAt);
}

export async function removeMockTest(id: string): Promise<void> {
  const database = await db();
  await database.delete("mockTests", id);
}

/** Invalidated on every write; rebuilt lazily on the next search. */
let searchCache: { chunks: LocalChunk[]; index: ReturnType<typeof buildBm25> } | null =
  null;

export async function addDocument(
  name: string,
  pages: number,
  pieces: Array<{ text: string; page?: number }>,
): Promise<LocalDocument> {
  const database = await db();
  const id = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  const document: LocalDocument = {
    id,
    name,
    addedAt: Date.now(),
    pages,
    chunks: pieces.length,
  };

  const tx = database.transaction(["documents", "chunks"], "readwrite");
  await tx.objectStore("documents").put(document);
  const store = tx.objectStore("chunks");
  await Promise.all(
    pieces.map((piece, i) =>
      store.put({
        id: `${id}-${i}`,
        docId: id,
        docName: name,
        page: piece.page,
        text: piece.text,
      }),
    ),
  );
  await tx.done;

  searchCache = null;
  return document;
}

export async function listDocuments(): Promise<LocalDocument[]> {
  const database = await db();
  const documents = await database.getAll("documents");
  return documents.sort((a, b) => b.addedAt - a.addedAt);
}

export async function removeDocument(id: string): Promise<void> {
  const database = await db();
  const tx = database.transaction(["documents", "chunks"], "readwrite");
  await tx.objectStore("documents").delete(id);
  const store = tx.objectStore("chunks");
  const keys = await store.index("docId").getAllKeys(id);
  await Promise.all(keys.map((key) => store.delete(key)));
  await tx.done;
  searchCache = null;
}

export interface LocalMatch {
  docName: string;
  page?: number;
  text: string;
  score: number;
}

/** Top passages from the reader's own documents for this question. */
export async function searchLocal(
  query: string,
  limit = 3,
): Promise<LocalMatch[]> {
  if (!query.trim()) return [];

  if (!searchCache) {
    const database = await db();
    const chunks = await database.getAll("chunks");
    if (!chunks.length) return [];
    searchCache = { chunks, index: buildBm25(chunks.map((c) => tokenize(c.text))) };
  }

  const { chunks, index } = searchCache;
  return bm25Search(index, query, limit)
    .filter(([, score]) => score > 0)
    .map(([docId, score]) => ({
      docName: chunks[docId].docName,
      page: chunks[docId].page,
      text: chunks[docId].text,
      score,
    }));
}

export async function isEmpty(): Promise<boolean> {
  const database = await db();
  return (await database.count("documents")) === 0;
}
