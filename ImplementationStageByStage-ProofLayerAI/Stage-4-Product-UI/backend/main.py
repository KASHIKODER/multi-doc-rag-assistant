from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.document_service import (
    get_documents,
    rebuild_rag_index,
    save_uploaded_pdf_bytes,
)
from backend.rag_bridge import rag_bridge
from backend.schemas import (
    AskRequest,
    AskResponse,
    DocumentsResponse,
    HealthResponse,
    RebuildIndexResponse,
    UploadDocumentsResponse,
)


app = FastAPI(
    title="DocuMind RAG API",
    description="FastAPI bridge for the routed, re-ranked, and graded multi-document RAG engine.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="DocuMind RAG API",
        stage="Stage 04 Product UI API",
    )


@app.get("/documents", response_model=DocumentsResponse)
def list_documents() -> DocumentsResponse:
    try:
        return get_documents()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document listing failed: {type(exc).__name__}: {exc}",
        ) from exc


@app.post("/documents/upload", response_model=UploadDocumentsResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
) -> UploadDocumentsResponse:
    try:
        file_payloads: list[tuple[str, bytes]] = []

        for uploaded_file in files:
            content = await uploaded_file.read()
            file_payloads.append((uploaded_file.filename or "uploaded.pdf", content))

        result = save_uploaded_pdf_bytes(file_payloads)

        if result.uploaded == 0:
            raise HTTPException(
                status_code=400,
                detail="No valid PDF files were uploaded.",
            )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {type(exc).__name__}: {exc}",
        ) from exc


@app.post("/documents/rebuild", response_model=RebuildIndexResponse)
def rebuild_documents_index() -> RebuildIndexResponse:
    try:
        result = rebuild_rag_index()

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=result.model_dump(),
            )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Index rebuild failed: {type(exc).__name__}: {exc}",
        ) from exc


@app.post("/ask", response_model=AskResponse)
def ask_documents(payload: AskRequest) -> AskResponse:
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        return rag_bridge.ask(question)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG pipeline failed: {type(exc).__name__}: {exc}",
        ) from exc
