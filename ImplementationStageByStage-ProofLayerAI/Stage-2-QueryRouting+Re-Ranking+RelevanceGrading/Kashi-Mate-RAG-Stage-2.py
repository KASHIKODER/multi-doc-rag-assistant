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

3. Query Construction (NEW)
   Natural language -> structured filters (subject, module) + semantic query

4. Claim-Level Citation (NEW)
   Answer -> individual claims, each mapped to a specific source + confidence

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
from typing import Any, Dict, List, Optional, Tuple

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

# --- NEW IMPORTS for Query Construction + Claim-Level Citation ---
from pydantic import BaseModel, Field


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

# Advanced retrieval controls for chat mode.
# ask mode stays backward-compatible and still uses the normal retrieval path.
RERANK_CANDIDATE_LIMIT = int(os.getenv("RERANK_CANDIDATE_LIMIT", str(FETCH_K)))
GRADE_CANDIDATE_LIMIT = int(os.getenv("GRADE_CANDIDATE_LIMIT", "6"))
MIN_GRADED_DOCS = int(os.getenv("MIN_GRADED_DOCS", "2"))
ENABLE_LLM_GRADING = os.getenv("ENABLE_LLM_GRADING", "true").lower() in {"1", "true", "yes", "on"}

# Known subjects in this course-module system (used by Query Construction)
KNOWN_SUBJECTS = ["HTML5", "HTML 5", "CSS3", "Bootstrap5", "JavaScript", "SQL", "MySQL"]

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


def clean_display_text(text: str) -> str:
    """
    Clean small PDF text-extraction spacing artifacts before displaying output.
    This does not change stored metadata or retrieval behavior.
    """
    text = re.sub(r"\s+", " ", str(text)).strip()

    replacements = {
        "Exer cises": "Exercises",
        "Exerci ses": "Exercises",
        "Exerc ises": "Exercises",
        "JavaScript Exer cises": "JavaScript Exercises",
        "JavaScript Exerci ses": "JavaScript Exercises",
        "Bootstrap 5 Exerci ses": "Bootstrap 5 Exercises",
        "HTML5 Exerci ses": "HTML5 Exercises",
        "ANSI SQL Using MySQL Exerc ises": "ANSI SQL Using MySQL Exercises",
        "Higher -Order": "Higher-Order",
        "Async /Await": "Async/Await",
        "HTML 5": "HTML5",
    }

    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    return text

def display_page_number(page_value) -> str:
    """
    LangChain/PyPDFLoader stores PDF page metadata as zero-based index.
    This converts it to human-readable PDF page number.
    
    Example:
    page=0 -> Page 1
    page=1 -> Page 2
    """
    try:
        return str(int(page_value) + 1)
    except Exception:
        return str(page_value)

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
    topics = []

    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())
        match = re.match(r"^(\d{1,2})\.\s+(.{4,100})$", line)
        if match:
            candidate = match.group(2).strip()
            candidate = re.split(r"\s+Exercise\s+\d", candidate)[0].strip()
            if 4 <= len(candidate) <= 100:
                topics.append(candidate)

    if len(topics) < 3:
        pattern = r"(?:^|\s)(\d{1,2})\.\s+([A-Z][A-Za-z0-9 &:/,()\-]+?)(?=\s+Exercise\s+\d|\s+\d{1,2}\.\s+[A-Z]|\n|$)"
        for _, candidate in re.findall(pattern, text):
            candidate = re.sub(r"\s+", " ", candidate).strip()
            if 4 <= len(candidate) <= 100:
                topics.append(candidate)

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
            "Bootstrap setup", "Containers and rows", "Responsive grid system",
            "Column classes", "Typography utilities", "Buttons and forms",
            "Navbars and cards", "Bootstrap JavaScript plugins",
        ]

    if "css" in s:
        return [
            "CSS syntax", "Selectors", "Colors and backgrounds", "Typography",
            "Box model", "Tables", "Responsive design", "Media queries",
        ]

    if "html" in s:
        return [
            "HTML5 document structure", "Semantic tags", "Forms", "Tables",
            "Media elements", "Links and navigation", "Browser-based portal structure",
        ]

    if "javascript" in s or "java script" in s:
        return [
            "Variables and data types", "Functions", "DOM manipulation", "Events",
            "Form validation", "Local storage", "Async behavior", "Interactive web pages",
        ]

    if "sql" in s or "mysql" in s:
        return [
            "SELECT queries", "Filtering and sorting", "Joins", "Aggregations",
            "GROUP BY", "Reports", "Subqueries", "MySQL database analysis",
        ]

    return []


def build_course_metadata(pdf_path: Path) -> Dict[str, Any]:
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
# NEW SECTION — QUERY CONSTRUCTION
# ============================================================
# Converts a natural language question into structured filters
# (subject, module) + a clean semantic query, instead of requiring
# the user to type --subject/--module manually every time.

class CourseQuery(BaseModel):
    """Structured representation of a natural-language course question."""
    subject: Optional[str] = Field(
        None,
        description=(
            "Subject filter if the question clearly mentions one. "
            f"Must be one of: {', '.join(KNOWN_SUBJECTS)}. "
            "Use None if no specific subject is mentioned."
        ),
    )
    module: Optional[str] = Field(
        None,
        description="Module number filter if mentioned, e.g. '1', '2'. Use None if not mentioned.",
    )
    semantic_query: str = Field(
        ...,
        description=(
            "The core question rewritten for semantic search, with filter "
            "words (subject/module names) removed if they were only used as filters."
        ),
    )




