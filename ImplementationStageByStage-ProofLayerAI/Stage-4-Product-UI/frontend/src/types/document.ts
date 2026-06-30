export type DocumentStatus = "Indexed" | "Not indexed" | "Missing metadata";

export type DocumentItem = {
  id: string;
  fileName: string;
  subject: string | null;
  module: string | number | null;
  title: string | null;
  pages: number;
  chunks: number | null;
  status: DocumentStatus;
  metadataAvailable: boolean;
};

export type DocumentsResponse = {
  total: number;
  documents: DocumentItem[];
};

export type UploadDocumentsResponse = {
  uploaded: number;
  files: string[];
  message: string;
};

export type RebuildIndexResponse = {
  success: boolean;
  message: string;
  stdoutPreview: string;
  stderrPreview: string;
};
