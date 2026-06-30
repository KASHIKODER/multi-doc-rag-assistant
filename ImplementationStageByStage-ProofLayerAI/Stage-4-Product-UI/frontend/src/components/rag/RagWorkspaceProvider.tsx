"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { askDocuments } from "@/lib/api";
import { saveAnswerToHistory } from "@/lib/chat-history";
import { DEMO_QUESTIONS } from "@/lib/constants";
import type { RagAnswer } from "@/types/rag";

const ASK_SESSION_STORAGE_KEY = "documind_current_ask_session_v1";

type PersistedAskSession = {
  question: string;
  answer: RagAnswer | null;
  updatedAt: string;
};

type RagWorkspaceContextValue = {
  question: string;
  answer: RagAnswer | null;
  loading: boolean;
  error: string;
  historyMessage: string;
  updateQuestion: (value: string) => void;
  runQuestion: () => Promise<void>;
  clearCurrentAnswer: () => void;
};

const RagWorkspaceContext = createContext<RagWorkspaceContextValue | null>(null);

function readPersistedSession(): PersistedAskSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(ASK_SESSION_STORAGE_KEY);

    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw);

    if (typeof parsed?.question !== "string") {
      return null;
    }

    return {
      question: parsed.question,
      answer: parsed.answer ?? null,
      updatedAt: parsed.updatedAt ?? new Date().toISOString(),
    };
  } catch {
    return null;
  }
}

function persistSession(question: string, answer: RagAnswer | null) {
  if (typeof window === "undefined") {
    return;
  }

  const payload: PersistedAskSession = {
    question,
    answer,
    updatedAt: new Date().toISOString(),
  };

  window.localStorage.setItem(
    ASK_SESSION_STORAGE_KEY,
    JSON.stringify(payload),
  );
}

type RagWorkspaceProviderProps = {
  children: ReactNode;
};

export function RagWorkspaceProvider({ children }: RagWorkspaceProviderProps) {
  const [question, setQuestion] = useState<string>(DEMO_QUESTIONS[0]);
  const [answer, setAnswer] = useState<RagAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyMessage, setHistoryMessage] = useState("");

  useEffect(() => {
    const persisted = readPersistedSession();

    if (!persisted) {
      return;
    }

    setQuestion(persisted.question);
    setAnswer(persisted.answer);
  }, []);

  function updateQuestion(value: string) {
    setQuestion(value);
    setError("");
    setHistoryMessage("");
    setAnswer(null);
    persistSession(value, null);
  }

  function clearCurrentAnswer() {
    setAnswer(null);
    setHistoryMessage("");
    persistSession(question, null);
  }

  async function runQuestion() {
    const cleanQuestion = question.trim();

    if (!cleanQuestion || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setHistoryMessage("");
    setAnswer(null);
    persistSession(cleanQuestion, null);

    try {
      const result = await askDocuments(cleanQuestion);

      setAnswer(result);
      persistSession(cleanQuestion, result);

      const savedItem = saveAnswerToHistory(result);

      setHistoryMessage(
        `Saved to history at ${new Date(savedItem.createdAt).toLocaleTimeString(
          "en-IN",
          {
            hour: "2-digit",
            minute: "2-digit",
          },
        )}.`,
      );
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while calling the RAG backend.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const value = useMemo(
    () => ({
      question,
      answer,
      loading,
      error,
      historyMessage,
      updateQuestion,
      runQuestion,
      clearCurrentAnswer,
    }),
    [question, answer, loading, error, historyMessage],
  );

  return (
    <RagWorkspaceContext.Provider value={value}>
      {children}
    </RagWorkspaceContext.Provider>
  );
}

export function useRagWorkspace() {
  const context = useContext(RagWorkspaceContext);

  if (!context) {
    throw new Error("useRagWorkspace must be used inside RagWorkspaceProvider.");
  }

  return context;
}