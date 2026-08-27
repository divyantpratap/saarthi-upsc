import { describe, expect, test } from "vitest";

import indexMeta from "../public/index/meta.json";
import { resetRetrievalCaches, retrieve } from "./retrieve";

const MIN_OPEN_CORPUS_CHUNKS = 9_000;

interface GoldenQuery {
  name: string;
  query: string;
  expectedFile: string;
}

/**
 * Stable, answerable questions spread across the bundled open corpus.
 *
 * File basenames are deliberate: the NCERT download folders are presentation
 * metadata and may be renamed, while the chapter codes are stable source IDs.
 * Retrieval is lexical-only here, so this gate is deterministic and never
 * spends embedding quota.
 */
const GOLDEN_QUERIES: GoldenQuery[] = [
  {
    name: "Money Bills",
    query:
      "What is a Money Bill under Article 110 and what provisions may it contain?",
    expectedFile: "Constitution_of_India.pdf",
  },
  {
    name: "constitutional remedies",
    query:
      "What remedies for enforcement of Fundamental Rights are provided by Article 32?",
    expectedFile: "Constitution_of_India.pdf",
  },
  {
    name: "Harappan city planning",
    query:
      "What features of drainage and town planning distinguished Harappan cities?",
    expectedFile: "lehs101.pdf",
  },
  {
    name: "Mughal agrarian society",
    query: "How did zamindars exercise power in Mughal agrarian society?",
    expectedFile: "lehs204.pdf",
  },
  {
    name: "Great Depression in India",
    query:
      "What were the effects of the Great Depression on Indian peasants and agricultural prices?",
    expectedFile: "jess303.pdf",
  },
  {
    name: "demographic transition",
    query: "Explain the demographic transition theory and its three stages.",
    expectedFile: "legy102.pdf",
  },
  {
    name: "balance of payments",
    query:
      "What is the difference between the current account and capital account in balance of payments?",
    expectedFile: "leec106.pdf",
  },
  {
    name: "Green Revolution",
    query:
      "How did the Green Revolution affect regional inequalities and rural credit in India?",
    expectedFile: "keec105.pdf",
  },
  {
    name: "Cuban Missile Crisis",
    query:
      "What was the Cuban Missile Crisis and how did it shape the Cold War?",
    expectedFile: "leps101.pdf",
  },
  {
    name: "caste mobility",
    query:
      "What do Sanskritisation and the dominant caste explain about caste mobility in India?",
    expectedFile: "lesy202.pdf",
  },
];

const hasOpenCorpus = indexMeta.openCount >= MIN_OPEN_CORPUS_CHUNKS;

if (process.env.SAARTHI_REQUIRE_OPEN_INDEX === "1" && !hasOpenCorpus) {
  throw new Error(
    `Golden retrieval needs the Tier A index (at least ${MIN_OPEN_CORPUS_CHUNKS.toLocaleString()} open chunks); ` +
      `the committed dev index has ${indexMeta.openCount.toLocaleString()}. Rebuild it before running test:retrieval.`,
  );
}

describe.skipIf(!hasOpenCorpus)("golden retrieval", () => {
  resetRetrievalCaches();

  test.each(GOLDEN_QUERIES)(
    "$name returns the expected source in the top three",
    async ({ query, expectedFile }) => {
      const hits = await retrieve(query, { topK: 3 });
      const files = hits.map((hit) => hit.chunk.file);

      expect(
        files.some((file) => file.endsWith(expectedFile)),
        `Expected ${expectedFile} in the top three for ${JSON.stringify(query)}; got ${files.join(", ")}`,
      ).toBe(true);
    },
  );
});
