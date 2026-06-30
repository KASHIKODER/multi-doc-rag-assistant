export const APP_CONFIG = {
  name: "DocuMind RAG",
  shortName: "DocuMind",
  description:
    "A source-grounded document intelligence workspace for routed, re-ranked, and graded multi-document RAG.",
  tagline: "Ask documents. Verify sources. Trust the answer.",
} as const;

export const APP_ROUTES = {
  landing: "/",
  login: "/login",
  dashboard: "/dashboard",
  documents: "/documents",
  ask: "/ask",
  history: "/history",
  settings: "/settings",
  developer: "/developer",
} as const;

export const NAV_ITEMS = [
  {
    label: "Dashboard",
    href: APP_ROUTES.dashboard,
    description: "Overview of documents, questions, and system activity.",
  },
  {
    label: "Documents",
    href: APP_ROUTES.documents,
    description: "Upload, inspect, and manage indexed course documents.",
  },
  {
    label: "Ask",
    href: APP_ROUTES.ask,
    description: "Ask questions and receive source-grounded answers.",
  },
  {
    label: "History",
    href: APP_ROUTES.history,
    description: "Review previous questions, answers, and citations.",
  },
  {
    label: "Settings",
    href: APP_ROUTES.settings,
    description: "Manage profile, retrieval settings, and preferences.",
  },
  {
    label: "Developer",
    href: APP_ROUTES.developer,
    description: "Inspect the RAG pipeline and system architecture.",
  },
] as const;

export const PIPELINE_STEPS = [
  {
    title: "Query Construction",
    description:
      "Transforms the user question into subject, module, and semantic query fields.",
  },
  {
    title: "Query Routing",
    description:
      "Routes implicit questions to the most likely document subject when needed.",
  },
  {
    title: "Candidate Retrieval",
    description:
      "Retrieves relevant chunks from the Chroma vector store using embeddings.",
  },
  {
    title: "Local Re-ranking",
    description:
      "Reorders retrieved chunks using query overlap, metadata, and topic signals.",
  },
  {
    title: "Relevance Grading",
    description:
      "Filters weak chunks before answer generation to improve grounding.",
  },
  {
    title: "Source-Grounded Answer",
    description:
      "Returns topic answers or claim-level cited answers with source metadata.",
  },
] as const;

export const DESIGN_TOKENS = {
  background: "#F8FAFC",
  text: "#0F172A",
  primary: "#2563EB",
  accent: "#10B981",
} as const;

export const DEMO_QUESTIONS = [
  "What are selectors?",
  "Explain the Bootstrap grid system.",
  "What table relationships are described in the SQL module?",
  "List the important topics in JavaScript.",
] as const;
