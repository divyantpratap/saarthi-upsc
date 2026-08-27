/**
 * Original starter questions, ported from src/mock_tests/question_bank.py.
 *
 * These exist so a drill can always start. When Gemini is rate-limited or
 * returns malformed JSON, the student gets real questions with written
 * explanations instead of an error.
 */
import type { Mcq } from "./types";

export interface BankQuestion extends Mcq {
  id: string;
}

export const QUESTIONS: BankQuestion[] = [
  {
    id: "p1",
    subject: "Polity",
    question:
      "With reference to a Money Bill, consider the following statements:\n1. It can be introduced only in the Lok Sabha.\n2. The Rajya Sabha can reject it within fourteen days.\n3. The Speaker's certification is final.\n\nWhich of the statements given above is/are correct?",
    options: ["1 and 2 only", "1 and 3 only", "2 and 3 only", "1, 2 and 3"],
    answerIndex: 1,
    explanation:
      "A Money Bill is introduced only in the Lok Sabha. The Rajya Sabha may recommend changes but can neither reject nor amend it, so statement 2 is wrong. The Speaker's certification that a Bill is a Money Bill is final and not open to challenge.",
    sourceRef: "Constitution of India, Articles 109–110",
  },
  {
    id: "p2",
    subject: "Polity",
    question:
      "Which constitutional body recommends the distribution of net tax proceeds between the Union and the States?",
    options: ["NITI Aayog", "GST Council", "Finance Commission", "Inter-State Council"],
    answerIndex: 2,
    explanation:
      "Article 280 provides for the Finance Commission, whose core function includes recommending vertical devolution between the Union and States, and horizontal distribution among States.",
    sourceRef: "Constitution of India, Article 280",
  },
  {
    id: "p3",
    subject: "Polity",
    question: "The writ of quo warranto is issued primarily to:",
    options: [
      "Release a person from unlawful detention",
      "Command a public authority to perform its duty",
      "Prevent a lower court from exceeding jurisdiction",
      "Challenge unlawful occupation of a public office",
    ],
    answerIndex: 3,
    explanation:
      "Quo warranto asks by what authority a person holds a substantive public office, and prevents unlawful usurpation. Habeas corpus covers detention, mandamus commands duty, and prohibition restrains jurisdiction.",
    sourceRef: "Indian Polity — Constitutional Remedies",
  },
  {
    id: "e1",
    subject: "Economy",
    question:
      "An increase in the policy repo rate, other things remaining constant, is most likely to:",
    options: [
      "Reduce the cost of bank borrowing from the RBI",
      "Increase liquidity automatically",
      "Make credit costlier and moderate aggregate demand",
      "Directly increase government capital expenditure",
    ],
    answerIndex: 2,
    explanation:
      "A higher repo rate raises the marginal cost of funds for banks, tightening financial conditions and moderating credit growth and demand.",
    sourceRef: "RBI monetary policy framework",
  },
  {
    id: "e2",
    subject: "Economy",
    question:
      "Which one of the following is included in the current account of India's Balance of Payments?",
    options: [
      "Foreign direct investment inflows",
      "External commercial borrowing",
      "Export of software services",
      "Changes in foreign exchange reserves",
    ],
    answerIndex: 2,
    explanation:
      "Trade in goods and services, primary income and transfers form the current account. FDI and external borrowing are financial-account items, as are reserve changes.",
    sourceRef: "Balance of Payments accounting",
  },
  {
    id: "e3",
    subject: "Economy",
    question: "Stagflation refers to the simultaneous occurrence of:",
    options: [
      "High growth and low inflation",
      "High inflation and stagnant output",
      "Deflation and full employment",
      "Currency appreciation and fiscal surplus",
    ],
    answerIndex: 1,
    explanation:
      "Stagflation combines persistent inflation with weak or stagnant activity, usually alongside elevated unemployment — a combination that standard demand management handles poorly.",
    sourceRef: "Macroeconomics — Inflation",
  },
  {
    id: "g1",
    subject: "Geography",
    question:
      "Western Disturbances that affect northwestern India generally originate near the:",
    options: [
      "South China Sea",
      "Mediterranean region",
      "Arabian Sea equator",
      "Bay of Bengal",
    ],
    answerIndex: 1,
    explanation:
      "Western Disturbances are extratropical systems originating around the Mediterranean–West Asian region, travelling eastward with the subtropical westerly jet.",
    sourceRef: "Indian climatology",
  },
  {
    id: "h1",
    subject: "History",
    question: "The Permanent Settlement of 1793 was introduced primarily in:",
    options: [
      "Bombay and Sind",
      "Bengal, Bihar and Orissa",
      "Madras Presidency",
      "Punjab and Awadh",
    ],
    answerIndex: 1,
    explanation:
      "Cornwallis introduced the Permanent Settlement in Bengal, Bihar and Orissa, recognising zamindars as proprietors subject to a fixed revenue demand in perpetuity.",
    sourceRef: "Modern Indian History — Land revenue systems",
  },
  {
    id: "env1",
    subject: "Environment",
    question:
      "The Ramsar Convention is specifically concerned with the conservation and wise use of:",
    options: [
      "Tropical forests",
      "Wetlands",
      "Migratory birds only",
      "World heritage monuments",
    ],
    answerIndex: 1,
    explanation:
      "The Ramsar Convention of 1971 provides the framework for national action and international cooperation on the conservation and wise use of wetlands.",
    sourceRef: "Ramsar Convention, 1971",
  },
  {
    id: "s1",
    subject: "Science & Tech",
    question: "CRISPR-Cas9 technology is best described as a tool for:",
    options: [
      "Carbon capture",
      "Targeted genome editing",
      "Quantum encryption",
      "Remote sensing",
    ],
    answerIndex: 1,
    explanation:
      "CRISPR-Cas systems can be programmed with a guide RNA to locate and cut a particular DNA sequence, enabling targeted genome editing.",
    sourceRef: "Biotechnology — genome editing",
  },
];

export const SUBJECTS = [...new Set(QUESTIONS.map((q) => q.subject))];

/** Fallback selection: prefer the requested subject, then top up from the rest. */
export function fallbackQuestions(topic: string, count: number): Mcq[] {
  const needle = topic.toLowerCase();
  const matching = QUESTIONS.filter(
    (question) =>
      question.subject.toLowerCase().includes(needle) ||
      needle.includes(question.subject.toLowerCase()) ||
      question.question.toLowerCase().includes(needle),
  );
  const rest = QUESTIONS.filter((question) => !matching.includes(question));
  return [...matching, ...rest].slice(0, count);
}