class RelevanceGrade(BaseModel):
    """Structured relevance judgment for a retrieved chunk."""
    relevant: bool = Field(description="True if the chunk directly helps answer the question.")
    reason: str = Field(description="Short reason explaining the relevance decision.")


def rule_based_query_construction(user_input: str) -> Optional["CourseQuery"]:
    """
    Reliable local parser for common English course-module questions.

    This runs before the local LLM because short natural-language questions are better handled deterministically.
    """
    q = user_input.lower()

    subject_aliases = {
        "CSS3": [
            "css", "css3", "selector", "selectors", "styling",
            "box model", "media query", "media queries", "typography",
            "background", "color", "colors",
        ],
        "Bootstrap5": [
            "bootstrap", "bootstrap5", "grid", "navbar", "card",
            "container", "row", "column", "columns", "col-", "responsive layout",
        ],
        "HTML5": [
            "html", "html5", "html 5", "semantic", "tag", "tags",
            "form", "forms", "table", "media elements", "doctype", "nav",
        ],
        "JavaScript": [
            "javascript", "java script", "js", "dom", "event", "events",
            "function", "functions", "local storage", "validation",
            "onclick", "listener", "listeners",
        ],
        "SQL": [
            "sql", "mysql", "join", "joins", "select", "group by",
            "aggregation", "database", "query", "queries", "subquery",
            "subqueries", "report", "reports", "relationship", "relationships",
            "foreign key", "foreign keys", "primary key", "primary keys",
            "table relationship", "table relationships",
        ],
    }

    # First priority: explicit subject mentions must win over generic topic aliases.
    # Example: "What table relationships are described in the SQL module?"
    # contains "table", but because it explicitly says SQL, it must route to SQL, not HTML5.
    explicit_subject_patterns = [
        (r"\b(css|css3)\b", "CSS3"),
        (r"\b(bootstrap|bootstrap5|bootstrap\s*5)\b", "Bootstrap5"),
        (r"\b(html|html5|html\s*5)\b", "HTML5"),
        (r"\b(javascript|java\s*script|js)\b", "JavaScript"),
        (r"\b(sql|mysql|ansi\s*sql)\b", "SQL"),
    ]

    detected_subject = None
    for pattern, subject_name in explicit_subject_patterns:
        if re.search(pattern, q):
            detected_subject = subject_name
            break

    # Second priority: infer a subject from topic words only when no explicit subject was found.
    if detected_subject is None:
        for canonical_subject, aliases in subject_aliases.items():
            if any(alias in q for alias in aliases):
                detected_subject = canonical_subject
                break

    detected_module = None
    module_match = re.search(r"\bmodule\s*(\d+)\b", q)
    if module_match:
        detected_module = module_match.group(1)

    semantic_query = user_input

    # Remove module filter text from semantic query.
    semantic_query = re.sub(r"\bmodule\s*\d+\b", " ", semantic_query, flags=re.IGNORECASE)

    # Remove common filter/filler words so vector search focuses on intent.
    remove_terms = [
        "css3", "css", "bootstrap5", "bootstrap", "html5", "html 5", "html",
        "javascript", "java script", "js", "sql", "mysql",
        "and", "tell me", "about", "explain", "please",
        "some", "important", "in", "the", "a", "an", "what", "does",
        "describe", "described", "module",
        "cover", "covers", "covered", "list", "show",
    ]

    for term in remove_terms:
        semantic_query = re.sub(rf"\b{re.escape(term)}\b", " ", semantic_query, flags=re.IGNORECASE)

    semantic_query = re.sub(r"\s+", " ", semantic_query).strip(" ?.,;:")

    # Professional intent normalization for known course questions.
    if detected_subject == "JavaScript" and any(word in q for word in ["event", "events", "onclick", "listener"]):
        semantic_query = "events covered"

    elif detected_subject == "SQL" and any(
        phrase in q
        for phrase in [
            "relationship", "relationships", "foreign key", "foreign keys",
            "primary key", "primary keys", "table relationship", "table relationships"
        ]
    ):
        semantic_query = "table relationships explanation"

    elif detected_subject == "SQL" and any(word in q for word in ["join", "joins"]):
        semantic_query = "joins explanation"

    elif detected_subject == "Bootstrap5" and "grid" in q:
        semantic_query = "grid system explanation"

    elif detected_subject == "HTML5" and any(word in q for word in ["form", "forms", "semantic", "tags", "tag"]):
        semantic_query = "forms semantic tags covered"

    elif detected_subject and any(word in q for word in ["topic", "topics", "important", "cover", "covered", "syllabus"]):
        semantic_query = "important topics covered"

    elif (
        not semantic_query
        or len(semantic_query) < 4
        or semantic_query.lower() in {"module", "topic", "topics"}
    ):
        if any(word in q for word in ["topic", "topics", "cover", "covered", "syllabus"]):
            semantic_query = "topics covered"
        elif any(word in q for word in ["explain", "explanation"]):
            semantic_query = "explanation"
        else:
            semantic_query = user_input

    if detected_subject or detected_module:
        return CourseQuery(
            subject=detected_subject,
            module=detected_module,
            semantic_query=semantic_query,
        )

    return None


