import type { AnswerMode } from "@/types/rag";

export const CHAT_HISTORY_STORAGE_KEY = "documind_chat_history_v1";

export type ChatHistoryItem = {
  id: string;
  question: string;
  summary: string;
  detectedSubject: string | null;
  answerMode: AnswerMode;
  semanticQuery: string;
  claimCount: number;
  sourceCount: number;
  createdAt: string;
};

export type ChatHistoryStats = {
  total: number;
  citationAnswers: number;
  topicAnswers: number;
  unsupportedAnswers: number;
};