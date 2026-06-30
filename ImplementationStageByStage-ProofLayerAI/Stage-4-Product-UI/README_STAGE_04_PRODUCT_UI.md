# Stage 04 — Product UI + FastAPI RAG API

## DocuMind RAG — Source-Grounded Document Intelligence Workspace

This stage converts the earlier Python-based multi-document RAG engine into a professional full-stack product experience.

The project started as a terminal-based RAG system that could ingest course PDFs, retrieve relevant context, generate answers, and cite document sources. In Stage 04, that backend was wrapped with FastAPI and connected to a clean Next.js product UI with GitHub authentication, protected routes, document management, real RAG asking, upload/rebuild support, and local browser history.

---

## 1. What This Stage Adds

Stage 04 turns the RAG backend into a usable product.

### Completed in this stage

* Next.js + TypeScript frontend
* Tailwind-based clean UI system
* FastAPI backend wrapper
* Real `/ask` API connected to the existing Stage-2 RAG engine
* Real `/documents` API connected to the Stage-2 data folder
* PDF upload support
* Chroma index rebuild support
* GitHub authentication using Auth.js / NextAuth
* Protected dashboard routes
* GitHub user avatar/name in topbar
* Logout support
* Ask page connected to real RAG responses
* Documents page connected to real backend data
* Local browser-based chat history
* Professional dashboard-style workspace

---

## 2. Development Model Followed

This project was built using an incremental Agile-style approach.

Instead of trying to build the full product at once, each milestone was completed and tested independently.

### Development approach

1. Build a working backend first.
2. Add a minimal product UI.
3. Connect frontend to backend through a stable API contract.
4. Add authentication.
5. Protect important routes.
6. Add document management.
7. Add history.
8. Document and polish the product.

This helped keep the project stable while adding multiple layers.

---

## 3. High-Level Architecture

```text
Next.js Product UI
        |
        | HTTP requests
        v
FastAPI Backend Wrapper
        |
        | Python function bridge
        v
Existing Stage-2 RAG Engine
        |
        | Retrieval + Generation
        v
Chroma DB + Course PDFs + Metadata
```

---

## 4. Folder Structure

```text
ImplementationStageByStage-ProofLayerAI/
│
├── Stage-2-QueryRouting+Re-Ranking+RelevanceGrading/
│   ├── Kashi-Mate-RAG-Stage-2.py
│   ├── data/
│   │   ├── Module 1-Bootstrap5.pdf
│   │   ├── Module 1-CSS3.pdf
│   │   ├── Module 1-HTML 5.pdf
│   │   ├── Module 1-JavaScript.pdf
│   │   ├── Module 2-ANSI SQL Using MySQL.pdf
│   │   └── extracted_metadata/
│   └── chroma_db/
│
└── Stage-4-Product-UI/
    │
    ├── backend/
    │   ├── main.py
    │   ├── rag_bridge.py
    │   ├── document_service.py
    │   ├── schemas.py
    │   └── requirements-api.txt
    │
    └── frontend/
        ├── auth.ts
        ├── middleware.ts
        ├── next.config.ts
        ├── .env.local
        ├── src/
        │   ├── app/
        │   │   ├── page.tsx
        │   │   ├── login/
        │   │   ├── dashboard/
        │   │   ├── documents/
        │   │   ├── ask/
        │   │   ├── history/
        │   │   ├── settings/
        │   │   ├── developer/
        │   │   └── api/auth/[...nextauth]/
        │   │
        │   ├── components/
        │   │   ├── auth/
        │   │   ├── chat/
        │   │   ├── layout/
        │   │   └── ui/
        │   │
        │   ├── lib/
        │   │   ├── api.ts
        │   │   ├── chat-history.ts
        │   │   └── constants.ts
        │   │
        │   └── types/
        │       ├── rag.ts
        │       ├── document.ts
        │       └── history.ts
```

---

## 5. Backend Features

The FastAPI backend is a wrapper around the already-working Stage-2 RAG engine.

### Backend files

```text
backend/main.py
backend/rag_bridge.py
backend/document_service.py
backend/schemas.py
backend/requirements-api.txt
```

### Backend endpoints