def parse_natural_query(user_input: str) -> "CourseQuery":
    """
    Hybrid Query Construction.

    Order:
    1. Rule-based parser for reliable English and informal course queries.
    2. Local LLM structured output if rules did not detect filters.
    3. Safe fallback to plain semantic search.

    This fixes cases where local Ollama returned:
    subject=None, module=None, semantic_query='Module'
    for a query like:
    "What topics are covered in Module 1 CSS?"
    """
    rule_result = rule_based_query_construction(user_input)
    if rule_result is not None:
        return rule_result

    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

    try:
        # method="json_schema" is supported by recent langchain-ollama versions.
        # If older versions do not support the argument, the except block below
        # tries the older call style automatically.
        try:
            structured_llm = llm.with_structured_output(CourseQuery, method="json_schema")
        except TypeError:
            structured_llm = llm.with_structured_output(CourseQuery)

        prompt = ChatPromptTemplate.from_template(
            "Extract structured filters from this question about course modules.\n"
            f"Available subjects: {', '.join(KNOWN_SUBJECTS)}\n"
            "Return subject only if clearly implied by the question.\n"
            "Return module only if a module number is clearly mentioned.\n"
            "Return a useful semantic_query for vector search.\n\n"
            "Examples:\n"
            "Question: What topics are covered in Module 1 CSS?\n"
            "subject: CSS3\n"
            "module: 1\n"
            "semantic_query: topics covered\n\n"
            "Question: Explain the Bootstrap grid system.\n"
            "subject: Bootstrap5\n"
            "module: null\n"
            "semantic_query: grid system explanation\n\n"
            "Question: What are SQL joins?\n"
            "subject: SQL\n"
            "module: null\n"
            "semantic_query: joins explanation\n\n"
            "Question: {question}"
        )

        chain = prompt | structured_llm
        result = chain.invoke({"question": user_input})

        # Safety cleanup if local model returns weak/partial output.
        bad_queries = {"module", "css", "html", "sql", "js", "javascript", "bootstrap"}
        if not result.semantic_query or len(result.semantic_query.strip()) < 4:
            result.semantic_query = user_input

        if result.semantic_query.strip().lower() in bad_queries:
            result.semantic_query = user_input

        # Normalize subject aliases returned by the model.
        if result.subject:
            subject_norm = normalize_filter_text(result.subject)
            if subject_norm in {"html5", "html"}:
                result.subject = "HTML5"
            elif subject_norm in {"css3", "css"}:
                result.subject = "CSS3"
            elif subject_norm in {"bootstrap5", "bootstrap"}:
                result.subject = "Bootstrap5"
            elif subject_norm in {"javascript", "js"}:
                result.subject = "JavaScript"
            elif subject_norm in {"sql", "mysql", "ansisql"}:
                result.subject = "SQL"

        return result

    except Exception as e:
        warn(f"Query construction failed, falling back to plain semantic search: {e}")
        return CourseQuery(subject=None, module=None, semantic_query=user_input)



# ============================================================
# ADVANCED QUERY ROUTING
# ============================================================
# Query Construction extracts explicit filters.
# Query Routing is the next safety layer: if the user asks a topic-only
# question such as "What are selectors?", the router infers the most likely
# subject before retrieval.

ROUTING_KEYWORDS: Dict[str, Dict[str, int]] = {
    "CSS3": {
        "selector": 4, "selectors": 4, "css selector": 5,
        "box model": 4, "media query": 4, "media queries": 4,
        "typography": 2, "color": 2, "background": 2,
    },
    "Bootstrap5": {
        "grid": 5, "grid system": 6, "column": 3, "columns": 3,
        "row": 2, "container": 2, "navbar": 4, "card": 3,
        "responsive layout": 4,
    },
    "HTML5": {
        "semantic tag": 5, "semantic tags": 5, "doctype": 4,
        "nav element": 4, "anchor tag": 3, "html form": 4,
        "html forms": 4, "media elements": 3,
    },
    "JavaScript": {
        "dom": 5, "event": 4, "events": 4, "event handling": 5,
        "function": 3, "functions": 3, "closure": 4, "closures": 4,
        "promise": 4, "promises": 4, "async": 4, "fetch api": 5,
        "local storage": 4,
    },
    "SQL": {
        "join": 5, "joins": 5, "foreign key": 5, "foreign keys": 5,
        "primary key": 4, "primary keys": 4, "table relationship": 5,
        "table relationships": 5, "group by": 4, "aggregation": 3,
        "subquery": 4, "subqueries": 4,
    },
}


def route_query_to_subject(original_query: str, semantic_query: str) -> Optional[Dict[str, Any]]:
    """
    Infer a subject when Query Construction does not return one.

    This is intentionally conservative. Explicit subject mentions are handled
    inside rule_based_query_construction(); this router focuses on topic-only
    questions such as "What are selectors?" or "Explain grid columns.".
    """
    combined = f"{original_query} {semantic_query}".lower()

    scores: Dict[str, int] = {subject: 0 for subject in ROUTING_KEYWORDS}
    matched_terms: Dict[str, List[str]] = {subject: [] for subject in ROUTING_KEYWORDS}

    for subject, weighted_terms in ROUTING_KEYWORDS.items():
        for term, weight in weighted_terms.items():
            if term in combined:
                scores[subject] += weight
                matched_terms[subject].append(term)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_subject, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    # Conservative threshold: route only if there is a clear winner.
    if best_score >= 4 and best_score >= second_score + 2:
        return {
            "subject": best_subject,
            "score": best_score,
            "reason": ", ".join(matched_terms[best_subject][:3]),
        }

    return None


