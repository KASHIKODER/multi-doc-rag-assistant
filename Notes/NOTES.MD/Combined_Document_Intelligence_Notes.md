# Combined Document Intelligence — Complete Professional Notes
> `combined_document_intelligence.py` — Course Module Version  
> Covers: Architecture → Imports → Config → Every Function → CLI → Flow

---

## TABLE OF CONTENTS

1. [System Architecture — Big Picture](#1-system-architecture--big-picture)
2. [What This System Does (Plain English)](#2-what-this-system-does-plain-english)
3. [Imports & Dependencies](#3-imports--dependencies)
4. [ENV + CONFIG — All Constants Explained](#4-env--config--all-constants-explained)
5. [Display Helpers](#5-display-helpers)
6. [Course Module Metadata Parser (LOCAL — No Groq)](#6-course-module-metadata-parser-local--no-groq)
7. [RAG Ingestion — PDFs + Metadata → Chroma Vector DB](#7-rag-ingestion--pdfs--metadata--chroma-vector-db)
8. [Question Answering — Chroma → Ollama](#8-question-answering--chroma--ollama)
9. [CLI — Command Line Interface](#9-cli--command-line-interface)
10. [main() — Entry Point](#10-main--entry-point)
11. [Complete Data Flow Diagrams](#11-complete-data-flow-diagrams)
12. [Command Cheat Sheet](#12-command-cheat-sheet)

---

## 1. System Architecture — Big Picture

```
SYSTEM: Combined Document Intelligence (Course Module Version)
══════════════════════════════════════════════════════════════

STAGE 1 — PARSE (Local, No API Cost)
┌─────────────┐      regex + PyPDF2       ┌──────────────────────┐
│  PDF Files  │  ──────────────────────►  │  JSON Metadata Files │
│  (data/)    │                           │  (data/extracted_    │
└─────────────┘                           │   metadata/*.json)   │
                                          └──────────────────────┘

STAGE 2 — INGEST (Local, No API Cost)
┌─────────────┐   LangChain PyPDFLoader   ┌───────────────┐
│  PDF Files  │  ──────────────────────►  │  Page chunks  │
└─────────────┘                           └──────┬────────┘
                                                 │ metadata attached
┌──────────────────────┐                         │
│  JSON Metadata Files │  ──────────────────────►│
└──────────────────────┘                         │
                                                 ▼
                                     ┌────────────────────────┐
                                     │  HuggingFace Embeddings │
                                     │ (all-MiniLM-L6-v2)     │
                                     └──────────┬─────────────┘
                                                │
                                                ▼
                                     ┌──────────────────────┐
                                     │    Chroma Vector DB   │
                                     │     (chroma_db/)      │
                                     └──────────────────────┘

STAGE 3 — ASK / CHAT (Local Ollama — No API Cost)
┌───────────────┐  similarity_search   ┌──────────────────────┐
│  User Query   │ ───────────────────► │  Chroma Vector DB    │
└───────────────┘                      └──────────┬───────────┘
                                                  │ Top K chunks
                                                  ▼
                                       ┌──────────────────────┐
                                       │  ChatOllama (llama3)  │
                                       │  + Prompt Template   │
                                       └──────────┬───────────┘
                                                  │
                                                  ▼
                                         ┌────────────────┐
                                         │  Final Answer  │
                                         │  + Sources     │
                                         └────────────────┘
```

**Core Insight:** This system chains 3 independent stages. Stage 1 (Parse) and Stage 2 (Ingest) are one-time setup operations. Stage 3 (Ask/Chat) is what the user uses repeatedly — all powered by a local LLM, so zero API cost at query time.

---

## 2. What This System Does (Plain English)

### Problem it solves:
Tere paas multiple course PDFs hain — `Module 1-CSS3.pdf`, `Module 1-Bootstrap5.pdf`, etc. Tu inpe questions puchna chahta hai. Normal PDF reader se ye nahi hoga. Ye system ek intelligent Q&A engine banata hai un PDFs ke upar.

### How it works in simple steps:

| Step | What happens | Tool used |
|------|-------------|-----------|
| 1 | PDFs se subject, topics, objectives nikalo | PyPDF2 + Regex (Local) |
| 2 | PDFs ko chunks mein todo aur metadata attach karo | LangChain |
| 3 | Chunks ko numbers (vectors) mein convert karo | HuggingFace Embeddings |
| 4 | Vectors ko database mein store karo | Chroma DB |
| 5 | Question aane pe relevant chunks dhundo | Cosine Similarity |
| 6 | Local LLM se answer generate karo | Ollama (llama3) |

---

## 3. Imports & Dependencies

```python
import argparse        # CLI banane ke liye (parse/ingest/ask/chat commands)
import json            # JSON read/write ke liye (metadata files)
import logging         # Log level control ke liye (warnings suppress)
import os              # Environment variables access ke liye
import re              # Regular expressions — text se patterns nikalne ke liye
import shutil          # Folder delete ke liye (Chroma DB rebuild)
import warnings        # Python warnings suppress ke liye
from pathlib import Path          # Cross-platform file paths (Windows/Linux dono chalega)
from typing import Any, Dict, List, Optional  # Type hints — code readable banane ke liye
```

### Third-party imports:
```python
from dotenv import load_dotenv
# .env file se GROQ_API_KEY, OLLAMA_MODEL etc. load karta hai

from PyPDF2 import PdfReader
# PDF ke pages se raw text extract karna — Stage 1 (Parse) mein use hota hai
# Ye Groq/OpenAI nahi use karta, purely local

from langchain_community.document_loaders import PyPDFLoader
# LangChain ka PDF loader — Stage 2 (Ingest) mein use hota hai
# Ye Document objects banata hai jinpe metadata attach hoti hai

from langchain_text_splitters import RecursiveCharacterTextSplitter
# Long documents ko chunks mein kaat-ta hai
# Recursive matlab: pehle '\n\n' pe split, phir '\n', phir ' ', phir char-by-char

from langchain_huggingface import HuggingFaceEmbeddings
# Text → numerical vectors (embeddings) convert karta hai
# Model: all-MiniLM-L6-v2 (lightweight, fast, offline chalega)

from langchain_chroma import Chroma
# Vector database — embeddings store karta hai, similarity search karta hai

from langchain_ollama import ChatOllama
# Local Ollama LLM se baat karne ka interface (llama3 model)

from langchain_core.prompts import ChatPromptTemplate
# Prompt template banane ke liye — structured way to define system/user messages

from langchain_core.output_parsers import StrOutputParser
# LLM response ko plain string mein convert karta hai
```

### Warning Suppression:
```python
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*langchain-community.*")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*HF Hub.*")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
```
**Kyun?** HuggingFace, LangChain libraries bahut saari unnecessary warnings print karti hain. User ko clean output dikhe isliye sab suppress kar diya. Errors tab bhi dikhenge (logging.ERROR level), warnings nahi.

---

## 4. ENV + CONFIG — All Constants Explained

```python
load_dotenv()
# .env file padhta hai — GROQ_API_KEY, OLLAMA_MODEL, DATA_DIR etc.
```

```python
DATA_DIR    = Path(os.getenv("DATA_DIR",    "./data"))
CHROMA_DIR  = Path(os.getenv("CHROMA_DIR",  "./chroma_db"))
METADATA_DIR = Path(os.getenv("METADATA_DIR", "./data/extracted_metadata"))
```
| Variable | Default | Purpose |
|----------|---------|---------|
| `DATA_DIR` | `./data` | Yahan teri PDF files honi chahiye |
| `CHROMA_DIR` | `./chroma_db` | Chroma vector DB yahan store hoti hai |
| `METADATA_DIR` | `./data/extracted_metadata` | Parser ke JSON files yahan save hote hain |

```python
COLLECTION_NAME  = os.getenv("COLLECTION_NAME", "combined_docs")
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "llama3")
```
| Variable | Default | Purpose |
|----------|---------|---------|
| `COLLECTION_NAME` | `combined_docs` | Chroma DB ke andar ye collection naam se data store hoga |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Text ko vectors mein convert karne wala model (HuggingFace) |
| `OLLAMA_MODEL` | `llama3` | Local LLM jo answers generate karta hai |

```python
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE",    "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K         = int(os.getenv("TOP_K",         "4"))
FETCH_K       = int(os.getenv("FETCH_K",       "12"))
```
| Variable | Default | Purpose |
|----------|---------|---------|
| `CHUNK_SIZE` | 1000 | Ek chunk mein max 1000 characters |
| `CHUNK_OVERLAP` | 200 | Adjacent chunks ke beech 200 characters overlap hoga (context preserve) |
| `TOP_K` | 4 | Answer generate karne ke liye top 4 chunks use hote hain |
| `FETCH_K` | 12 | Similarity search mein pehle 12 candidates fetch hote hain, phir filter |

**CHUNK_OVERLAP kyun?**
```
Without overlap:        With overlap (200 chars):
[chunk1: 0-1000]       [chunk1: 0-1000]
[chunk2: 1000-2000]    [chunk2: 800-1800]  ← 200 chars repeat
[chunk3: 2000-3000]    [chunk3: 1600-2600]

Agar koi important sentence chunk ke end mein aadhi cut gayi → overlap se
woh sentence next chunk mein bhi rahegi → retrieval miss nahi hoga
```

```python
os.environ["TOKENIZERS_PARALLELISM"]      = os.getenv("TOKENIZERS_PARALLELISM", "false")
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = os.getenv("HF_HUB_DISABLE_PROGRESS_BARS", "1")
```
- `TOKENIZERS_PARALLELISM=false` → HuggingFace tokenizer deadlock warning avoid karta hai
- `HF_HUB_DISABLE_PROGRESS_BARS=1` → Model download progress bar hide karta hai (cleaner output)

```python
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
```
**Ye ek fallback template hai.** Jab bhi kisi PDF ka metadata load karna ho aur file exist na kare ya corrupt ho — ye default dict use hota hai. Iska matlab system crash nahi karega, empty fields ke saath chalega.

---

## 5. Display Helpers

Ye functions sirf pretty terminal output ke liye hain — koi logic nahi:

```python
def section(title: str):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
# Output:
# ========================================================================
# COURSE MODULE PARSING — PDF TO JSON METADATA
# ========================================================================
```

```python
def status(label: str, value: str):
    print(f"✅ {label}: {value}")
# Output: ✅ Metadata saved: ./data/extracted_metadata/Module1-CSS3.json
```

```python
def info(label: str, value: str):
    print(f"• {label}: {value}")
# Output: • Subject: CSS3
```

```python
def warn(message: str):
    print(f"⚠️ {message}")
# Output: ⚠️ No docs matched metadata filters. Falling back to semantic search only.
```

```python
def clean_preview(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()  # multiple spaces/newlines → single space
    return text if len(text) <= limit else text[:limit].rstrip() + "..."
```
**Purpose:** Long text ko terminal pe cleanly print karna. Extra whitespace hatata hai, aur agar text limit se zyada lamba ho toh `...` lagata hai.

```python
def ensure_folders():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
```
`parents=True` → nested directories bana dega agar na ho  
`exist_ok=True` → already exist kare toh error nahi dega

```python
def get_pdf_files() -> List[Path]:
    ensure_folders()
    pdfs = sorted(DATA_DIR.glob("*.pdf"))  # data/ folder mein saari .pdf files
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in '{DATA_DIR}'. Add PDFs first.")
    return pdfs
```
`sorted()` → alphabetical order mein — consistent order important hai taaki har run pe same sequence mile.

---

## 6. Course Module Metadata Parser (LOCAL — No Groq)

**Goal:** PDF file ka naam aur content padhke automatically metadata nikalna — subject, topics, learning objectives, summary — bina kisi API call ke.

---

### 6.1 `extract_text_from_pdf(pdf_path, max_pages=None)`

```python
def extract_text_from_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> str:
    reader = PdfReader(str(pdf_path))   # PyPDF2 reader object
    pages = []

    total = len(reader.pages)
    limit = min(total, max_pages) if max_pages else total  # agar max_pages diya ho toh limit karo

    for idx in range(limit):
        try:
            text = reader.pages[idx].extract_text() or ""   # page se text nikalo
            pages.append(f"\n\n--- PAGE {idx + 1} ---\n{text}")
        except Exception as e:
            warn(f"Could not extract page {idx + 1} from {pdf_path.name}: {e}")

    return "\n".join(pages)
```

**Key Points:**
- PyPDF2 ka `extract_text()` kuch PDFs pe fail ho sakta hai (scanned images, encrypted) — isliye try/except
- `or ""` → agar text None return ho toh empty string le lo
- Parse step mein sirf pehle 3 pages chahiye (`max_pages=3`) kyunki course outline usually starting mein hoti hai
- RAG mein PyPDFLoader use hota hai (ye function nahi) — ye sirf parser ke liye hai

---

### 6.2 `metadata_path_for(pdf_path)`

```python
def metadata_path_for(pdf_path: Path) -> Path:
    return METADATA_DIR / f"{pdf_path.stem}.json"
```

`pdf_path.stem` → filename bina extension ke  
Example: `Module 1-CSS3.pdf` → stem = `Module 1-CSS3` → JSON: `data/extracted_metadata/Module 1-CSS3.json`

---

### 6.3 `guess_module_number(filename)`

```python
def guess_module_number(filename: str) -> str:
    match = re.search(r"module\s*(\d+)", filename, flags=re.IGNORECASE)
    return match.group(1) if match else ""
```

**Regex breakdown:** `r"module\s*(\d+)"`
- `module` → literal word "module"
- `\s*` → zero ya zyada spaces (Module1 ya Module 1 dono match)
- `(\d+)` → ek ya zyada digits — ye capture group hai
- `re.IGNORECASE` → Module/MODULE/module sab match

Example:
```
"Module 1-CSS3.pdf"   → match.group(1) = "1"
"module3-html.pdf"    → match.group(1) = "3"
"Bootstrap5.pdf"      → koi match nahi → ""
```

---

### 6.4 `guess_subject_from_filename(filename)`

```python
def guess_subject_from_filename(filename: str) -> str:
    stem = Path(filename).stem           # "Module 1-Bootstrap5"
    if "-" in stem:
        subject = stem.split("-", 1)[1]  # Split at first "-": ["Module 1", "Bootstrap5"]
                                         # [1] → "Bootstrap5"
    else:
        subject = re.sub(r"module\s*\d+", "", stem, flags=re.IGNORECASE)
        # "module1bootstrap5" → "" + "bootstrap5" → "bootstrap5"

    subject = subject.replace("_", " ").strip()  # underscore → space, trim
    subject = re.sub(r"\s+", " ", subject)        # multiple spaces → single space
    return subject
```

Example:
```
"Module 1-Bootstrap5.pdf" → stem="Module 1-Bootstrap5" → has "-" → split → "Bootstrap5"
"Module1-CSS3.pdf"        → stem="Module1-CSS3"         → has "-" → split → "CSS3"
"HTML5module2.pdf"        → no "-" → regex removes "module2" → "HTML5"
```

---

### 6.5 `first_meaningful_line(text)`

```python
def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 5 and not line.startswith("--- PAGE"):
            return line   # Pehli valid line milte hi return
    return ""
```

**Purpose:** PDF ke extracted text mein pehli valid line dhundna jo module ka title ho sake.  
- 5+ characters chahiye (single words skip)
- `--- PAGE 1 ---` jaise artificial markers skip
- Ye `ModuleTitle` set karne ke liye use hota hai

---

### 6.6 `extract_numbered_topics(text)` ⭐ Most Complex Function

```python
def extract_numbered_topics(text: str) -> List[str]:
    topics = []

    # METHOD 1: Line-by-line parsing
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())    # normalize whitespace
        match = re.match(r"^(\d{1,2})\.\s+(.{4,100})$", line)
        # Pattern: starts with 1-2 digit number, dot, space, then 4-100 char text
        # Example: "1. Why CSS?" or "18. Bootstrap 5 JavaScript Plugins"
        if match:
            candidate = match.group(2).strip()
            candidate = re.split(r"\s+Exercise\s+\d", candidate)[0].strip()
            # Remove exercise numbers if attached: "Why CSS? Exercise 1" → "Why CSS?"
            if 4 <= len(candidate) <= 100:
                topics.append(candidate)

    # METHOD 2: If PDF merged lines (line-wise failed with < 3 results)
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

    return unique[:20]   # Max 20 topics return karo
```

**Why two methods?**
- PDF text extraction ka behavior inconsistent hai
- Kuch PDFs mein lines properly separate hoti hain → Method 1 kaam karta hai
- Kuch PDFs mein text ek badi string mein merge ho jaata hai → Method 2 (broader regex) kaam karta hai

**Method 2 Regex explained:** `r"(?:^|\s)(\d{1,2})\.\s+([A-Z][A-Za-z0-9 &:/,()\-]+?)(?=...)"`
- `(?:^|\s)` → line start ya whitespace (non-capturing group)
- `(\d{1,2})` → 1-2 digit number
- `\.\s+` → dot followed by spaces
- `([A-Z][A-Za-z0-9 &:/,()\-]+?)` → Starts with Capital letter, then any valid chars (lazy)
- `(?=...)` → Lookahead: ends before "Exercise N" or another numbered topic or newline

**De-duplication logic:**
```python
seen = set()   # lowercase keys store karo
unique = []    # original case mein topics
for topic in topics:
    key = topic.lower()   # "Why CSS?" → "why css?"
    if key not in seen:   # pehli baar aa raha hai?
        seen.add(key)     # mark as seen
        unique.append(topic)  # add karo original case mein
# Result: case-insensitive duplicates remove, order preserved
```

---

### 6.7 `subject_key_concepts(subject)`

```python
def subject_key_concepts(subject: str) -> List[str]:
    s = subject.lower()   # case-insensitive comparison

    if "bootstrap" in s:
        return ["Bootstrap setup", "Containers and rows", "Responsive grid system", ...]
    if "css" in s:
        return ["CSS syntax", "Selectors", "Colors and backgrounds", ...]
    if "html" in s:
        return [...]
    if "javascript" in s or "java script" in s:
        return [...]
    if "sql" in s or "mysql" in s:
        return [...]

    return []   # Unknown subject → empty list
```

**Purpose:** Ye hardcoded knowledge hai — manual list of key concepts per subject. Jab PDF se automatically topics extract nahi ho pate, ya concept list ko enrich karna ho.

**Subject matching:** `"bootstrap" in s` → partial match (Bootstrap5, Bootstrap 5, Bootstrap CSS sab match karenge)

---

### 6.8 `build_course_metadata(pdf_path)` ⭐ Main Parser Function

```python
def build_course_metadata(pdf_path: Path) -> Dict[str, Any]:
    # Step 1: PDF se raw text nikalo (sirf pehle 3 pages)
    text = extract_text_from_pdf(pdf_path, max_pages=3)
    
    # Step 2: Filename se subject aur module number guess karo
    subject = guess_subject_from_filename(pdf_path.name)
    module_number = guess_module_number(pdf_path.name)
    
    # Step 3: Text se specific data nikalo
    first_line = first_meaningful_line(text)
    topics = extract_numbered_topics(text)
    key_concepts = subject_key_concepts(subject)
    
    # Step 4: ModuleTitle determine karo
    if first_line and len(first_line) < 120:
        module_title = first_line          # PDF ka actual title prefer karo
    else:
        module_title = f"{subject} Module" # Fallback
    
    # Step 5: Agar PDF se topics nahi nikle, key_concepts se fill karo
    if not topics and key_concepts:
        topics = key_concepts
    
    # Step 6: LearningObjectives generate karo topics se
    learning_objectives = [
        f"Understand and practice {topic.lower()}."
        for topic in topics[:8]   # Max 8 objectives
    ]
    
    # Step 7: Summary generate karo
    if topics:
        summary = (
            f"This module focuses on {subject}. It covers topics such as "
            f"{', '.join(topics[:6])}."   # First 6 topics mention karo
        )
    else:
        summary = f"This module focuses on {subject}."
    
    # Final dict return karo
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
```

**Flow visualization:**
```
pdf_path: "data/Module 1-CSS3.pdf"
                    │
    ┌───────────────┼──────────────────┐
    │               │                  │
    ▼               ▼                  ▼
extract_text    guess_subject    guess_module_number
(3 pages)       → "CSS3"         → "1"
    │
    ├── first_meaningful_line → "CSS3 Complete Guide"
    ├── extract_numbered_topics → ["Why CSS?", "Selectors", ...]
    └── subject_key_concepts → ["CSS syntax", "Box model", ...]
                    │
                    ▼
         build final metadata dict
                    │
                    ▼
        save as JSON → data/extracted_metadata/Module 1-CSS3.json
```

---

### 6.9 `save_metadata_json(pdf_path, metadata)`

```python
def save_metadata_json(pdf_path: Path, metadata: Dict[str, Any]):
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    path = metadata_path_for(pdf_path)                              # path compute karo
    path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),         # dict → JSON string
        encoding="utf-8"
    )
    status("Metadata saved", str(path))
```

`json.dumps(metadata, indent=2)` → pretty-print JSON (2-space indent)  
`ensure_ascii=False` → Unicode characters (Hindi etc.) bhi properly save hon  

**Output file example:**
```json
{
  "DocumentType": "course_module",
  "ModuleTitle": "CSS3 Complete Guide",
  "Subject": "CSS3",
  "ModuleNumber": "1",
  "TopicsCovered": ["Why CSS?", "Selectors", "Colors and backgrounds"],
  "LearningObjectives": ["Understand and practice why css?.", ...],
  "KeyConcepts": ["CSS syntax", "Selectors", "Box model", ...],
  "Summary": "This module focuses on CSS3. It covers topics such as Why CSS?, ..."
}
```

---

### 6.10 `load_metadata_json(pdf_path)`

```python
def load_metadata_json(pdf_path: Path) -> Dict[str, Any]:
    path = metadata_path_for(pdf_path)
    if not path.exists():
        return DEFAULT_COURSE_METADATA.copy()   # JSON nahi hai → default dict

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))   # JSON string → dict
        
        # Safe merge with defaults (missing keys handle karo)
        normalized = DEFAULT_COURSE_METADATA.copy()
        for key in normalized:
            normalized[key] = parsed.get(key, normalized[key])
            # parsed mein key exist kare toh use lo, warna default rakho
        return normalized
    except Exception as e:
        warn(f"Could not read metadata JSON for {pdf_path.name}: {e}")
        return DEFAULT_COURSE_METADATA.copy()
```

**Why normalized merge?**
JSON file mein koi field missing ho ya corrupted ho → system crash na ho, default value use ho.

---

### 6.11 `parse_course_pdf_if_needed(pdf_path, force_parse=False)`

```python
def parse_course_pdf_if_needed(pdf_path: Path, force_parse: bool = False) -> Dict[str, Any]:
    path = metadata_path_for(pdf_path)

    if path.exists() and not force_parse:
        info("Metadata loaded", path.name)
        return load_metadata_json(pdf_path)    # Already parsed → load from JSON

    info("Parsing course metadata locally", pdf_path.name)
    metadata = build_course_metadata(pdf_path)  # Fresh parse
    save_metadata_json(pdf_path, metadata)
    return metadata
```

**Smart caching logic:**
```
JSON exists? ─── YES → force_parse? ─── NO  → Load from JSON (fast)
                                    └── YES → Re-parse PDF (fresh)
            └── NO  → Parse PDF → Save JSON → Return
```

---

### 6.12 `parse_all_pdfs(force_parse=False)`

```python
def parse_all_pdfs(force_parse: bool = False):
    section("COURSE MODULE PARSING — PDF TO JSON METADATA")
    print("Local parser: no Groq quota used.\n")

    for pdf in get_pdf_files():                # data/ folder ke saare PDFs iterate
        print(f"\n📄 {pdf.name}")
        metadata = parse_course_pdf_if_needed(pdf, force_parse=force_parse)
        info("ModuleTitle", clean_preview(metadata["ModuleTitle"], 120))
        info("Subject", metadata["Subject"])
        info("ModuleNumber", str(metadata["ModuleNumber"]))
        info("Topics", clean_preview(", ".join(metadata["TopicsCovered"][:8]), 180))
```

**Command:** `python combined_document_intelligence.py parse`  
Ye function `parse` command ke saath call hota hai. Har PDF ke liye metadata parse/load karta hai aur print karta hai.

---

## 7. RAG Ingestion — PDFs + Metadata → Chroma Vector DB

**Goal:** PDFs ko read karo, text ko chunks mein kato, metadata attach karo, embeddings banao, Chroma mein store karo.

---

### 7.1 `flatten_metadata_for_chroma(raw, pdf_path)`

```python
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
```

**Kyun flatten?**
Chroma DB metadata mein sirf simple key-value pairs store ho sakti hain (string, int, float). Lists store nahi ho sakti directly.

```
Original metadata (List):         Flattened for Chroma (String):
"TopicsCovered": [                 "topics_covered": "Why CSS? | Selectors | Box model"
    "Why CSS?",
    "Selectors",
    "Box model"
]
```

`" | ".join(topics)` → list items ko pipe separator se string bana do

---

### 7.2 `load_pdf_pages_with_metadata(pdf_path, parse_metadata, force_parse)`

```python
def load_pdf_pages_with_metadata(pdf_path: Path, parse_metadata: bool, force_parse: bool):
    # Step 1: Metadata decide karo
    if parse_metadata:
        raw_meta = parse_course_pdf_if_needed(pdf_path, force_parse=force_parse)
    else:
        # Existing JSON use karo ya build karo (save nahi karta)
        existing = metadata_path_for(pdf_path)
        raw_meta = load_metadata_json(pdf_path) if existing.exists() else build_course_metadata(pdf_path)

    # Step 2: Chroma ke liye flatten karo
    flat_meta = flatten_metadata_for_chroma(raw_meta, pdf_path)

    # Step 3: PDF load karo with LangChain
    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()   # List of Document objects (ek per page)

    # Step 4: Har page pe metadata attach karo
    for page in pages:
        page.metadata.update(flat_meta)
    # page.metadata already mein "source", "page" hota hai (PyPDFLoader se)
    # update() se hamari custom metadata add ho jaati hai

    return pages
```

**PyPDFLoader Document object structure:**
```
Document(
    page_content = "actual text of the page...",
    metadata = {
        "source": "data/Module 1-CSS3.pdf",   # LangChain adds this
        "page": 0,                              # LangChain adds this
        # After update():
        "file_name": "Module 1-CSS3.pdf",      # Hamara
        "subject": "CSS3",                      # Hamara
        "topics_covered": "Why CSS? | ...",     # Hamara
        ...
    }
)
```

---

### 7.3 `load_all_documents_for_rag(parse_metadata, force_parse)`

```python
def load_all_documents_for_rag(parse_metadata: bool = False, force_parse: bool = False):
    section("RAG INGESTION — PDFS + COURSE METADATA TO VECTOR DB")
    all_pages = []

    for pdf in get_pdf_files():
        try:
            print(f"\n📄 Loading: {pdf.name}")
            pages = load_pdf_pages_with_metadata(pdf, parse_metadata, force_parse)
            all_pages.extend(pages)     # saare pages ek list mein combine
            status("Pages loaded", str(len(pages)))
        except Exception as e:
            warn(f"Skipping {pdf.name}: {type(e).__name__}: {e}")
            # Ek PDF fail ho toh baaki process hoti rahein

    if not all_pages:
        raise RuntimeError("No pages loaded. Check your PDFs.")

    status("Total pages loaded", str(len(all_pages)))
    return all_pages
```

---

### 7.4 `split_documents(documents)`

```python
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,      # 1000 chars per chunk
        chunk_overlap=CHUNK_OVERLAP, # 200 chars overlap
    )
    chunks = splitter.split_documents(documents)
    # Documents list → Chunks list
    # Metadata automatically carried over from parent Document
    status("Chunks created", str(len(chunks)))
    return chunks
```

**RecursiveCharacterTextSplitter algorithm:**
```
1. Pehle "\n\n" (paragraph breaks) pe split karo
2. Agar chunk still too big → "\n" pe split
3. Agar still too big → " " (space) pe split
4. Agar still too big → character by character split
→ Natural text boundaries prefer karta hai
```

**Example:**
```
Page text (3000 chars):
"Bootstrap is a CSS framework... [1000 chars] ...grid system allows... [1000 chars] ...columns are responsive..."

After splitting (chunk_size=1000, overlap=200):
Chunk 1: chars 0-1000   (Bootstrap is a CSS framework...)
Chunk 2: chars 800-1800 (grid system allows...) ← 200 char overlap
Chunk 3: chars 1600-2600 (columns are responsive...)
```

---

### 7.5 `get_embedding_function()`

```python
def get_embedding_function():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,   # "sentence-transformers/all-MiniLM-L6-v2"
        show_progress=False,
    )
```

**Embedding kya hota hai?**
```
Text: "CSS selectors are used to target HTML elements"
         │
         ▼ (embedding model)
Vector: [0.23, -0.11, 0.87, 0.04, ..., 0.56]  ← 384 dimensions
```

Ek 384-dimensional vector jo text ka meaning represent karta hai. Similar meanings → similar vectors (close in 384-D space).

**all-MiniLM-L6-v2 kyun?**
- Small model (22MB) — fast, offline
- Good semantic understanding
- Widely used for RAG applications

---

### 7.6 `create_vector_store(chunks)`

```python
def create_vector_store(chunks):
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding_function(),   # Text → vectors
        persist_directory=str(CHROMA_DIR),    # "./chroma_db" folder mein save
        collection_name=COLLECTION_NAME,       # "combined_docs"
    )
    status("Vector DB created", str(CHROMA_DIR))
    return vector_store
```

**Internally kya hota hai:**
```
Chunks list:
[Chunk1(text+metadata), Chunk2(text+metadata), ...]
                │
                ▼ embedding function
[Vector1(384-D), Vector2(384-D), ...]
                │
                ▼ stored in Chroma
chroma_db/
├── chroma.sqlite3     ← metadata + original text store
└── [vector files]     ← actual embedding vectors
```

---

### 7.7 `load_vector_store()`

```python
def load_vector_store():
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embedding_function(),
        collection_name=COLLECTION_NAME,
    )
    status("Vector DB loaded", str(CHROMA_DIR))
    return vector_store
```

**vs create_vector_store():**
- `create_vector_store()` → Naya DB banata hai + chunks + embeddings likhta hai (slow, one-time)
- `load_vector_store()` → Existing DB se load karta hai (fast, every query pe)

---

### 7.8 `ingest_documents(rebuild, parse_metadata, force_parse)`

```python
def ingest_documents(rebuild: bool = False, parse_metadata: bool = False, force_parse: bool = False):
    # Step 1: Rebuild flag check
    if rebuild and CHROMA_DIR.exists():
        warn("Rebuild enabled. Removing old Chroma DB.")
        shutil.rmtree(CHROMA_DIR)   # Poora chroma_db/ folder delete

    # Step 2: Already exists aur rebuild nahi → just load
    if CHROMA_DIR.exists() and not rebuild:
        info("Existing Chroma DB", "Already exists. Use --rebuild to recreate.")
        return load_vector_store()

    # Step 3: Fresh build
    documents = load_all_documents_for_rag(parse_metadata, force_parse)
    chunks = split_documents(documents)
    return create_vector_store(chunks)
```

**Decision tree:**
```
--rebuild flag? ─── YES → Delete old chroma_db/ → Fresh ingest
                └── NO  → chroma_db/ exists? ─── YES → Load existing (fast)
                                              └── NO  → Fresh ingest
```

---

## 8. Question Answering — Chroma → Ollama

**Goal:** User ka question lo, relevant chunks dhundo, Ollama LLM se answer generate karo.

---

### 8.1 `metadata_matches(doc, subject, module, title)`

```python
def metadata_matches(
    doc,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    meta = doc.metadata

    if subject and subject.lower() not in str(meta.get("subject", "")).lower():
        return False    # Subject filter fail

    if module and str(module).lower() != str(meta.get("module_number", "")).lower():
        return False    # Module number exact match required

    if title and title.lower() not in str(meta.get("module_title", "")).lower():
        return False    # Title substring check

    return True   # All filters passed (or no filters given)
```

**Filter behavior:**
```
subject="CSS3"  → case-insensitive substring match
                  "css3" in "CSS3" → True ✅
                  "css3" in "Bootstrap5" → False ❌

module="1"      → exact string match (both lowercased)
                  "1" == "1" → True ✅
                  "1" == "2" → False ❌

title="grid"    → case-insensitive substring match
                  "grid" in "Bootstrap Grid System" → True ✅
```

---

### 8.2 `retrieve_docs(query, vector_store, subject, module, title)`

```python
def retrieve_docs(query, vector_store, subject=None, module=None, title=None):
    # Step 1: Semantic search — top FETCH_K=12 candidates
    candidates = vector_store.similarity_search(query, k=FETCH_K)
    # Chroma: query text → embedding → cosine similarity → top 12 chunks

    # Step 2: Metadata filter apply karo
    filtered = [
        doc for doc in candidates
        if metadata_matches(doc, subject=subject, module=module, title=title)
    ]

    # Step 3: Agar filter ke baad kuch nahi mila → fallback
    if not filtered and any([subject, module, title]):
        warn("No docs matched metadata filters. Falling back to semantic search only.")
        filtered = candidates   # Unfiltered results use karo

    return filtered[:TOP_K]   # Top 4 return karo
```

**Why FETCH_K > TOP_K?**
```
Semantic search → TOP 12 candidates fetch karo
    │
    ▼
Metadata filter → only CSS3 wale chahiye → shayad 4-5 bachein
    │
    ▼
Top 4 return karo (TOP_K=4)

Agar directly 4 fetch karte → filter ke baad 0-1 bachte
Agar 12 fetch karo → filter ke baad bhi enough candidates milte hain
```

**similarity_search kaise kaam karta hai:**
```
User query: "What are CSS selectors?"
    │
    ▼ Embedding
Vector: [0.45, -0.23, ...]
    │
    ▼ Chroma cosine similarity against all stored vectors
Ranked: [chunk_selectors_page3 (0.92), chunk_css_intro_p1 (0.87), ...]
    │
    ▼ Return top 12
```

---

### 8.3 `format_docs_for_prompt(docs)`

```python
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
```

**Output example:**
```
[Source 1: Module 1-CSS3.pdf, page=2, subject=CSS3, module=1, title=CSS3 Complete Guide]
CSS selectors are patterns used to select elements. Class selectors use a dot...

[Source 2: Module 1-CSS3.pdf, page=5, subject=CSS3, module=1, title=CSS3 Complete Guide]
ID selectors use a hash symbol. They target unique elements on the page...
```

LLM ko ye formatted context diya jaata hai taaki woh accurate answers de sake.

---

### 8.4 `answer_question(query, vector_store, subject, module, title)`

```python
def answer_question(query, vector_store, subject=None, module=None, title=None):
    # Step 1: Relevant chunks retrieve karo
    docs = retrieve_docs(query, vector_store, subject=subject, module=module, title=title)

    if not docs:
        return "I don't know based on the provided documents.", []

    # Step 2: Ollama LLM initialize karo
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)
    # temperature=0 → deterministic output, no randomness — factual QA ke liye best

    # Step 3: Prompt template define karo
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

    # Step 4: Chain — prompt | llm | parser
    answer = (prompt | llm | StrOutputParser()).invoke(
        {"context": format_docs_for_prompt(docs), "question": query}
    )

    return answer, docs
```

**LangChain Chain (`|` operator):**
```
prompt template     llm          output parser
      │              │                │
      ▼              ▼                ▼
{context}+{question} → ChatOllama → raw AIMessage → plain string
      
.invoke({"context": ..., "question": ...})
→ Fills template → Sends to Ollama → Returns string answer
```

**temperature=0 kyun?**
```
temperature=0    → Always picks most likely token → Consistent, factual
temperature=0.7  → Some randomness → Creative but may hallucinate
temperature=1.0  → Maximum randomness → Unpredictable

For Q&A from documents → temperature=0 best hai
```

**Prompt engineering notes:**
- "Answer ONLY using the context below" → Hallucination prevent karta hai
- "If the answer is not present...say exactly..." → Predictable failure mode
- "Do NOT add 'I don't know' after giving a valid answer" → LLM ki tendency fix karta hai

---

### 8.5 `print_sources(docs)`

```python
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
```

**Output example:**
```
📚 Retrieved sources:
1. Module 1-CSS3.pdf | page=2 | subject=CSS3 | module=1 | title=CSS3 Complete Guide
   Preview: CSS selectors target HTML elements. Class selectors use a dot notation...
2. Module 1-CSS3.pdf | page=5 | subject=CSS3 | module=1 | title=CSS3 Complete Guide
   Preview: ID selectors target unique elements using hash symbol. Each ID must be...
```

Ye transparency ke liye hai — user dekh sake ki answer kahan se aaya.

---

### 8.6 `run_ask(args)`

```python
def run_ask(args):
    vector_store = load_vector_store()   # Existing Chroma DB load karo

    answer, docs = answer_question(
        query=args.question,        # CLI se question
        vector_store=vector_store,
        subject=args.subject,       # --subject CSS3 (optional)
        module=args.module,         # --module 1 (optional)
        title=args.title,           # --title "grid" (optional)
    )

    print("\n🧠 Answer:")
    print(answer)

    print_sources(docs)
```

**Command:** `python combined_document_intelligence.py ask "What are CSS selectors?" --subject CSS3`

---

### 8.7 `run_chat()`

```python
def run_chat():
    vector_store = load_vector_store()   # Ek baar load karo

    section("COMBINED COURSE MODULE RAG CHAT")
    print("Ask questions about your PDFs. Type 'exit' to quit.\n")

    while True:
        query = input("❓ Question: ").strip()   # User se input lo

        if query.lower() in {"exit", "quit"}:   # Exit check
            print("👋 Exiting.")
            break

        if not query:   # Empty input skip karo
            continue

        answer, docs = answer_question(query, vector_store)
        print("\n🧠 Answer:")
        print(answer)
        print_sources(docs)
        print("\n" + "-" * 72 + "\n")   # Visual separator between Q&As
```

**Stateless nature:** Har question independent hai — koi conversation history nahi. Matlab `answer_question` ko pata nahi ki pehle kya pucha tha. Ye RAG system hai, chatbot nahi.

---

## 9. CLI — Command Line Interface

```python
def build_cli():
    parser = argparse.ArgumentParser(
        description="Course Metadata Parser + Multi-Document RAG"
    )

    sub = parser.add_subparsers(dest="command", required=True)
    # "dest=command" → args.command mein selected subcommand store hoga
    # required=True → koi command dena zaroori hai
```

### Subcommands:

```python
# 1. PARSE
p_parse = sub.add_parser("parse", help="Extract course metadata JSON from PDFs locally")
p_parse.add_argument("--force", action="store_true", help="Re-parse even if JSON already exists")
# action="store_true" → flag present hai toh True, absent hai toh False
```

```python
# 2. INGEST
p_ingest = sub.add_parser("ingest", help="Build Chroma vector DB from PDFs")
p_ingest.add_argument("--rebuild", action="store_true")
p_ingest.add_argument("--parse", action="store_true")          # metadata bhi parse karo
p_ingest.add_argument("--force-parse", action="store_true")    # metadata re-parse karo
```

```python
# 3. ASK
p_ask = sub.add_parser("ask", help="Ask one question")
p_ask.add_argument("question", type=str)              # Positional argument (required)
p_ask.add_argument("--subject", type=str, default=None)  # Optional filters
p_ask.add_argument("--module", type=str, default=None)
p_ask.add_argument("--title", type=str, default=None)
```

```python
# 4. CHAT
sub.add_parser("chat", help="Interactive chat mode")
# No additional arguments needed
```

**argparse behavior:**
```
python script.py parse              → args.command = "parse", args.force = False
python script.py parse --force      → args.command = "parse", args.force = True
python script.py ask "What is CSS?" → args.command = "ask", args.question = "What is CSS?"
python script.py ask "X" --subject CSS3 → args.subject = "CSS3"
```

---

## 10. main() — Entry Point

```python
def main():
    ensure_folders()        # data/ aur metadata/ folders create karo
    args = build_cli().parse_args()   # CLI parse karo

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
```

`if __name__ == "__main__":` → Script directly run ho tab main() call ho. Import ho tab nahi.

---

## 11. Complete Data Flow Diagrams

### PARSE Command Flow:
```
python script.py parse
          │
          ▼
    main() → parse_all_pdfs()
          │
          ▼
    get_pdf_files() → [Module1-CSS3.pdf, Module1-Bootstrap5.pdf]
          │
          ▼ (for each PDF)
    parse_course_pdf_if_needed()
          │
          ├── JSON exists? → load_metadata_json() → print & return
          │
          └── No JSON → build_course_metadata()
                   │
                   ├── extract_text_from_pdf() (3 pages, PyPDF2)
                   ├── guess_subject_from_filename()
                   ├── guess_module_number()
                   ├── first_meaningful_line()
                   ├── extract_numbered_topics() (regex)
                   └── subject_key_concepts() (hardcoded)
                             │
                             ▼
                   save_metadata_json() → data/extracted_metadata/Module1-CSS3.json
```

### INGEST Command Flow:
```
python script.py ingest --rebuild --parse
          │
          ▼
    main() → ingest_documents(rebuild=True, parse_metadata=True)
          │
          ├── --rebuild: shutil.rmtree(chroma_db/)
          │
          ▼
    load_all_documents_for_rag()
          │
          ▼ (for each PDF)
    load_pdf_pages_with_metadata()
          │
          ├── parse_course_pdf_if_needed() → raw metadata dict
          ├── flatten_metadata_for_chroma() → flat string dict
          ├── PyPDFLoader.load() → [Document(page_content, metadata), ...]
          └── page.metadata.update(flat_meta) → metadata attach
                    │
                    ▼
    split_documents() (RecursiveCharacterTextSplitter, 1000/200)
                    │
                    ▼
    create_vector_store()
          │
          ├── HuggingFaceEmbeddings (all-MiniLM-L6-v2)
          └── Chroma.from_documents() → chroma_db/ folder
```

### ASK/CHAT Command Flow:
```
python script.py ask "What are CSS selectors?" --subject CSS3
          │
          ▼
    main() → run_ask(args)
          │
          ▼
    load_vector_store() → Chroma(chroma_db/)
          │
          ▼
    answer_question(query, vector_store, subject="CSS3")
          │
          ├── retrieve_docs()
          │       │
          │       ├── similarity_search(query, k=12) → [12 candidate chunks]
          │       ├── metadata_matches() filter → keep CSS3 only
          │       └── return top 4
          │
          ├── format_docs_for_prompt() → formatted context string
          │
          ├── ChatOllama(model="llama3", temperature=0)
          │
          ├── ChatPromptTemplate.from_template(...)
          │
          └── (prompt | llm | StrOutputParser()).invoke(...)
                    │
                    ▼
    print(answer) + print_sources(docs)
```

---

## 12. Command Cheat Sheet

```bash
# Step 1: PDFs se metadata parse karo (local, no API)
python combined_document_intelligence.py parse

# Force re-parse (JSON already exist kare toh bhi)
python combined_document_intelligence.py parse --force

# Step 2: Vector DB build karo
python combined_document_intelligence.py ingest --rebuild

# Metadata ke saath ingest (parse bhi karo)
python combined_document_intelligence.py ingest --rebuild --parse

# Step 3: Question puchho
python combined_document_intelligence.py ask "What are CSS selectors?"

# Subject filter ke saath
python combined_document_intelligence.py ask "Explain grid system" --subject Bootstrap5

# Module filter ke saath
python combined_document_intelligence.py ask "What topics are covered?" --module 1

# Interactive chat mode
python combined_document_intelligence.py chat
```

---

## KEY CONCEPTS SUMMARY

| Concept | Tool Used | Purpose |
|---------|-----------|---------|
| PDF Text Extraction | PyPDF2 | Raw text nikalna (parse step) |
| Regex Parsing | Python `re` | Topics, module number nikalna filenames se |
| Document Loading | LangChain PyPDFLoader | Pages as Document objects (ingest step) |
| Text Splitting | RecursiveCharacterTextSplitter | Long pages → manageable chunks |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Text → 384-D vectors |
| Vector DB | Chroma | Vectors store + similarity search |
| Local LLM | Ollama llama3 | Answer generation |
| Prompt Template | LangChain ChatPromptTemplate | Structured prompt with context |
| LangChain Chain | `|` operator | prompt → llm → parser pipeline |
| Metadata Filtering | Custom `metadata_matches()` | Subject/module specific retrieval |

---

*Notes by: Karan (Claude) for Suyash — DN 5.0 & AI Projects*
