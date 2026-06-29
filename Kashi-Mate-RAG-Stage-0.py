"""
COMBINED DOCUMENT INTELLIGENCE — COURSE MODULE VERSION
=====================================================

This version combines:

1. Course Module Metadata Parser
   Course PDF -> local metadata JSON
   Fields:
   ModuleTitle, Subject, ModuleNumber, TopicsCovered,
   LearningObjectives, KeyConcepts, Summary

2. Multi-Document RAG
   PDFs + metadata -> chunks -> embeddings -> Chroma -> Ollama answer

Important:
- Course parser is LOCAL and does NOT consume Groq quota.
- RAG answering uses Ollama locally and does NOT consume Groq quota.
- Groq/OpenAI is not required for this course-module version.

Commands:
    python combined_document_intelligence.py parse
    python combined_document_intelligence.py ingest --rebuild --parse
    python combined_document_intelligence.py ask "What topics are covered in CSS3?"
    python combined_document_intelligence.py ask "Explain Bootstrap grid system" --subject Bootstrap5
    python combined_document_intelligence.py chat
"""

import argparse
import json
import logging
import os
import re
import shutil
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Clean public/demo output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*langchain-community.*")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*HF Hub.*")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

from dotenv import load_dotenv
from PyPDF2 import PdfReader

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# ENV + CONFIG
# ============================================================

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "./chroma_db"))
METADATA_DIR = Path(os.getenv("METADATA_DIR", "./data/extracted_metadata"))

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "combined_docs")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "4"))
FETCH_K = int(os.getenv("FETCH_K", "12"))

os.environ["TOKENIZERS_PARALLELISM"] = os.getenv("TOKENIZERS_PARALLELISM", "false")
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = os.getenv("HF_HUB_DISABLE_PROGRESS_BARS", "1")


DEFAULT_COURSE_METADATA: Dict[str, Any] = {
    "DocumentType": "course_module",
    "ModuleTitle": "",
    "Subject": "",
    "ModuleNumber": "",
    "TopicsCovered": [],
    "LearningObjectives": [],
    "KeyConcepts": [],
    "Summary": "",
}


# ============================================================
# DISPLAY HELPERS
# ============================================================

def section(title: str):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def status(label: str, value: str):
    print(f"✅ {label}: {value}")


def info(label: str, value: str):
    print(f"• {label}: {value}")


def warn(message: str):
    print(f"⚠️ {message}")


