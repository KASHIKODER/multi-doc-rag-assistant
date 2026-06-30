import type { Metadata } from "next";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { RagWorkspaceProvider } from "@/components/rag/RagWorkspaceProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMind RAG",
  description:
    "A source-grounded document intelligence workspace for routed, re-ranked, and graded multi-document RAG.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <RagWorkspaceProvider>{children}</RagWorkspaceProvider>
        </AuthProvider>
      </body>
    </html>
  );
}