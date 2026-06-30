import type {
  DocumentsResponse,
  RebuildIndexResponse,
  UploadDocumentsResponse,
} from "@/types/document";
import type { RagAnswer } from "@/types/rag";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type AskDocumentsPayload = {
  question: string;
};

async function parseErrorMessage(response: Response, fallback: string) {
  try {
    const errorBody = await response.json();

    if (typeof errorBody.detail === "string") {
      return errorBody.detail;
    }

    if (errorBody.detail?.message) {
      return errorBody.detail.message;
    }

    return fallback;
  } catch {
    return fallback;
  }
}

export async function askDocuments(question: string): Promise<RagAnswer> {
  const payload: AskDocumentsPayload = {
    question,
  };

  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await parseErrorMessage(
      response,
      "Failed to get an answer from the RAG backend.",
    );

    throw new Error(message);
  }

  return response.json();
}

export async function getDocuments(): Promise<DocumentsResponse> {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: "GET",
  });

  if (!response.ok) {
    const message = await parseErrorMessage(
      response,
      "Failed to load documents from the backend.",
    );

    throw new Error(message);
  }

  return response.json();
}

export async function uploadDocuments(
  files: FileList | File[],
): Promise<UploadDocumentsResponse> {
  const formData = new FormData();

  Array.from(files).forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const message = await parseErrorMessage(
      response,
      "Failed to upload documents.",
    );

    throw new Error(message);
  }

  return response.json();
}

export async function rebuildDocumentsIndex(): Promise<RebuildIndexResponse> {
  const response = await fetch(`${API_BASE_URL}/documents/rebuild`, {
    method: "POST",
  });

  if (!response.ok) {
    const message = await parseErrorMessage(
      response,
      "Failed to rebuild the document index.",
    );

    throw new Error(message);
  }

  return response.json();
}