def clean_preview(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def ensure_folders():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def get_pdf_files() -> List[Path]:
    ensure_folders()
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in '{DATA_DIR}'. Add PDFs first.")
    return pdfs


# ============================================================
# COURSE MODULE METADATA PARSER — LOCAL, NO GROQ
# ============================================================

def extract_text_from_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> str:
    """Extract text from PDF. Used for local metadata parsing."""
    reader = PdfReader(str(pdf_path))
    pages = []

    total = len(reader.pages)
    limit = min(total, max_pages) if max_pages else total

    for idx in range(limit):
        try:
            text = reader.pages[idx].extract_text() or ""
            pages.append(f"\n\n--- PAGE {idx + 1} ---\n{text}")
        except Exception as e:
            warn(f"Could not extract page {idx + 1} from {pdf_path.name}: {e}")

    return "\n".join(pages)


def metadata_path_for(pdf_path: Path) -> Path:
    return METADATA_DIR / f"{pdf_path.stem}.json"


def guess_module_number(filename: str) -> str:
    match = re.search(r"module\s*(\d+)", filename, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def guess_subject_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    # Example: Module 1-Bootstrap5 -> Bootstrap5
    if "-" in stem:
        subject = stem.split("-", 1)[1]
    else:
        subject = re.sub(r"module\s*\d+", "", stem, flags=re.IGNORECASE)

    subject = subject.replace("_", " ").strip()
    subject = re.sub(r"\s+", " ", subject)
    return subject


def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 5 and not line.startswith("--- PAGE"):
            return line
    return ""


def extract_numbered_topics(text: str) -> List[str]:
    """
    Extract headings like:
    1. Why CSS?
    4. Column Layouts and Grid Classes
    18. Bootstrap 5 JavaScript Plugins
    """
    topics = []

    # First try line-wise extraction
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())
        match = re.match(r"^(\d{1,2})\.\s+(.{4,100})$", line)
        if match:
            candidate = match.group(2).strip()
            candidate = re.split(r"\s+Exercise\s+\d", candidate)[0].strip()
            if 4 <= len(candidate) <= 100:
                topics.append(candidate)

    # If PDF extraction merged lines, try broader regex
    if len(topics) < 3:
        pattern = r"(?:^|\s)(\d{1,2})\.\s+([A-Z][A-Za-z0-9 &:/,()\-]+?)(?=\s+Exercise\s+\d|\s+\d{1,2}\.\s+[A-Z]|\n|$)"
        for _, candidate in re.findall(pattern, text):
            candidate = re.sub(r"\s+", " ", candidate).strip()
            if 4 <= len(candidate) <= 100:
                topics.append(candidate)

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for topic in topics:
        key = topic.lower()
        if key not in seen:
            seen.add(key)
            unique.append(topic)

    return unique[:20]


def subject_key_concepts(subject: str) -> List[str]:
    s = subject.lower()

    if "bootstrap" in s:
        return [
            "Bootstrap setup",
            "Containers and rows",
            "Responsive grid system",
            "Column classes",
            "Typography utilities",
            "Buttons and forms",
            "Navbars and cards",
            "Bootstrap JavaScript plugins",
        ]

    if "css" in s:
        return [
            "CSS syntax",
            "Selectors",
            "Colors and backgrounds",
            "Typography",
            "Box model",
            "Tables",
            "Responsive design",
            "Media queries",
        ]

    if "html" in s:
        return [
            "HTML5 document structure",
            "Semantic tags",
            "Forms",
            "Tables",
            "Media elements",
            "Links and navigation",
            "Browser-based portal structure",
        ]

    if "javascript" in s or "java script" in s:
        return [
            "Variables and data types",
            "Functions",
            "DOM manipulation",
            "Events",
            "Form validation",
            "Local storage",
            "Async behavior",
            "Interactive web pages",
        ]

    if "sql" in s or "mysql" in s:
        return [
            "SELECT queries",
            "Filtering and sorting",
            "Joins",
            "Aggregations",
            "GROUP BY",
            "Reports",
            "Subqueries",
            "MySQL database analysis",
        ]

    return []


def build_course_metadata(pdf_path: Path) -> Dict[str, Any]:
    """
    Local metadata builder for course module PDFs.
    This avoids Groq quota and is suited for files like:
    Module 1-Bootstrap5.pdf
    Module 1-CSS3.pdf
    """
    text = extract_text_from_pdf(pdf_path, max_pages=3)
    subject = guess_subject_from_filename(pdf_path.name)
    module_number = guess_module_number(pdf_path.name)

    first_line = first_meaningful_line(text)
    topics = extract_numbered_topics(text)
    key_concepts = subject_key_concepts(subject)

    if first_line and len(first_line) < 120:
        module_title = first_line
    else:
        module_title = f"{subject} Module"

    if not topics and key_concepts:
        topics = key_concepts

    learning_objectives = [
        f"Understand and practice {topic.lower()}."
        for topic in topics[:8]
    ]

    if topics:
        summary = (
            f"This module focuses on {subject}. It covers topics such as "
            f"{', '.join(topics[:6])}."
        )
    else:
        summary = f"This module focuses on {subject}."

    return {
        "DocumentType": "course_module",
        "ModuleTitle": module_title,
        "Subject": subject,
        "ModuleNumber": module_number,
        "TopicsCovered": topics,
        "LearningObjectives": learning_objectives,
        "KeyConcepts": key_concepts,
        "Summary": summary,
    }


def save_metadata_json(pdf_path: Path, metadata: Dict[str, Any]):
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    path = metadata_path_for(pdf_path)
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    status("Metadata saved", str(path))


def load_metadata_json(pdf_path: Path) -> Dict[str, Any]:
    path = metadata_path_for(pdf_path)
    if not path.exists():
        return DEFAULT_COURSE_METADATA.copy()

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        normalized = DEFAULT_COURSE_METADATA.copy()
        for key in normalized:
            normalized[key] = parsed.get(key, normalized[key])
        return normalized
    except Exception as e:
        warn(f"Could not read metadata JSON for {pdf_path.name}: {e}")
        return DEFAULT_COURSE_METADATA.copy()


def parse_course_pdf_if_needed(pdf_path: Path, force_parse: bool = False) -> Dict[str, Any]:
    path = metadata_path_for(pdf_path)

    if path.exists() and not force_parse:
        info("Metadata loaded", path.name)
        return load_metadata_json(pdf_path)

    info("Parsing course metadata locally", pdf_path.name)
    metadata = build_course_metadata(pdf_path)
    save_metadata_json(pdf_path, metadata)
    return metadata


def parse_all_pdfs(force_parse: bool = False):
    section("COURSE MODULE PARSING — PDF TO JSON METADATA")
    print("Local parser: no Groq quota used.\n")

    for pdf in get_pdf_files():
        print(f"\n📄 {pdf.name}")
        metadata = parse_course_pdf_if_needed(pdf, force_parse=force_parse)
        info("ModuleTitle", clean_preview(metadata["ModuleTitle"], 120))
        info("Subject", metadata["Subject"])
        info("ModuleNumber", str(metadata["ModuleNumber"]))
        info("Topics", clean_preview(", ".join(metadata["TopicsCovered"][:8]), 180))


# ============================================================
# RAG INGESTION: PDFS + COURSE METADATA -> CHROMA
# ============================================================

def flatten_metadata_for_chroma(raw: Dict[str, Any], pdf_path: Path) -> Dict[str, Any]:
    topics = raw.get("TopicsCovered", [])
    objectives = raw.get("LearningObjectives", [])
    concepts = raw.get("KeyConcepts", [])

    return {
        "file_name": pdf_path.name,
        "document_type": str(raw.get("DocumentType", "course_module")),
        "module_title": str(raw.get("ModuleTitle", "")),
        "subject": str(raw.get("Subject", "")),
        "module_number": str(raw.get("ModuleNumber", "")),
        "topics_covered": " | ".join(topics) if isinstance(topics, list) else str(topics),
        "learning_objectives": " | ".join(objectives) if isinstance(objectives, list) else str(objectives),
        "key_concepts": " | ".join(concepts) if isinstance(concepts, list) else str(concepts),
        "summary": str(raw.get("Summary", "")),
    }


def load_pdf_pages_with_metadata(pdf_path: Path, parse_metadata: bool, force_parse: bool):
    if parse_metadata:
        raw_meta = parse_course_pdf_if_needed(pdf_path, force_parse=force_parse)
    else:
        # If metadata JSON exists, use it. If not, create lightweight metadata from filename.
        existing = metadata_path_for(pdf_path)
        raw_meta = load_metadata_json(pdf_path) if existing.exists() else build_course_metadata(pdf_path)

    flat_meta = flatten_metadata_for_chroma(raw_meta, pdf_path)

    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()

    for page in pages:
        page.metadata.update(flat_meta)

    return pages


def load_all_documents_for_rag(parse_metadata: bool = False, force_parse: bool = False):
    section("RAG INGESTION — PDFS + COURSE METADATA TO VECTOR DB")

    all_pages = []

    for pdf in get_pdf_files():
        try:
            print(f"\n📄 Loading: {pdf.name}")
            pages = load_pdf_pages_with_metadata(pdf, parse_metadata, force_parse)
            all_pages.extend(pages)
            status("Pages loaded", str(len(pages)))
        except Exception as e:
            warn(f"Skipping {pdf.name}: {type(e).__name__}: {e}")

    if not all_pages:
        raise RuntimeError("No pages loaded. Check your PDFs.")

    status("Total pages loaded", str(len(all_pages)))
    return all_pages


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    status("Chunks created", str(len(chunks)))
    return chunks


def get_embedding_function():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        show_progress=False,
    )


