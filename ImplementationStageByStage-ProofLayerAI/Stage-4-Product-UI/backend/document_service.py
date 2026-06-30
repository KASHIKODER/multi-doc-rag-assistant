import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from backend.schemas import (
    DocumentItem,
    DocumentsResponse,
    RebuildIndexResponse,
    UploadDocumentsResponse,
)


CURRENT_FILE = Path(__file__).resolve()
STAGE4_ROOT = CURRENT_FILE.parents[1]
STAGE_ROOT = STAGE4_ROOT.parent

STAGE2_DIR = STAGE_ROOT / "Stage-2-QueryRouting+Re-Ranking+RelevanceGrading"
STAGE2_SCRIPT = STAGE2_DIR / "Kashi-Mate-RAG-Stage-2.py"
STAGE2_DATA_DIR = STAGE2_DIR / "data"
STAGE2_METADATA_DIR = STAGE2_DATA_DIR / "extracted_metadata"
STAGE2_CHROMA_DB = STAGE2_DIR / "chroma_db" / "chroma.sqlite3"


def get_documents() -> DocumentsResponse:
    """
    Return documents currently available in the Stage-2 RAG data folder.

    This service:
    - scans PDFs from Stage-2/data
    - reads extracted metadata when available
    - counts PDF pages
    - reports whether documents appear indexed based on Chroma DB presence
    """
    if not STAGE2_DATA_DIR.exists():
        return DocumentsResponse(total=0, documents=[])

    pdf_files = sorted(STAGE2_DATA_DIR.glob("*.pdf"))
    documents: list[DocumentItem] = []

    for pdf_path in pdf_files:
        metadata = _load_metadata_for_pdf(pdf_path)
        metadata_available = bool(metadata)

        subject = _extract_first_string(
            metadata,
            [
                "subject",
                "module_subject",
                "course_subject",
                "detected_subject",
                "topic_subject",
            ],
        )

        module = _extract_first_value(
            metadata,
            [
                "module_number",
                "module",
                "module_no",
                "module_id",
                "chapter",
            ],
        )

        title = _extract_first_string(
            metadata,
            [
                "module_title",
                "title",
                "document_title",
                "name",
            ],
        )

        if not subject or not module:
            inferred_subject, inferred_module = _infer_from_filename(pdf_path.name)
            subject = subject or inferred_subject
            module = module or inferred_module

        if not title:
            title = _title_from_filename(pdf_path.stem)

        pages = _count_pdf_pages(pdf_path)

        if not metadata_available:
            status = "Missing metadata"
        elif STAGE2_CHROMA_DB.exists():
            status = "Indexed"
        else:
            status = "Not indexed"

        documents.append(
            DocumentItem(
                id=_make_document_id(pdf_path.stem),
                fileName=pdf_path.name,
                subject=subject,
                module=module,
                title=title,
                pages=pages,
                chunks=None,
                status=status,
                metadataAvailable=metadata_available,
            )
        )

    return DocumentsResponse(total=len(documents), documents=documents)


def save_uploaded_pdf_bytes(files: list[tuple[str, bytes]]) -> UploadDocumentsResponse:
    """
    Save uploaded PDF files into the Stage-2/data folder.

    The function accepts a list of:
        (original_file_name, file_bytes)

    It validates:
    - file extension must be .pdf
    - content must not be empty
    - filename must be sanitized before writing to disk
    """
    STAGE2_DATA_DIR.mkdir(parents=True, exist_ok=True)

    saved_files: list[str] = []

    for original_name, content in files:
        safe_name = _safe_pdf_filename(original_name)

        if not safe_name:
            continue

        if not content:
            continue

        destination = STAGE2_DATA_DIR / safe_name
        destination.write_bytes(content)
        saved_files.append(safe_name)

    message = (
        f"Uploaded {len(saved_files)} PDF file."
        if len(saved_files) == 1
        else f"Uploaded {len(saved_files)} PDF files."
    )

    return UploadDocumentsResponse(
        uploaded=len(saved_files),
        files=saved_files,
        message=message,
    )


def rebuild_rag_index() -> RebuildIndexResponse:
    """
    Rebuild Stage-2 Chroma index using the existing Stage-2 ingestion command.

    Equivalent command:
        python Kashi-Mate-RAG-Stage-2.py ingest --rebuild --parse

    It uses sys.executable so the same active virtual environment is used.
    """
    if not STAGE2_SCRIPT.exists():
        return RebuildIndexResponse(
            success=False,
            message=f"Stage-2 script not found: {STAGE2_SCRIPT}",
        )

    command = [
        sys.executable,
        str(STAGE2_SCRIPT),
        "ingest",
        "--rebuild",
        "--parse",
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=str(STAGE2_DIR),
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        return RebuildIndexResponse(
            success=False,
            message="Index rebuild timed out.",
            stdoutPreview=_preview(exc.stdout),
            stderrPreview=_preview(exc.stderr),
        )
    except Exception as exc:
        return RebuildIndexResponse(
            success=False,
            message=f"Index rebuild failed: {type(exc).__name__}: {exc}",
        )

    success = completed.returncode == 0

    return RebuildIndexResponse(
        success=success,
        message=(
            "Index rebuilt successfully."
            if success
            else f"Index rebuild failed with exit code {completed.returncode}."
        ),
        stdoutPreview=_preview(completed.stdout),
        stderrPreview=_preview(completed.stderr),
    )


def _load_metadata_for_pdf(pdf_path: Path) -> dict[str, Any]:
    metadata_path = STAGE2_METADATA_DIR / f"{pdf_path.stem}.json"

    if not metadata_path.exists():
        return {}

    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _count_pdf_pages(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return 0


def _extract_first_string(metadata: dict[str, Any], keys: list[str]) -> str | None:
    value = _extract_first_value(metadata, keys)

    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _extract_first_value(metadata: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in metadata and metadata[key] not in {None, ""}:
            return metadata[key]

    return None


def _infer_from_filename(file_name: str) -> tuple[str | None, int | str | None]:
    name = file_name.replace(".pdf", "")

    module_match = re.search(r"Module\s+(\d+)", name, flags=re.IGNORECASE)
    module = module_match.group(1) if module_match else None

    lowered = name.lower()

    if "css" in lowered:
        subject = "CSS3"
    elif "javascript" in lowered:
        subject = "JavaScript"
    elif "html" in lowered:
        subject = "HTML5"
    elif "bootstrap" in lowered:
        subject = "Bootstrap5"
    elif "sql" in lowered or "mysql" in lowered:
        subject = "ANSI SQL Using MySQL"
    else:
        subject = None

    return subject, module


def _title_from_filename(stem: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", stem).strip()
    return cleaned


def _make_document_id(stem: str) -> str:
    lowered = stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "document"


def _safe_pdf_filename(file_name: str) -> str | None:
    name = Path(file_name).name.strip()

    if not name.lower().endswith(".pdf"):
        return None

    stem = Path(name).stem
    safe_stem = re.sub(r"[^A-Za-z0-9 ._-]+", "", stem).strip()
    safe_stem = re.sub(r"\s+", " ", safe_stem)

    if not safe_stem:
        return None

    return f"{safe_stem}.pdf"


def _preview(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""

    text = str(value)
    text = text.strip()

    if len(text) <= limit:
        return text

    return text[-limit:]