```text
GET  /health
GET  /documents
POST /documents/upload
POST /documents/rebuild
POST /ask
```

---

## 6. RAG Bridge Logic

The file `rag_bridge.py` connects FastAPI to the existing Stage-2 RAG engine.

It does not rewrite the RAG logic. It imports and reuses the existing Stage-2 functions.

### Main responsibilities

* Load the Stage-2 RAG module
* Load the existing Chroma vector store
* Parse the user query
* Apply query routing
* Retrieve, re-rank, and grade documents
* Generate topic or citation-backed answers
* Convert backend objects into frontend-friendly JSON

### Response shape

```json
{
  "question": "What are selectors?",
  "detectedSubject": "CSS3",
  "detectedModule": null,
  "semanticQuery": "are selectors",
  "answerMode": "citation",
  "retrievalStats": {
    "candidates": 4,
    "reranked": 4,
    "keptAfterGrading": 4
  },
  "summary": "...",
  "claims": [],
  "sources": []
}
```

---

## 7. Frontend Features

The frontend is built with:

* Next.js
* TypeScript
* Tailwind CSS
* Auth.js / NextAuth
* Clean component-based architecture

### Main pages

```text
/
 /login
 /dashboard
 /documents
 /ask
 /history
 /settings
 /developer
```

### Layout components

```text
AppShell
Sidebar
Topbar
PageHeader
```

### UI components

```text
Button
Card
Badge
```

### Auth components

```text
AuthProvider
GitHubLoginButton
UserMenu
```

### Chat components

```text
QuestionInput
AnswerCard
ClaimCard
SourceCard
PipelineStats
```

---

## 8. UI Design System

The UI follows a clean 4-color product design.

```text
Background: #F8FAFC
Text:       #0F172A
Primary:    #2563EB
Accent:     #10B981
```

Design goals:

* Minimal
* Professional
* Workspace-like
* Not visually noisy
* Technical details hidden inside expandable sections
* Sources and citations clearly visible

---

## 9. Ask Page Flow

The Ask page is the main product workflow.

### Flow

```text
User enters question
        |
        v
QuestionInput
        |
        v
POST /ask
        |
        v
FastAPI rag_bridge
        |
        v
Stage-2 RAG Engine
        |
        v
AnswerCard + ClaimCard + SourceCard
```

### Ask page displays

* Detected subject
* Detected module
* Semantic query
* Answer mode
* Pipeline stats
* Summary
* Verified claims or topic concepts
* Retrieved sources
* Source previews

---

## 10. Documents Page Flow

The Documents page is connected to the backend.

### Flow

```text
Documents Page
        |
        v
GET /documents
        |
        v
FastAPI document_service
        |
        v
Stage-2 data folder scan
```

### Documents page displays

* Total documents
* Indexed documents
* Metadata-ready documents
* PDF filename
* Subject
* Module
* Page count
* Index status

### Upload and rebuild

The page also supports:

```text
POST /documents/upload
POST /documents/rebuild
```

This allows the user to upload PDFs and rebuild the local Chroma index.

---

## 11. GitHub Authentication

GitHub authentication is implemented using Auth.js / NextAuth.

### Auth files

```text
frontend/auth.ts
frontend/src/app/api/auth/[...nextauth]/route.ts
frontend/src/components/auth/AuthProvider.tsx
frontend/src/components/auth/GitHubLoginButton.tsx
frontend/src/components/auth/UserMenu.tsx
frontend/middleware.ts
```

### Auth features

* GitHub OAuth login
* Session provider
* GitHub avatar and user name in topbar
* Logout
* Protected routes
* Callback URL support after login
* `/login` redirects logged-in users to dashboard

### Protected routes

```text
/dashboard
/documents
/ask
/history
/settings
/developer
```

Public routes:

```text
/
 /login
/api/auth/*
```

---

## 12. Local History

The History page is connected to local browser storage.

When a user asks a question and receives an answer, the answer metadata is saved into `localStorage`.

### Saved history fields

```text
question
summary
detectedSubject
answerMode
semanticQuery
claimCount
sourceCount
createdAt
```

### History page displays

* Total saved questions
* Citation answer count
* Topic answer count
* Unsupported answer count
* Saved question list
* Summary
* Subject badge
* Answer mode badge
* Claim/topic count
* Source count