def apply_query_routing(parsed: "CourseQuery", original_query: str) -> Optional[Dict[str, Any]]:
    """
    Apply subject routing only when Query Construction did not already detect a subject.
    """
    if parsed.subject:
        return None

    routing_decision = route_query_to_subject(original_query, parsed.semantic_query)

    if routing_decision:
        parsed.subject = routing_decision["subject"]
        return routing_decision

    return None


# ============================================================
# QUESTION ANSWERING: CHROMA -> OLLAMA
# ============================================================

def normalize_filter_text(text: str) -> str:
    """
    Normalize metadata/filter text for robust matching.

    Examples:
    - "HTML5" matches "HTML 5"
    - "SQL" matches "ANSI SQL Using MySQL"
    """
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def metadata_matches(
    doc,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    meta = doc.metadata

    if subject:
        wanted_subject = normalize_filter_text(subject)
        actual_subject = normalize_filter_text(meta.get("subject", ""))

        # Special-case broad SQL matching because actual metadata may be
        # "ANSI SQL Using MySQL" while the user/filter says only "SQL".
        if wanted_subject in {"sql", "mysql"}:
            if "sql" not in actual_subject and "mysql" not in actual_subject:
                return False
        elif wanted_subject not in actual_subject and actual_subject not in wanted_subject:
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
    limit: int = TOP_K,
    fetch_k: int = FETCH_K,
):
    """
    Retrieve candidate documents from Chroma with optional metadata filters.

    Backward compatibility:
    - ask mode keeps the default limit=TOP_K behavior.
    - chat mode can request more candidates for re-ranking and grading.
    """
    candidates = vector_store.similarity_search(query, k=fetch_k)

    filtered = [
        doc for doc in candidates
        if metadata_matches(doc, subject=subject, module=module, title=title)
    ]

    if not filtered and any([subject, module, title]):
        warn("No docs matched metadata filters. Falling back to semantic search only.")
        filtered = candidates

    return filtered[:limit]




def retrieval_tokens(text: str) -> set:
    """Tokenize query/document text for local re-ranking and fallback grading."""
    stopwords = {
        "the", "is", "are", "a", "an", "and", "or", "to", "of", "in", "on", "for",
        "with", "as", "by", "this", "that", "it", "be", "been", "being", "from",
        "what", "which", "does", "do", "about", "explain", "describe", "module",
        "topic", "topics", "covered", "important", "list", "show"
    }
    tokens = re.findall(r"[a-zA-Z0-9]+", str(text).lower())
    return {token for token in tokens if len(token) > 2 and token not in stopwords}


def doc_search_text(doc) -> str:
    """Combine content and metadata into one searchable string for local scoring."""
    meta = doc.metadata
    return " ".join([
        str(doc.page_content),
        str(meta.get("file_name", "")),
        str(meta.get("subject", "")),
        str(meta.get("module_title", "")),
        str(meta.get("topics_covered", "")),
        str(meta.get("key_concepts", "")),
        str(meta.get("summary", "")),
    ])


def doc_rerank_score(query: str, doc, subject: Optional[str] = None, module: Optional[str] = None) -> float:
    """
    Local re-ranking score.

    It rewards:
    - query/document token overlap
    - exact phrase hits
    - subject/module metadata matches
    - title/topic metadata hits
    """
    q_tokens = retrieval_tokens(query)
    search_text = doc_search_text(doc)
    search_text_lower = search_text.lower()
    d_tokens = retrieval_tokens(search_text)

    if not q_tokens:
        return 0.0

    overlap = q_tokens.intersection(d_tokens)
    overlap_score = len(overlap) / max(1, len(q_tokens))

    phrase_score = 0.0
    query_lower = query.lower().strip()
    if query_lower and query_lower in search_text_lower:
        phrase_score += 0.40

    for token in q_tokens:
        if token in search_text_lower:
            phrase_score += 0.03

    metadata_boost = 0.0
    meta = doc.metadata

    if subject and metadata_matches(doc, subject=subject):
        metadata_boost += 0.25

    if module and str(module).lower() == str(meta.get("module_number", "")).lower():
        metadata_boost += 0.15

    title_topic_text = " ".join([
        str(meta.get("module_title", "")),
        str(meta.get("topics_covered", "")),
        str(meta.get("key_concepts", "")),
    ]).lower()

    topic_hits = sum(1 for token in q_tokens if token in title_topic_text)
    topic_boost = min(0.25, topic_hits * 0.05)

    return overlap_score + phrase_score + metadata_boost + topic_boost


def rerank_docs(
    query: str,
    docs: list,
    subject: Optional[str] = None,
    module: Optional[str] = None,
) -> list:
    """
    Re-rank retrieved candidates using local lexical + metadata scoring.
    This is fast, quota-free, and runs before optional LLM relevance grading.
    """
    scored = []

    for idx, doc in enumerate(docs):
        score = doc_rerank_score(query, doc, subject=subject, module=module)
        scored.append((score, idx, doc))

    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return [doc for score, idx, doc in scored]


