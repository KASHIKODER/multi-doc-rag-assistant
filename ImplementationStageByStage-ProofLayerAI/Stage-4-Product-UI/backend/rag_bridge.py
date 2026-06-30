import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from backend.schemas import (
    AskResponse,
    RetrievedSource,
    RetrievalStats,
    VerifiedClaim,
)


CURRENT_FILE = Path(__file__).resolve()
STAGE4_ROOT = CURRENT_FILE.parents[1]
STAGE_ROOT = STAGE4_ROOT.parent

STAGE2_DIR = STAGE_ROOT / "Stage-2-QueryRouting+Re-Ranking+RelevanceGrading"
STAGE2_SCRIPT = STAGE2_DIR / "Kashi-Mate-RAG-Stage-2.py"


@contextmanager
def stage2_working_directory():
    """
    Stage-2 RAG code uses relative paths such as ./data and ./chroma_db.
    This context manager temporarily moves execution into the Stage-2 folder
    so the existing backend logic works without modifying Stage-2 code.
    """
    previous_cwd = Path.cwd()
    os.chdir(STAGE2_DIR)

    try:
        yield
    finally:
        os.chdir(previous_cwd)


class RagBridge:
    """
    Bridge between the FastAPI layer and the existing Stage-2 RAG engine.

    This class intentionally does not rewrite the RAG logic.
    It imports and reuses the already-working Stage-2 functions:
    - parse_natural_query
    - apply_query_routing
    - retrieve_rerank_and_grade_docs
    - generate_cited_answer
    - collect_topic_items_from_docs
    - resolve_claim_source_index
    """

    def __init__(self) -> None:
        self.rag_module: Any | None = None
        self.vector_store: Any | None = None

    def load(self) -> None:
        """
        Import Stage-2 RAG module and load vector store once.

        ENABLE_LLM_GRADING defaults to false for API speed.
        You can enable it later with:
            $env:ENABLE_LLM_GRADING="true"
        before running FastAPI.
        """
        if self.rag_module is not None and self.vector_store is not None:
            return

        if not STAGE2_SCRIPT.exists():
            raise FileNotFoundError(f"Stage-2 RAG script not found: {STAGE2_SCRIPT}")

        os.environ.setdefault("ENABLE_LLM_GRADING", "false")

        with stage2_working_directory():
            spec = importlib.util.spec_from_file_location(
                "stage2_rag_engine",
                STAGE2_SCRIPT,
            )

            if spec is None or spec.loader is None:
                raise ImportError(f"Could not import Stage-2 RAG script: {STAGE2_SCRIPT}")

            module = importlib.util.module_from_spec(spec)
            sys.modules["stage2_rag_engine"] = module
            spec.loader.exec_module(module)

            vector_store = module.load_vector_store()

        self.rag_module = module
        self.vector_store = vector_store

    def ask(self, question: str) -> AskResponse:
        """
        Main public method used by FastAPI.

        It runs the Stage-2 pipeline and converts the result into the
        frontend-compatible AskResponse schema.
        """
        self.load()

        if self.rag_module is None or self.vector_store is None:
            raise RuntimeError("RAG bridge failed to initialize.")

        rag = self.rag_module

        with stage2_working_directory():
            parsed = rag.parse_natural_query(question)
            rag.apply_query_routing(parsed, question)

            docs, retrieval_stats_raw = rag.retrieve_rerank_and_grade_docs(
                query=parsed.semantic_query,
                vector_store=self.vector_store,
                subject=parsed.subject,
                module=parsed.module,
            )

            stats = self._map_retrieval_stats(retrieval_stats_raw, docs)

            if not docs:
                return AskResponse(
                    question=question,
                    detectedSubject=parsed.subject,
                    detectedModule=parsed.module,
                    semanticQuery=parsed.semantic_query,
                    answerMode="unsupported",
                    retrievalStats=stats,
                    summary="No relevant document context was retrieved for this question.",
                    claims=[],
                    sources=[],
                )

            sources = self._map_sources(docs)

            if rag.is_topic_style_question(question, parsed.semantic_query):
                return self._build_topic_response(
                    question=question,
                    parsed=parsed,
                    docs=docs,
                    stats=stats,
                    sources=sources,
                )

            return self._build_citation_response(
                question=question,
                parsed=parsed,
                docs=docs,
                stats=stats,
                sources=sources,
            )

    def _map_retrieval_stats(self, raw_stats: dict[str, Any], docs: list[Any]) -> RetrievalStats:
        return RetrievalStats(
            candidates=int(raw_stats.get("candidates", len(docs))),
            reranked=int(raw_stats.get("reranked", len(docs))),
            keptAfterGrading=int(raw_stats.get("graded_relevant", len(docs))),
        )

    def _map_sources(self, docs: list[Any]) -> list[RetrievedSource]:
        rag = self.rag_module
        sources: list[RetrievedSource] = []

        for index, doc in enumerate(docs, start=1):
            meta = getattr(doc, "metadata", {}) or {}

            file_name = meta.get("file_name") or meta.get("source") or "unknown"
            title = self._clean(meta.get("module_title", ""))
            subject = self._clean(meta.get("subject", ""))
            module = meta.get("module_number", "")
            page = self._display_page(meta.get("page", "?"))

            page_content = getattr(doc, "page_content", "") or ""
            preview = (
                rag.clean_preview(page_content, 500)
                if hasattr(rag, "clean_preview")
                else page_content[:500]
            )

            sources.append(
                RetrievedSource(
                    id=f"source_{index:03d}",
                    fileName=str(file_name),
                    title=title or None,
                    page=page,
                    subject=subject or None,
                    module=module or None,
                    preview=preview,
                )
            )

        return sources

    def _build_topic_response(
        self,
        question: str,
        parsed: Any,
        docs: list[Any],
        stats: RetrievalStats,
        sources: list[RetrievedSource],
    ) -> AskResponse:
        rag = self.rag_module

        topic_items = rag.collect_topic_items_from_docs(
            docs=docs,
            query=f"{question} {parsed.semantic_query}",
        )

        claims: list[VerifiedClaim] = []

        for index, item in enumerate(topic_items, start=1):
            topic_text = self._clean(item[0])

            if not topic_text:
                continue

            source_label = item[2] if len(item) > 2 else {}
            source_name = source_label.get("source_name", "unknown")
            page = self._display_page(source_label.get("page", "?"))
            subject = self._clean(source_label.get("subject", ""))
            module = source_label.get("module", "")
            title = self._clean(source_label.get("title", ""))

            claims.append(
                VerifiedClaim(
                    id=f"topic_{index:03d}",
                    claim=topic_text,
                    source=str(source_name),
                    page=page,
                    confidence="high",
                    subject=subject or None,
                    module=module or None,
                    title=title or None,
                )
            )

        if claims:
            summary = (
                f"The retrieved sources indicate that "
                f"{parsed.subject or 'the selected documents'} cover these topics."
            )
            answer_mode = "topic"
        else:
            summary = "No document-grounded topics were found for this question."
            answer_mode = "unsupported"

        return AskResponse(
            question=question,
            detectedSubject=parsed.subject,
            detectedModule=parsed.module,
            semanticQuery=parsed.semantic_query,
            answerMode=answer_mode,
            retrievalStats=stats,
            summary=summary,
            claims=claims,
            sources=sources,
        )

    def _build_citation_response(
        self,
        question: str,
        parsed: Any,
        docs: list[Any],
        stats: RetrievalStats,
        sources: list[RetrievedSource],
    ) -> AskResponse:
        rag = self.rag_module
        cited_answer = rag.generate_cited_answer(parsed.semantic_query, docs)

        claims: list[VerifiedClaim] = []
        seen_claims: set[str] = set()

        for index, claim in enumerate(getattr(cited_answer, "claims", []) or [], start=1):
            source_idx, _source_method = rag.resolve_claim_source_index(claim, docs)

            if source_idx is None:
                continue

            confidence = str(getattr(claim, "confidence", "low")).lower().strip()

            if confidence == "low":
                continue

            claim_text = str(getattr(claim, "claim_text", "")).strip()

            if not claim_text:
                continue

            claim_key = (
                rag.claim_key(claim_text)
                if hasattr(rag, "claim_key")
                else claim_text.lower()
            )

            if claim_key in seen_claims:
                continue

            seen_claims.add(claim_key)

            meta = getattr(docs[source_idx], "metadata", {}) or {}

            claims.append(
                VerifiedClaim(
                    id=f"claim_{index:03d}",
                    claim=claim_text,
                    source=str(meta.get("file_name") or meta.get("source") or "unknown"),
                    page=self._display_page(meta.get("page", "?")),
                    confidence="high" if confidence == "high" else "medium",
                    subject=self._clean(meta.get("subject", "")) or None,
                    module=meta.get("module_number", "") or None,
                    title=self._clean(meta.get("module_title", "")) or None,
                )
            )

        if not claims:
            return AskResponse(
                question=question,
                detectedSubject=parsed.subject,
                detectedModule=parsed.module,
                semanticQuery=parsed.semantic_query,
                answerMode="unsupported",
                retrievalStats=stats,
                summary="No supported claims were found in the retrieved sources.",
                claims=[],
                sources=sources,
            )

        summary = str(getattr(cited_answer, "overall_summary", "") or "").strip()

        if not summary:
            summary = "The retrieved sources support the following verified claims."

        return AskResponse(
            question=question,
            detectedSubject=parsed.subject,
            detectedModule=parsed.module,
            semanticQuery=parsed.semantic_query,
            answerMode="citation",
            retrievalStats=stats,
            summary=summary,
            claims=claims,
            sources=sources,
        )

    def _clean(self, value: Any) -> str:
        rag = self.rag_module
        text = "" if value is None else str(value)

        if rag is not None and hasattr(rag, "clean_display_text"):
            return rag.clean_display_text(text)

        return text.strip()

    def _display_page(self, value: Any) -> int | str:
        rag = self.rag_module

        if rag is not None and hasattr(rag, "display_page_number"):
            return rag.display_page_number(value)

        return value if value not in {None, ""} else "?"


rag_bridge = RagBridge()