This is an MVP-friendly solution. Later, it can be moved to PostgreSQL.

---

## 13. Environment Variables

Create this file:

```text
frontend/.env.local
```

Required values:

```env
AUTH_SECRET=your_generated_secret
AUTH_URL=http://localhost:3000

AUTH_GITHUB_ID=your_github_client_id
AUTH_GITHUB_SECRET=your_github_client_secret

NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Do not commit `.env.local`.

---

## 14. How to Run

### Terminal 1 — FastAPI backend

From:

```text
ImplementationStageByStage-ProofLayerAI/Stage-4-Product-UI
```

Run:

```powershell
..\..\..\venv\Scripts\Activate.ps1

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

API docs:

```text
http://127.0.0.1:8000/docs
```

---

### Terminal 2 — Next.js frontend

From:

```text
ImplementationStageByStage-ProofLayerAI/Stage-4-Product-UI/frontend
```

Run:

```powershell
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

---

## 15. Recommended Test Questions

Use these questions from the Ask page.

### Citation-backed questions

```text
What are selectors?
```

Expected:

```text
Detected subject: CSS3
Answer mode: Citation-backed
Sources: Module 1-CSS3.pdf
```

```text
Explain the Bootstrap grid system.
```

Expected:

```text
Detected subject: Bootstrap5
Answer mode: Citation-backed
Sources: Module 1-Bootstrap5.pdf
```

```text
What table relationships are described in the SQL module?
```

Expected:

```text
Detected subject: SQL
Answer mode: Citation-backed
Sources: Module 2-ANSI SQL Using MySQL.pdf
```

### Topic answer question

```text
List the important topics in JavaScript.
```

Expected:

```text
Detected subject: JavaScript
Answer mode: Topic answer
Multiple topics found
Source: Module 1-JavaScript.pdf
```

---

## 16. Why This Is More Than a Basic PDF Chatbot

This project includes multiple production-style RAG concepts:

* Query construction
* Query routing
* Metadata-aware retrieval
* Local re-ranking
* Relevance grading
* Topic answer mode
* Claim-level citation
* Source-safe output
* Human-readable page numbers
* API contract between backend and frontend
* Authenticated product workspace
* Document management
* Local chat history

A basic PDF chatbot usually retrieves chunks and sends them to an LLM. This project adds routing, grading, structured answer modes, and source-level UI presentation.

---

## 17. Known Limitations

This is a local MVP, not a deployed SaaS product yet.

Current limitations:

* History uses localStorage, not a database.
* Uploaded generic PDFs may not always have rich metadata.
* Local LLM responses can be slow.
* Chroma rebuild can take time.
* User-specific document separation is not implemented yet.
* No PostgreSQL persistence yet.
* No cloud storage yet.
* No production deployment yet.
* Google login was intentionally skipped for this version.

---

## 18. Future Roadmap

### Short-term improvements

* Add root project README
* Add screenshots
* Improve source preview cleanup
* Add document delete support
* Add clearer upload metadata fallback
* Add better loading states for long rebuilds

### Medium-term improvements

* PostgreSQL chat history
* User-specific saved sessions
* User-specific documents
* Document delete and re-index flow
* Better evaluation dashboard

### Long-term improvements

* Production deployment
* S3-compatible storage
* Background jobs for ingestion
* Admin dashboard
* Multi-user workspace support
* Model/provider switching

---

## 19. Current Project Status

```text
Backend RAG Engine:        Working
FastAPI API Layer:         Working
Next.js Frontend:          Working
GitHub Authentication:     Working
Protected Routes:          Working
Ask Page:                  Real backend connected
Documents Page:            Real backend connected
Upload/Rebuild:            Working locally
History Page:              LocalStorage connected
Production Deployment:     Not yet
```

---

## 20. Final Summary

Stage 04 successfully transforms the Python RAG engine into a working full-stack document intelligence product.

The project now supports:

```text
GitHub login
Protected workspace
Real document listing
PDF upload
Index rebuild
Real RAG question answering
Claim-level citation display
Retrieved source previews
Local question history
```

This stage is suitable as a strong portfolio-ready MVP and a foundation for future production features.
