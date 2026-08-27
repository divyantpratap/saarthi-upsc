/**
 * Question routing, ported verbatim from src/rag/router.py.
 *
 * Heuristic on purpose: classifying with a model call would add latency and
 * quota cost to every question for a decision these patterns already make well.
 */

const DEEP = new RegExp(
  "\\b(compare|contrast|analyze|analysis|discuss|evaluate|critically|" +
    "relationship between|difference between|similarit|implications|" +
    "multi|comprehensive|in detail|elaborate|mains answer|essay)\\b",
  "i",
);

const DIRECT = new RegExp(
  "\\b(what is|who is|when was|define|article \\d+|list the|name the|" +
    "which article|full form|meaning of|how many|term of|capital of)\\b",
  "i",
);

export type Route = "direct" | "rag" | "hybrid";

export function routeQuestion(question: string, hasIndex: boolean): Route {
  const q = question.trim();
  if (!hasIndex) return "direct";
  if (DEEP.test(q)) return "rag";
  if (DIRECT.test(q) && q.split(/\s+/).length < 25) return "direct";
  if (q.split(/\s+/).length > 35) return "rag";
  return "hybrid";
}
