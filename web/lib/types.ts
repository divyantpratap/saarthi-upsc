/** Shapes shared by the index artifacts, the retrieval layer and the UI. */

/** A chunk that ships with its prose — freely redistributable material. */
export interface OpenChunk {
  i: number;
  src: string;
  file: string;
  subj: string;
  page?: number | null;
  para?: number | null;
  text: string;
}

/**
 * A chunk from a commercial title. It ships with a keyword signature so it stays
 * findable, and with enough citation detail to point a student at the page — but
 * never with the page's prose.
 */
export interface RestrictedChunk {
  i: number;
  src: string;
  file: string;
  subj: string;
  page?: number | null;
  para?: number | null;
  terms: string[];
  chars: number;
}

export type Chunk = OpenChunk | RestrictedChunk;

export function hasText(chunk: Chunk): chunk is OpenChunk {
  return "text" in chunk;
}

export interface SourceRecord {
  file: string;
  subject: string;
  tier: "A" | "B";
  chunks: number;
}

export interface IndexMeta {
  version: number;
  fingerprint: string;
  embedModel: string;
  dims: number;
  count: number;
  openCount: number;
  restrictedCount: number;
  builtAt: string;
  sources: Record<string, SourceRecord>;
}

/** One retrieved passage, ready to cite. */
export interface Retrieved {
  chunk: Chunk;
  score: number;
  /** Present only when the chunk's text may be shown and sent to the model. */
  text?: string;
  /** True when the match is real but the passage cannot be reproduced. */
  citationOnly: boolean;
}

export type StudyMode = "Learn" | "Prelims" | "Mains" | "Evaluate";

export interface Mcq {
  question: string;
  options: string[];
  answerIndex: number;
  explanation: string;
  sourceRef: string;
  subject: string;
}