RELEVANCE_GRADING_PROMPT = ChatPromptTemplate.from_template(
    """You are grading whether a retrieved document chunk is relevant to a user's question.

Question:
{question}

Retrieved chunk:
{document}

Return:
- relevant: true only if the chunk directly helps answer the question.
- reason: one short sentence explaining the decision.

Be strict. If the chunk is only loosely related, mark relevant as false.
"""
)


def heuristic_relevance_grade(query: str, doc, subject: Optional[str] = None) -> "RelevanceGrade":
    """Local fallback relevance grade when LLM grading fails or is disabled."""
    score = doc_rerank_score(query, doc, subject=subject)
    relevant = score >= 0.18

    if relevant:
        reason = f"Local score {score:.2f}: chunk overlaps with the query and metadata."
    else:
        reason = f"Local score {score:.2f}: chunk appears weakly related."

    return RelevanceGrade(relevant=relevant, reason=reason)


def grade_single_doc_with_llm(query: str, doc) -> "RelevanceGrade":
    """Ask the local LLM to judge one retrieved chunk for relevance."""
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

    try:
        try:
            structured_llm = llm.with_structured_output(RelevanceGrade, method="json_schema")
        except TypeError:
            structured_llm = llm.with_structured_output(RelevanceGrade)

        chunk_text = clean_preview(doc_search_text(doc), 1800)
        chain = RELEVANCE_GRADING_PROMPT | structured_llm
        return chain.invoke({"question": query, "document": chunk_text})

    except Exception as e:
        warn(f"LLM relevance grading failed for one chunk; using local fallback: {e}")
        return heuristic_relevance_grade(query, doc)


def grade_docs_for_relevance(
    query: str,
    docs: list,
    subject: Optional[str] = None,
    use_llm: bool = ENABLE_LLM_GRADING,
) -> Tuple[list, List[Dict[str, Any]]]:
    """
    CRAG-style relevance grading.

    Steps:
    1. Grade top candidates after re-ranking.
    2. Keep only relevant chunks.
    3. If grading is too strict, keep the best re-ranked chunks as fallback.
    """
    if not docs:
        return [], []

    docs_to_grade = docs[:max(1, min(GRADE_CANDIDATE_LIMIT, len(docs)))]
    kept_docs = []
    grade_report = []

    for idx, doc in enumerate(docs_to_grade, start=1):
        if use_llm:
            grade = grade_single_doc_with_llm(query, doc)
        else:
            grade = heuristic_relevance_grade(query, doc, subject=subject)

        grade_report.append({
            "rank": idx,
            "relevant": bool(grade.relevant),
            "reason": grade.reason,
            "source": doc.metadata.get("file_name", doc.metadata.get("source", "unknown")),
            "page": display_page_number(doc.metadata.get("page", "?")),
        })

        if grade.relevant:
            kept_docs.append(doc)

    # Guardrail: if grading removes too much, preserve the best re-ranked docs.
    if len(kept_docs) < MIN_GRADED_DOCS:
        seen_ids = {id(doc) for doc in kept_docs}
        for doc in docs:
            if id(doc) not in seen_ids:
                kept_docs.append(doc)
                seen_ids.add(id(doc))
            if len(kept_docs) >= MIN_GRADED_DOCS:
                break

    return kept_docs[:TOP_K], grade_report


def retrieve_rerank_and_grade_docs(
    query: str,
    vector_store,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    title: Optional[str] = None,
) -> Tuple[list, Dict[str, Any]]:
    """
    Advanced retrieval pipeline for chat mode:
    candidate retrieval -> local re-ranking -> CRAG-style relevance grading.
    """
    candidate_docs = retrieve_docs(
        query=query,
        vector_store=vector_store,
        subject=subject,
        module=module,
        title=title,
        limit=RERANK_CANDIDATE_LIMIT,
        fetch_k=max(FETCH_K, RERANK_CANDIDATE_LIMIT),
    )

    reranked_docs = rerank_docs(query, candidate_docs, subject=subject, module=module)
    graded_docs, grade_report = grade_docs_for_relevance(query, reranked_docs, subject=subject)

    stats = {
        "candidates": len(candidate_docs),
        "reranked": len(reranked_docs),
        "graded_relevant": len(graded_docs),
        "grade_report": grade_report,
    }

    return graded_docs[:TOP_K], stats


