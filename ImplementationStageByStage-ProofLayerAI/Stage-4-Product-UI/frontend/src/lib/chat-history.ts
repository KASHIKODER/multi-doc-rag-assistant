import type { ChatHistoryItem, ChatHistoryStats } from "@/types/history";
import { CHAT_HISTORY_STORAGE_KEY } from "@/types/history";
import type { RagAnswer } from "@/types/rag";

const MAX_HISTORY_ITEMS = 50;

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function createHistoryId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `history_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function safeParseHistory(rawValue: string | null): ChatHistoryItem[] {
  if (!rawValue) {
    return [];
  }

  try {
    const parsed = JSON.parse(rawValue);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter((item) => {
      return (
        typeof item?.id === "string" &&
        typeof item?.question === "string" &&
        typeof item?.summary === "string" &&
        typeof item?.createdAt === "string"
      );
    });
  } catch {
    return [];
  }
}

export function getChatHistory(): ChatHistoryItem[] {
  if (!canUseStorage()) {
    return [];
  }

  const rawValue = window.localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
  return safeParseHistory(rawValue);
}

export function saveAnswerToHistory(answer: RagAnswer): ChatHistoryItem {
  const historyItem: ChatHistoryItem = {
    id: createHistoryId(),
    question: answer.question,
    summary: answer.summary,
    detectedSubject: answer.detectedSubject,
    answerMode: answer.answerMode,
    semanticQuery: answer.semanticQuery,
    claimCount: answer.claims.length,
    sourceCount: answer.sources.length,
    createdAt: new Date().toISOString(),
  };

  if (!canUseStorage()) {
    return historyItem;
  }

  const existingHistory = getChatHistory();

  const updatedHistory = [
    historyItem,
    ...existingHistory.filter((item) => item.question !== answer.question),
  ].slice(0, MAX_HISTORY_ITEMS);

  window.localStorage.setItem(
    CHAT_HISTORY_STORAGE_KEY,
    JSON.stringify(updatedHistory),
  );

  return historyItem;
}

export function clearChatHistory() {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.removeItem(CHAT_HISTORY_STORAGE_KEY);
}

export function getChatHistoryStats(history: ChatHistoryItem[]): ChatHistoryStats {
  return {
    total: history.length,
    citationAnswers: history.filter((item) => item.answerMode === "citation").length,
    topicAnswers: history.filter((item) => item.answerMode === "topic").length,
    unsupportedAnswers: history.filter((item) => item.answerMode === "unsupported")
      .length,
  };
}

export function formatHistoryDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }

  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}