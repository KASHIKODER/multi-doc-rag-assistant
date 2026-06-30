"use client";

import type { ChangeEvent } from "react";
import { useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { APP_ROUTES } from "@/lib/constants";
import {
  getDocuments,
  rebuildDocumentsIndex,
  uploadDocuments,
} from "@/lib/api";
import type { DocumentItem } from "@/types/document";

function statusVariant(status: DocumentItem["status"]) {
  if (status === "Indexed") return "success";
  if (status === "Missing metadata") return "muted";
  return "outline";
}

export default function DocumentsPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const response = await getDocuments();
      setDocuments(response.documents);
      setTotal(response.total);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while loading documents.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = event.target.files;

    if (!selectedFiles || selectedFiles.length === 0) {
      return;
    }

    setUploading(true);
    setError("");
    setStatusMessage("");

    try {
      const result = await uploadDocuments(selectedFiles);
      setStatusMessage(result.message);
      await loadDocuments();
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while uploading documents.";

      setError(message);
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handleRebuildIndex() {
    setRebuilding(true);
    setError("");
    setStatusMessage(
      "Rebuilding the document index. This can take some time for local embeddings.",
    );

    try {
      const result = await rebuildDocumentsIndex();
      setStatusMessage(result.message);
      await loadDocuments();
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while rebuilding the index.";

      setError(message);
      setStatusMessage("");
    } finally {
      setRebuilding(false);
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  const busy = loading || uploading || rebuilding;

  return (
    <AppShell activePath={APP_ROUTES.documents} title="Documents">
      <PageHeader
        title="Documents"
        description="Manage the course PDFs available to the RAG workspace. This page reads real document data from the FastAPI backend."
        action={
          <Button onClick={loadDocuments} disabled={busy}>
            {loading ? "Refreshing..." : "Refresh Documents"}
          </Button>
        }
      />

      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        className="hidden"
        onChange={handleFileChange}
      />

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Total documents</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {total}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            PDFs discovered from the Stage-2 RAG data folder.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Indexed</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {documents.filter((doc) => doc.status === "Indexed").length}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Documents currently available for retrieval.
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Metadata ready</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight text-[#0F172A]">
            {documents.filter((doc) => doc.metadataAvailable).length}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Documents with extracted metadata available.
          </p>
        </div>
      </section>

      <section className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white p-8 shadow-sm">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold text-[#2563EB]">
            Upload workspace
          </p>

          <h2 className="mt-2 text-2xl font-semibold text-[#0F172A]">
            Upload course PDFs and rebuild the searchable index.
          </h2>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            Selected PDFs are saved into the Stage-2 data folder. After upload,
            rebuild the index so the new documents become searchable by the RAG
            pipeline.
          </p>

          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploading ? "Uploading..." : "Select PDFs"}
            </Button>

            <Button
              variant="secondary"
              disabled={busy || documents.length === 0}
              onClick={handleRebuildIndex}
            >
              {rebuilding ? "Rebuilding..." : "Rebuild Index"}
            </Button>
          </div>

          {statusMessage ? (
            <div className="mt-5 rounded-2xl bg-[#10B981]/10 p-4 text-left">
              <p className="text-sm font-semibold text-[#0F172A]">Status</p>
              <p className="mt-1 text-sm leading-6 text-slate-700">
                {statusMessage}
              </p>
            </div>
          ) : null}
        </div>
      </section>

      {error ? (
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-[#2563EB]">
            Documents API error
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-700">{error}</p>

          <p className="mt-3 text-xs leading-5 text-slate-500">
            Make sure the FastAPI backend is running on http://127.0.0.1:8000.
          </p>
        </section>
      ) : null}

      <section className="mt-6 rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-5">
          <p className="text-sm font-semibold text-[#2563EB]">
            Indexed documents
          </p>

          <h2 className="mt-1 text-xl font-semibold text-[#0F172A]">
            Current local knowledge base
          </h2>
        </div>

        {loading ? (
          <div className="px-6 py-8">
            <p className="text-sm leading-6 text-slate-600">
              Loading documents from the backend...
            </p>
          </div>
        ) : documents.length > 0 ? (
          <div className="divide-y divide-slate-200">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="grid gap-4 px-6 py-5 md:grid-cols-[1.5fr_0.8fr_0.5fr_0.5fr_0.5fr_0.7fr]"
              >
                <div>
                  <p className="text-sm font-semibold text-[#0F172A]">
                    {doc.fileName}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {doc.title ?? "Untitled document"}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-500">Subject</p>
                  <p className="mt-1 text-sm font-semibold">
                    {doc.subject ?? "Unknown"}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-500">Module</p>
                  <p className="mt-1 text-sm font-semibold">
                    {doc.module ?? "—"}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-500">Pages</p>
                  <p className="mt-1 text-sm font-semibold">{doc.pages}</p>
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-500">Chunks</p>
                  <p className="mt-1 text-sm font-semibold">
                    {doc.chunks ?? "—"}
                  </p>
                </div>

                <div>
                  <Badge variant={statusVariant(doc.status)}>
                    {doc.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-8">
            <p className="text-sm leading-6 text-slate-600">
              No documents were found in the Stage-2 data folder.
            </p>
          </div>
        )}
      </section>
    </AppShell>
  );
}