def create_vector_store(chunks):
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding_function(),
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )
    status("Vector DB created", str(CHROMA_DIR))
    return vector_store


def load_vector_store():
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embedding_function(),
        collection_name=COLLECTION_NAME,
    )
    status("Vector DB loaded", str(CHROMA_DIR))
    return vector_store


def ingest_documents(rebuild: bool = False, parse_metadata: bool = False, force_parse: bool = False):
    if rebuild and CHROMA_DIR.exists():
        warn("Rebuild enabled. Removing old Chroma DB.")
        shutil.rmtree(CHROMA_DIR)

    if CHROMA_DIR.exists() and not rebuild:
        info("Existing Chroma DB", "Already exists. Use --rebuild to recreate.")
        return load_vector_store()

    documents = load_all_documents_for_rag(parse_metadata, force_parse)
    chunks = split_documents(documents)
    return create_vector_store(chunks)


# ============================================================
# QUESTION ANSWERING: CHROMA -> OLLAMA
# ============================================================

def metadata_matches(
    doc,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    meta = doc.metadata

    if subject and subject.lower() not in str(meta.get("subject", "")).lower():
        return False

    if module and str(module).lower() != str(meta.get("module_number", "")).lower():
        return False

    if title and title.lower() not in str(meta.get("module_title", "")).lower():
        return False

    return True


def retrieve_docs(
    query: str,
    vector_store,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    title: Optional[str] = None,
):
    candidates = vector_store.similarity_search(query, k=FETCH_K)

    filtered = [
        doc for doc in candidates
        if metadata_matches(doc, subject=subject, module=module, title=title)
    ]

    if not filtered and any([subject, module, title]):
        warn("No docs matched metadata filters. Falling back to semantic search only.")
        filtered = candidates

    return filtered[:TOP_K]


def format_docs_for_prompt(docs) -> str:
    blocks = []

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        header = (
            f"[Source {i}: {meta.get('file_name', meta.get('source', 'unknown'))}, "
            f"page={meta.get('page', 'unknown')}, "
            f"subject={meta.get('subject', '')}, "
            f"module={meta.get('module_number', '')}, "
            f"title={meta.get('module_title', '')}]"
        )
        blocks.append(f"{header}\n{doc.page_content}")

    return "\n\n".join(blocks)


def answer_question(
    query: str,
    vector_store,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    title: Optional[str] = None,
):
    docs = retrieve_docs(query, vector_store, subject=subject, module=module, title=title)

    if not docs:
        return "I don't know based on the provided documents.", []

    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

    prompt = ChatPromptTemplate.from_template(
        """
You are a helpful course-module QA assistant.

Answer ONLY using the context below.
If the answer is not present in the context, say exactly:
"I don't know based on the provided documents."

Important:
- If the context contains enough information to answer, answer directly.
- Do NOT add "I don't know" after giving a valid answer.
- Mention module/source names when useful.

Context:
{context}

Question:
{question}

Answer:
"""
    )

    answer = (prompt | llm | StrOutputParser()).invoke(
        {"context": format_docs_for_prompt(docs), "question": query}
    )

    return answer, docs


def print_sources(docs):
    print("\n📚 Retrieved sources:")

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        source = meta.get("file_name", meta.get("source", "unknown"))
        page = meta.get("page", "unknown")
        subject = meta.get("subject", "")
        module = meta.get("module_number", "")
        title = meta.get("module_title", "")

        print(
            f"{i}. {source} | page={page} | "
            f"subject={subject} | module={module} | title={clean_preview(title, 70)}"
        )
        print(f"   Preview: {clean_preview(doc.page_content, 180)}")


def run_ask(args):
    vector_store = load_vector_store()

    answer, docs = answer_question(
        query=args.question,
        vector_store=vector_store,
        subject=args.subject,
        module=args.module,
        title=args.title,
    )

    print("\n🧠 Answer:")
    print(answer)

    print_sources(docs)


def run_chat():
    vector_store = load_vector_store()

    section("COMBINED COURSE MODULE RAG CHAT")
    print("Ask questions about your PDFs. Type 'exit' to quit.\n")

    while True:
        query = input("❓ Question: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting.")
            break

        if not query:
            continue

        answer, docs = answer_question(query, vector_store)

        print("\n🧠 Answer:")
        print(answer)
        print_sources(docs)
        print("\n" + "-" * 72 + "\n")


# ============================================================
# CLI
# ============================================================

def build_cli():
    parser = argparse.ArgumentParser(
        description="Course Metadata Parser + Multi-Document RAG"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_parse = sub.add_parser("parse", help="Extract course metadata JSON from PDFs locally")
    p_parse.add_argument("--force", action="store_true", help="Re-parse even if JSON already exists")

    p_ingest = sub.add_parser("ingest", help="Build Chroma vector DB from PDFs")
    p_ingest.add_argument("--rebuild", action="store_true", help="Delete old Chroma DB and rebuild")
    p_ingest.add_argument("--parse", action="store_true", help="Create/use course metadata before attaching it to chunks")
    p_ingest.add_argument("--force-parse", action="store_true", help="Re-parse metadata even if JSON exists")

    p_ask = sub.add_parser("ask", help="Ask one question")
    p_ask.add_argument("question", type=str)
    p_ask.add_argument("--subject", type=str, default=None, help="Optional subject filter, e.g. CSS3")
    p_ask.add_argument("--module", type=str, default=None, help="Optional module number filter, e.g. 1")
    p_ask.add_argument("--title", type=str, default=None, help="Optional module title substring filter")

    sub.add_parser("chat", help="Interactive chat mode")

    return parser


def main():
    ensure_folders()
    args = build_cli().parse_args()

    if args.command == "parse":
        parse_all_pdfs(force_parse=args.force)

    elif args.command == "ingest":
        ingest_documents(
            rebuild=args.rebuild,
            parse_metadata=args.parse,
            force_parse=args.force_parse,
        )

    elif args.command == "ask":
        run_ask(args)

    elif args.command == "chat":
        run_chat()


if __name__ == "__main__":
    main()
