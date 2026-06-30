export type AnswerMode = "topic" | "citation" | "unsupported";

export type ClaimConfidence = "high" | "medium" | "low";

export type RetrievalStats = {
  candidates: number;
  reranked: number;
  keptAfterGrading: number;
};

export type VerifiedClaim = {
  id: string;
  claim: string;
  source: string;
  page: number | string;
  confidence: ClaimConfidence;
  subject?: string;
  module?: string | number;
  title?: string;
};

export type RetrievedSource = {
  id: string;
  fileName: string;
  title?: string;
  page: number | string;
  subject?: string;
  module?: string | number;
  preview: string;
};

export type RagAnswer = {
  question: string;
  detectedSubject: string | null;
  detectedModule: string | null;
  semanticQuery: string;
  answerMode: AnswerMode;
  retrievalStats: RetrievalStats;
  summary: string;
  claims: VerifiedClaim[];
  sources: RetrievedSource[];
};

export const mockRagAnswer: RagAnswer = {
  question: "What are selectors?",
  detectedSubject: "CSS3",
  detectedModule: null,
  semanticQuery: "selectors explanation",
  answerMode: "citation",
  retrievalStats: {
    candidates: 5,
    reranked: 5,
    keptAfterGrading: 2,
  },
  summary:
    "The retrieved CSS3 module explains that selectors are used to target and style HTML elements. The module includes several selector types, including universal, element, class, ID, and grouping selectors.",
  claims: [
    {
      id: "claim_001",
      claim:
        "Selectors are used to target and style HTML elements based on selector types.",
      source: "Module 1-CSS3.pdf",
      page: 1,
      confidence: "high",
      subject: "CSS3",
      module: 1,
      title: "CSS3 Exercises",
    },
    {
      id: "claim_002",
      claim:
        "The CSS3 module covers universal, element, class, and ID selectors.",
      source: "Module 1-CSS3.pdf",
      page: 1,
      confidence: "high",
      subject: "CSS3",
      module: 1,
      title: "CSS3 Exercises",
    },
  ],
  sources: [
    {
      id: "source_001",
      fileName: "Module 1-CSS3.pdf",
      title: "CSS3 Exercises",
      page: 1,
      subject: "CSS3",
      module: 1,
      preview:
        "Selectors Playground introduces universal selectors, element selectors, ID selectors, class selectors, and grouping selectors.",
    },
    {
      id: "source_002",
      fileName: "Module 1-CSS3.pdf",
      title: "CSS3 Exercises",
      page: 2,
      subject: "CSS3",
      module: 1,
      preview:
        "The module continues with styling scenarios, typography, link styling, box model, and responsive media queries.",
    },
  ],
};
