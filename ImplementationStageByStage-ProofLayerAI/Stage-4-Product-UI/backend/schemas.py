from typing import Literal

from pydantic import BaseModel, Field


AnswerMode = Literal["topic", "citation", "unsupported"]
ClaimConfidence = Literal["high", "medium", "low"]


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural language question asked by the user.",
    )


class RetrievalStats(BaseModel):
    candidates: int = Field(
        ...,
        ge=0,
        description="Number of initially retrieved candidate chunks.",
    )
    reranked: int = Field(
        ...,
        ge=0,
        description="Number of chunks processed by the re-ranking stage.",
    )
    keptAfterGrading: int = Field(
        ...,
        ge=0,
        description="Number of chunks kept after relevance grading.",
    )


class VerifiedClaim(BaseModel):
    id: str
    claim: str
    source: str
    page: int | str
    confidence: ClaimConfidence
    subject: str | None = None
    module: int | str | None = None
    title: str | None = None


class RetrievedSource(BaseModel):
    id: str
    fileName: str
    title: str | None = None
    page: int | str
    subject: str | None = None
    module: int | str | None = None
    preview: str


class AskResponse(BaseModel):
    question: str
    detectedSubject: str | None
    detectedModule: int | str | None
    semanticQuery: str
    answerMode: AnswerMode
    retrievalStats: RetrievalStats
    summary: str
    claims: list[VerifiedClaim]
    sources: list[RetrievedSource]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    stage: str

class DocumentItem(BaseModel):
    id: str
    fileName: str
    subject: str | None = None
    module: int | str | None = None
    title: str | None = None
    pages: int = Field(
        default=0,
        ge=0,
        description="Number of pages found in the source PDF.",
    )
    chunks: int | None = Field(
        default=None,
        ge=0,
        description="Number of indexed chunks when available.",
    )
    status: Literal["Indexed", "Not indexed", "Missing metadata"] = "Indexed"
    metadataAvailable: bool = False


class DocumentsResponse(BaseModel):
    total: int = Field(..., ge=0)
    documents: list[DocumentItem]


class UploadDocumentsResponse(BaseModel):
    uploaded: int = Field(..., ge=0)
    files: list[str]
    message: str


class RebuildIndexResponse(BaseModel):
    success: bool
    message: str
    stdoutPreview: str = ""
    stderrPreview: str = ""