def format_docs_for_prompt(docs) -> str:
    blocks = []

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        header = (
            f"[Source {i}: {meta.get('file_name', meta.get('source', 'unknown'))}, "
            f"page={display_page_number(meta.get('page', 'unknown'))}, "
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
        page = display_page_number(meta.get("page", "unknown"))
        subject = meta.get("subject", "")
        module = meta.get("module_number", "")
        title = meta.get("module_title", "")

        print(
            f"{i}. {source} | page={page} | "
            f"subject={subject} | module={module} | title={clean_preview(clean_display_text(title), 70)}"
        )
        print(f"   Preview: {clean_preview(doc.page_content, 180)}")


# ============================================================
# NEW SECTION — CLAIM-LEVEL CITATION + TOPIC ANSWER MODE
# ============================================================
# Claim-Level Citation:
# - Breaks answers into factual claims.
# - Maps every shown claim to a real retrieved source.
# - Repairs weak/invalid source numbers using local token matching.
# - Hides low-confidence claims from public output.
#
# Topic Answer Mode:
# - For "topics covered" style questions, answers directly from parsed metadata.
# - This avoids weak LLM claims and gives a fuller document-grounded topic list.

class Claim(BaseModel):
    """A single factual claim with its supporting source."""
    claim_text: str = Field(description="The specific factual statement, in plain language.")
    source_number: int = Field(
        description="Which numbered source (1, 2, 3...) from the context supports this claim."
    )
    confidence: str = Field(
        description="'high' if the source directly states this, 'medium' if it's a reasonable "
                    "inference, 'low' if weakly supported."
    )


class CitedAnswer(BaseModel):
    """A full answer broken into individually-cited claims."""
    claims: List[Claim] = Field(
        description="List of claims that together form the full answer. Empty list if nothing relevant was found."
    )
    overall_summary: str = Field(description="A one or two line summary tying the claims together.")


CLAIM_EXTRACTION_PROMPT = ChatPromptTemplate.from_template(
    """You are answering a question using ONLY the numbered sources below.

There are exactly {num_sources} numbered sources.
For every claim, source_number MUST be an integer between 1 and {num_sources}.
If you are not sure which source supports a claim, do not include that claim.

Break your answer into separate factual claims. For EACH claim:
- State the claim clearly and concisely.
- Identify EXACTLY which source number supports it.
- Rate confidence as: high or medium.
- Do NOT include low-confidence claims.

Rules:
- Do not use source numbers outside the valid range.
- Do not include unsupported claims.
- Do not include low-confidence claims in the final answer.
- Only include claims that directly answer the user's question.
- Do not invent facts outside the sources.
- If nothing in the sources answers the question, return an empty claims list.
- overall_summary must be a non-empty 1-2 sentence summary if claims exist.

Sources:
{context}

Question: {question}
"""
)


def citation_tokens(text: str) -> set:
    """
    Convert text into useful comparison tokens.
    Used for source repair, duplicate removal, and topic filtering.
    """
    stopwords = {
        "the", "is", "are", "a", "an", "and", "or", "to", "of", "in", "on", "for",
        "with", "as", "by", "this", "that", "it", "be", "been", "being", "from",
        "topic", "topics", "covered", "discussed", "module", "exercise", "exercises",
        "including", "include", "includes", "also", "well", "question", "answer",
        "explain", "cover", "covers", "covered", "list", "show", "tell"
    }

    tokens = re.findall(r"[a-zA-Z0-9]+", str(text).lower())
    return {token for token in tokens if len(token) > 2 and token not in stopwords}


def claim_key(text: str) -> str:
    """Normalize a claim for duplicate removal."""
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def score_claim_against_doc(claim_text: str, doc) -> float:
    """
    Score how well a claim matches a retrieved document chunk.
    Higher score means the claim is more likely supported by that source.
    """
    claim_set = citation_tokens(claim_text)

    if not claim_set:
        return 0.0

    meta = doc.metadata
    searchable_text = " ".join([
        str(doc.page_content),
        str(meta.get("subject", "")),
        str(meta.get("module_title", "")),
        str(meta.get("topics_covered", "")),
        str(meta.get("key_concepts", "")),
        str(meta.get("summary", "")),
    ])

    doc_set = citation_tokens(searchable_text)

    if not doc_set:
        return 0.0

    overlap = claim_set.intersection(doc_set)
    return len(overlap) / max(1, len(claim_set))


def find_best_source_index_for_claim(claim_text: str, docs: list) -> Optional[int]:
    """
    Find the best supporting source for a claim using local token-overlap matching.
    """
    best_idx = None
    best_score = 0.0

    for idx, doc in enumerate(docs):
        score = score_claim_against_doc(claim_text, doc)

        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is not None and best_score >= 0.20:
        return best_idx

    return None


def resolve_claim_source_index(claim: "Claim", docs: list):
    """
    Resolve a claim's source index safely.

    Priority:
    1. Use model-provided source_number if it is valid and reasonably matching.
    2. Repair using local token matching if source_number is invalid/weak.
    3. Drop unresolved claims instead of printing unknown source.
    """
    if not docs:
        return None, "unresolved"

    direct_idx = None

    try:
        direct_idx = int(claim.source_number) - 1
    except Exception:
        direct_idx = None

    best_idx = find_best_source_index_for_claim(claim.claim_text, docs)

    if direct_idx is not None and 0 <= direct_idx < len(docs):
        direct_score = score_claim_against_doc(claim.claim_text, docs[direct_idx])

        if best_idx is None:
            return direct_idx, "model"

        best_score = score_claim_against_doc(claim.claim_text, docs[best_idx])

        if direct_score >= 0.20 and direct_score >= best_score - 0.10:
            return direct_idx, "model"

        return best_idx, "matched"

    if best_idx is not None:
        return best_idx, "matched"

    return None, "unresolved"


def split_metadata_items(value: Any) -> List[str]:
    """Split Chroma-safe metadata strings back into a clean list."""
    if not value:
        return []

    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = re.split(r"\s*\|\s*", str(value))

    items = []
    seen = set()

    for item in raw_items:
        item = clean_preview(item, 160).strip(" -•\t\n")
        if not item:
            continue

        key = item.lower()
        if key not in seen:
            seen.add(key)
            items.append(item)

    return items


def is_topic_style_question(original_query: str, semantic_query: str) -> bool:
    """Return True for questions that are asking what a module/document covers."""
    q = f"{original_query} {semantic_query}".lower()
    return any(
        phrase in q
        for phrase in [
            "topic", "topics", "covered", "covers",
            "syllabus", "what does", "what are covered",
        ]
    )


def topic_relevance_score(item: str, query: str) -> float:
    """Score a metadata topic/key-concept against the question."""
    item_tokens = citation_tokens(item)
    query_tokens = citation_tokens(query)

    if not item_tokens or not query_tokens:
        return 0.0

    overlap = item_tokens.intersection(query_tokens)
    return len(overlap) / max(1, min(len(item_tokens), len(query_tokens)))


def collect_topic_items_from_docs(docs: list, query: str):
    """
    Collect topics/key concepts from retrieved docs.

    For broad "topics covered" questions, returns full module topic coverage.
    For specific questions like "events covered", prefers matching items.
    """
    candidates = []
    seen = set()

    for doc in docs:
        meta = doc.metadata

        source_label = {
            "source_name": meta.get("file_name", meta.get("source", "unknown")),
            "page": meta.get("page", "?"),
            "subject": meta.get("subject", ""),
            "module": meta.get("module_number", ""),
            "title": meta.get("module_title", ""),
        }

        for field in ["topics_covered", "key_concepts", "learning_objectives"]:
            for item in split_metadata_items(meta.get(field, "")):
                item = re.sub(r"^Understand and practice\s+", "", item, flags=re.IGNORECASE).strip(". ")

                key = item.lower()
                if key in seen:
                    continue

                score = topic_relevance_score(item, query)
                seen.add(key)
                candidates.append((item, score, source_label))

    if not candidates:
        return []

    q = query.lower()
    broad_topic_query = any(word in q for word in ["topic", "topics", "syllabus"]) and not any(
        word in q for word in ["form", "forms", "semantic", "event", "events", "join", "joins", "grid"]
    )

    if broad_topic_query:
        filtered = candidates
    else:
        filtered = [c for c in candidates if c[1] > 0]
        if not filtered:
            filtered = candidates

    filtered = sorted(filtered, key=lambda x: x[1], reverse=True)
    return filtered[:12]


def print_topic_answer_from_metadata(original_query: str, parsed: "CourseQuery", docs: list) -> bool:
    """
    Deterministic answer path for topic/coverage questions.

    This is intentionally not fully LLM-based because "what topics are covered"
    questions are better answered from parsed document metadata.
    """
    if not docs:
        return False

    if not is_topic_style_question(original_query, parsed.semantic_query):
        return False

    topic_items = collect_topic_items_from_docs(
        docs=docs,
        query=f"{original_query} {parsed.semantic_query}",
    )

    if not topic_items:
        return False

    subject = parsed.subject or docs[0].metadata.get("subject", "the selected")
    module = parsed.module or docs[0].metadata.get("module_number", "")

    print("\n🎯 DOCUMENT-GROUNDED TOPIC ANSWER")
    print("-" * 72)

    module_text = f" Module {module}" if module else ""
    print(
        f"\n🧠 Summary\nThe retrieved sources indicate that{module_text} "
        f"{subject} covers the following relevant topics/concepts."
    )

    print("\n📌 Topics / Concepts Found\n")

    for idx, (item, score, source_label) in enumerate(topic_items, start=1):
        print(f"{idx}. {clean_display_text(item)}")
        print(
            f"   🟢 Source: {source_label['source_name']} "
            f"(page {display_page_number(source_label['page'])}) | subject={clean_display_text(source_label['subject'])} | "
            f"module={source_label['module']} | confidence=metadata"
        )
        if source_label.get("title"):
            print(f"   Title: {clean_preview(clean_display_text(source_label['title']), 90)}")
        print()

    return True


def generate_cited_answer(query: str, docs: list) -> Optional["CitedAnswer"]:
    """
    Generate an answer where every claim is mapped to a specific source.
    Returns None if no documents were retrieved, or if structured output fails.
    """
    if not docs:
        return None

    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

    try:
        try:
            structured_llm = llm.with_structured_output(CitedAnswer, method="json_schema")
        except TypeError:
            structured_llm = llm.with_structured_output(CitedAnswer)

        context = format_docs_for_prompt(docs)
        chain = CLAIM_EXTRACTION_PROMPT | structured_llm

        return chain.invoke({
            "context": context,
            "question": query,
            "num_sources": len(docs),
        })

    except Exception as e:
        warn(f"Claim-level citation failed, falling back to plain answer: {e}")
        return None


def print_cited_answer(cited_answer: "CitedAnswer", docs: list):
    """
    Print final citation-backed answer in a clean public-demo style.
    """
    shown_claims = []
    seen_claims = set()

    for claim in cited_answer.claims:
        source_idx, source_method = resolve_claim_source_index(claim, docs)

        if source_idx is None:
            continue

        confidence = str(claim.confidence).lower().strip()

        # Hide weak/noisy claims from final public output.
        if confidence == "low":
            continue

        key = claim_key(claim.claim_text)
        if key in seen_claims:
            continue

        seen_claims.add(key)
        shown_claims.append((claim, source_idx, source_method, confidence))

    print("\n🎯 CITATION-BACKED ANSWER")
    print("-" * 72)

    summary = str(cited_answer.overall_summary or "").strip()

    if not summary and shown_claims:
        summary = "The retrieved sources support the following verified points from the documents."

    if summary:
        print(f"\n🧠 Summary\n{clean_preview(summary, 600)}")
    else:
        print("\n🧠 Summary\nNo supported summary could be generated from the retrieved sources.")

    if not shown_claims:
        print("\n⚠️ No supported claims found in the retrieved sources.")
        return

    print("\n📌 Verified Claims\n")

    for idx, (claim, source_idx, source_method, confidence) in enumerate(shown_claims, start=1):
        source_meta = docs[source_idx].metadata
        source_name = source_meta.get("file_name", "unknown")
        page = display_page_number(source_meta.get("page", "?"))
        subject = source_meta.get("subject", "")
        module = source_meta.get("module_number", "")
        title = source_meta.get("module_title", "")

        confidence_icon = {
            "high": "🟢",
            "medium": "🟡",
        }.get(confidence, "⚪")

        source_note = ""
        if source_method == "matched":
            source_note = " | source matched locally"

        print(f"{idx}. {claim.claim_text}")
        print(
            f"   {confidence_icon} Source: {source_name} "
            f"(page {page}) | subject={clean_display_text(subject)} | module={module} | "
            f"confidence={confidence}{source_note}"
        )

        if title:
            print(f"   Title: {clean_preview(clean_display_text(title), 90)}")

        print()


def print_question_suggestions():
    """
    Print document-grounded test questions from parsed metadata.
    This helps users choose questions that the PDFs can actually answer.
    """
    section("DOCUMENT-GROUNDED QUESTION SUGGESTIONS")
    print("Use these questions because they are generated from your PDFs/metadata.\n")

    try:
        pdfs = get_pdf_files()
    except FileNotFoundError as e:
        warn(str(e))
        return

    for pdf in pdfs:
        meta = load_metadata_json(pdf)
        if not meta.get("Subject"):
            meta = build_course_metadata(pdf)

        subject = str(meta.get("Subject", "")).strip()
        module = str(meta.get("ModuleNumber", "")).strip()
        title = str(meta.get("ModuleTitle", "")).strip()

        print(f"\n📄 {pdf.name}")
        info("Subject", subject)
        info("Module", module or "N/A")
        info("Title", clean_preview(title, 100))

        topics = meta.get("TopicsCovered", []) or meta.get("KeyConcepts", [])
        if not topics:
            topics = subject_key_concepts(subject)

        print("\nSuggested questions:")

        if subject:
            print(f"  1. What topics are covered in the {subject} module?")
            print(f"  2. List the important topics in {subject}.")

        if module and subject:
            print(f"  3. What topics are covered in Module {module} for {subject}?")

        for idx, topic in enumerate(topics[:5], start=4):
            print(f"  {idx}. Explain {topic} based on the documents.")

    print("\nTip: In chat mode, prefer questions about listed topics/concepts. "
          "If a topic is not present in these suggestions, the answer may correctly say it is not supported.")


# ============================================================
# CLI ACTIONS
# ============================================================

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
    print("Tip: ask naturally, e.g. 'What are selectors?' or 'Explain the Bootstrap grid system.' — routing, re-ranking, and grading run automatically.\n")

    while True:
        query = input("❓ Question: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting.")
            break

        if not query:
            continue

        # --- Query Construction step ---
        parsed = parse_natural_query(query)

        # --- Query Routing step ---
        # If Query Construction cannot detect a subject, infer it from topic words.
        routing_decision = apply_query_routing(parsed, query)

        print(f"   → Detected subject: {parsed.subject} | module: {parsed.module} | "
              f"semantic_query: '{parsed.semantic_query}'")

        if routing_decision:
            print(
                f"   → Query routed to: {routing_decision['subject']} "
                f"(matched: {routing_decision['reason']})"
            )

        # --- Advanced Retrieval step ---
        # Chat mode retrieves more candidates, re-ranks them, then grades relevance.
        docs, retrieval_stats = retrieve_rerank_and_grade_docs(
            query=parsed.semantic_query,
            vector_store=vector_store,
            subject=parsed.subject,
            module=parsed.module,
        )
        print(
            f"   → Retrieval pipeline: candidates={retrieval_stats['candidates']} | "
            f"reranked={retrieval_stats['reranked']} | "
            f"kept_after_grading={retrieval_stats['graded_relevant']}"
        )

        # --- Deterministic topic-answer path ---
        # For "what topics are covered" style questions, metadata gives a more
        # complete and reliable answer than free-form LLM claim generation.
        if print_topic_answer_from_metadata(query, parsed, docs):
            print("\n" + "-" * 72 + "\n")
            continue

        # --- Claim-Level Citation step ---
        cited_answer = generate_cited_answer(parsed.semantic_query, docs)

        if cited_answer is not None:
            print_cited_answer(cited_answer, docs)
        else:
            # Fallback to the original plain-answer path if structured output failed
            answer, docs = answer_question(
                parsed.semantic_query, vector_store, subject=parsed.subject, module=parsed.module
            )
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
    sub.add_parser("suggest", help="Show document-grounded questions generated from parsed metadata")

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

    elif args.command == "suggest":
        print_question_suggestions()


if __name__ == "__main__":
    main()