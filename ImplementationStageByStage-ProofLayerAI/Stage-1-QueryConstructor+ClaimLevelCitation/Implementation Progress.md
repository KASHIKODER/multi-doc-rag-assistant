# Stage 02 Implementation Process Log

## Query Construction, Source-Safe Citation, and Final Output Polishing

This document is an add-on development log for the existing project README.  
It does **not** replace the original README. The original README explains the core architecture, code flow, and feature purpose. This file explains how the implementation evolved through testing, errors, fixes, and final stabilization.

---

## 1. Why This Extra Document Exists

During the implementation of Stage 02, the project went through several practical debugging steps:

- environment setup issues
- folder/path issues
- dependency issues
- query construction failures
- source citation failures
- low-confidence claim noise
- output formatting issues
- GitHub/public-demo polish

The goal of this document is to make that engineering process visible in the repository.

This is useful because it shows that the project was not only coded, but also tested, debugged, and improved step by step.

---

## 2. Final Stage Goal

Stage 02 upgrades the project from a basic metadata-aware multi-document RAG system into a more reliable document assistant with:

1. **Query Construction**
   - Converts natural-language questions into structured filters.
   - Example:
     ```text
     Question: What topics are covered in the CSS3 module?
     Parsed:
       subject = CSS3
       module = None
       semantic_query = topics covered
     ```

2. **Metadata-Aware Retrieval**
   - Uses detected subject/module filters to improve retrieval precision.
   - Prevents unrelated documents from being retrieved when the query clearly belongs to one subject.

3. **Deterministic Topic Answer Mode**
   - For topic/listing questions, answers directly from metadata fields:
     - `topics_covered`
     - `key_concepts`
     - `learning_objectives`
   - This is faster and more reliable than forcing the LLM to generate claims for simple topic-listing questions.

4. **Claim-Level Citation**
   - For explanation-style questions, breaks the answer into verified claims.
   - Each claim is mapped to a retrieved source document and page.

5. **Source-Safe Output**
   - Removes unknown-source claims.
   - Hides low-confidence claims.
   - Repairs invalid source numbers using local token matching.
   - Converts zero-based PDF page indexes into human-readable page numbers.

---

## 3. Implementation Timeline

### Step 1 — Base Multi-Document RAG Was Working

The project already had:

```text
PDFs
  → metadata parser
  → chunks
  → HuggingFace embeddings
  → Chroma vector store
  → Ollama answer generation
  → source display
```

A basic query such as:

```text
What topics are covered in the CSS3 module?
```

successfully returned CSS3-related chunks and source metadata.

This confirmed that:

- PDFs were loading correctly.
- Chroma was working.
- Metadata was attached to chunks.
- Normal RAG answering worked.

---

### Step 2 — Environment Issue: `langchain_community` Missing

#### Error

```text
ModuleNotFoundError: No module named 'langchain_community'
```

#### Cause

The virtual environment was not active in the terminal session. The project was being run using a Python environment that did not contain the required LangChain packages.

#### Fix

Activated the correct virtual environment:

```powershell
..\..\..\venv\Scripts\Activate.ps1
```

Verified that Python and pip pointed to the project virtual environment:

```powershell
python -c "import sys; print(sys.executable)"
python -m pip --version
```

Then verified the package import:

```powershell
python -c "from langchain_community.document_loaders import PyPDFLoader; print('langchain_community ok')"
```

#### Result

Dependency issue was resolved.

---

### Step 3 — Folder/Path Issue: Data Folder Location

The stage implementation was placed inside:

```text
ImplementationStageByStage-ProofLayerAI/
  QueryConstructor+ClaimLevelCitation/
```

The script used relative paths:

```python
DATA_DIR = ./data
CHROMA_DIR = ./chroma_db
METADATA_DIR = ./data/extracted_metadata
```

#### Issue

If the script was run from the wrong folder, it could not find the expected `data/` folder or vector database.

#### Fix

Moved/copied the required `data/` folder into the stage folder so the script could run locally inside the stage workspace:

```text
QueryConstructor+ClaimLevelCitation/
  data/
  chroma_db/
  Kashi-Mate-RAG-QueryConstructor-ClaimLevelCitation.py
```

#### Result

The stage became self-contained for local testing.

---

## 4. Query Construction Debugging

### Initial Problem

The first version used local Ollama structured output directly for query construction.

For this question:

```text
Module 1 ke CSS topics batao
```

the system returned:

```text
subject = None
module = None
semantic_query = Module
```

This was not acceptable because the query clearly refers to CSS3 and Module 1.

---

### Root Cause

Small local models can be inconsistent when parsing short mixed-language or informal queries into structured JSON.

The issue was not Chroma or retrieval. It was the query-construction layer.

---

### Fix

Added a **hybrid query construction strategy**:

```text
1. Rule-based parser first
2. Local LLM structured output as fallback
3. Plain semantic query fallback if structured output fails
```

The rule-based parser detects known subject aliases:

```text
CSS3        → css, selectors, styling, media query
Bootstrap5 → bootstrap, grid, navbar, row, column
HTML5       → html, forms, semantic tags, nav
JavaScript → javascript, js, dom, events, functions
SQL         → sql, mysql, joins, group by, queries
```

It also extracts module numbers:

```text
Module 1 → module = 1
```

---

### Result

The same query now returns:

```text
subject = CSS3
module = 1
semantic_query = topics covered
```

Another example:

```text
Question: Explain the Bootstrap grid system.
Parsed:
  subject = Bootstrap5
  module = None
  semantic_query = grid system explanation
```

This made retrieval much more precise.

---

## 5. Claim-Level Citation Debugging

### Initial Problem

Claim-level citation generated claims, but some claims showed:

```text
Source: unknown (page ?)
```

This happened when the local LLM returned an invalid `source_number`.

Example:

```text
source_number = 5
```

while only 4 retrieved sources existed.

---

### Root Cause

Structured output controlled the schema, but it did not guarantee that the model would always return a valid source number.

---

### Fix

Added local source repair logic:

```text
claim_text
  → token overlap scoring
  → compare claim with retrieved docs
  → select best matching source
```

Added functions for:

- citation token extraction
- claim-to-document scoring
- best source index matching
- safe source resolution

If the model-provided source number is invalid or weak, the system repairs it locally.

If no safe match exists, the claim is not printed.

---

### Result

The output no longer prints:

```text
Source: unknown (page ?)
```

Instead, it prints a real source or hides the unsupported claim.

---

## 6. Low-Confidence Claim Filtering

### Problem

Some citation outputs included weak claims such as:

```text
Bootstrap's JavaScript plugins can be used to create responsive design.
Confidence: low
```

This was technically source-mapped but not relevant enough for a final public answer.

---

### Fix

The citation prompt was made stricter:

```text
- Do not include low-confidence claims.
- Only include claims that directly answer the user's question.
```

The output printer was also updated to skip low-confidence claims.

---

### Result

Public output became cleaner and more professional.

---

## 7. Topic Answer Mode

### Problem

For topic-listing questions like:

```text
Tell me some important topics in JavaScript.
```

the LLM-based claim path was unnecessary and sometimes produced weak claims.

---

### Fix

Added a deterministic topic-answer path.

If the question asks about:

```text
topics
important topics
covered
what does this module cover
```

the system answers directly from metadata fields:

```text
topics_covered
key_concepts
learning_objectives
```

---

### Result

The response is now fast, complete, and document-grounded.

Example:

```text
Question:
List the important topics in JavaScript.

Output:
DOCUMENT-GROUNDED TOPIC ANSWER
- JavaScript Basics & Setup
- Modern JavaScript Features
- Syntax, Data Types, and Operators
- Functions, Scope, Closures, Higher-Order Functions
- DOM Manipulation
- Event Handling
- Async JS, Promises, Async/Await
```

This path is intentionally fast because it does not require LLM generation for simple metadata questions.

---

## 8. Human-Readable Page Numbers

### Problem

LangChain/PyPDFLoader stores PDF page numbers as zero-based indexes:

```text
page 0 = PDF page 1
page 1 = PDF page 2
```

This looked confusing in public output.

---

### Fix

Added a display helper:

```python
display_page_number(page_value)
```

It converts:

```text
0 → 1
1 → 2
2 → 3
```

Only the displayed page number changes. The internal metadata remains unchanged.

---

### Result

Output now shows human-readable page numbers:

```text
Source: Module 1-JavaScript.pdf (page 1)
```

instead of:

```text
Source: Module 1-JavaScript.pdf (page 0)
```

---

## 9. Display Text Cleanup

### Problem

PDF extraction sometimes introduced broken spacing:

```text
JavaScript Exer cises
Bootstrap 5 Exerci ses
Higher -Order Functions
```

---

### Fix

Added a display cleanup helper:

```python
clean_display_text(text)
```

This performs final output cleanup only.

Examples:

```text
Exer cises     → Exercises
Exerci ses     → Exercises
Exerc ises     → Exercises
Higher -Order  → Higher-Order
```

---

### Result

GitHub/demo output looks cleaner.

---

## 10. Final Answer Routing

The final system uses two different answer modes.

### Mode 1 — Document-Grounded Topic Answer

Used for topic/listing questions.

Example questions:

```text
List the important topics in JavaScript.
What topics are covered in the CSS3 module?
What does the HTML5 module cover about forms and semantic tags?
```

Expected output:

```text
DOCUMENT-GROUNDED TOPIC ANSWER
```

This mode is fast and deterministic.

---

### Mode 2 — Citation-Backed Answer

Used for explanation questions.

Example questions:

```text
Explain the Bootstrap grid system.
What table relationships are described in the SQL module?
Explain CSS selectors.
```

Expected output:

```text
CITATION-BACKED ANSWER
```

This mode uses the local LLM, then verifies and prints source-backed claims.

---

## 11. Final Validated Questions

These questions were used for validation.

### Topic-Listing Tests

```text
List the important topics in JavaScript.
What topics are covered in the CSS3 module?
What does the HTML5 module cover about forms and semantic tags?
```

Expected:

```text
DOCUMENT-GROUNDED TOPIC ANSWER
```

---

### Explanation Tests

```text
Explain the Bootstrap grid system.
What table relationships are described in the SQL module?
Explain CSS selectors.
```

Expected:

```text
CITATION-BACKED ANSWER
```

---

### Hallucination Guard Test

```text
What does the document say about React?
```

Expected:

```text
No supported claims found
```

or a clearly grounded refusal based on retrieved documents.

---

## 12. Final Verified Outputs

### HTML5 Query

```text
Question:
What does the HTML5 module cover about forms and semantic tags?

Result:
- Subject detected as HTML5
- Topic answer mode selected
- Correct source: Module 1-HTML 5.pdf
- Human-readable page number shown
```

---

### Bootstrap Query

```text
Question:
Explain the Bootstrap grid system.

Result:
- Subject detected as Bootstrap5
- Citation-backed answer mode selected
- Claims supported by Module 1-Bootstrap5.pdf
- Low-confidence claims removed
```

---

### SQL Query

```text
Question:
What table relationships are described in the SQL module?

Result:
- Subject detected as SQL
- Citation-backed answer mode selected
- Foreign key/table relationship claims supported by Module 2-ANSI SQL Using MySQL.pdf
```

---

## 13. GitHub Push Checklist

Before pushing:

```powershell
git status
```

Make sure these are **not** committed:

```text
.env
venv/
.venv/
chroma_db/
data/*.pdf
data/extracted_metadata/*.json
__pycache__/
```

Recommended `.gitignore` rules:

```gitignore
.env
**/.env
venv/
.venv/
__pycache__/
**/__pycache__/
*.pyc
chroma_db/
**/chroma_db/
data/*.pdf
**/data/*.pdf
data/extracted_metadata/*.json
**/data/extracted_metadata/*.json
```

Recommended commit message:

```bash
git commit -m "Add final metadata-aware RAG stage with query construction and source citations"
```

---

## 14. Current Project Rating

For the current learning + portfolio stage:

```text
9.1 / 10
```

### Strengths

- Multi-document PDF ingestion
- Local metadata parser
- Chroma vector storage
- HuggingFace embeddings
- Ollama local answering
- Query construction
- Metadata-aware retrieval
- Deterministic topic answer mode
- Source-safe claim-level citation
- Human-readable page numbers
- Public-demo-friendly output

### Remaining Improvements

To move closer to production level:

- Add automated evaluation
- Add unit tests
- Add reranking
- Add Streamlit or FastAPI UI
- Add Docker support
- Add logging and observability
- Add CI checks before GitHub push

---

## 15. Final Summary

Stage 02 evolved from a simple metadata-aware RAG upgrade into a more reliable document intelligence layer.

The final version now supports:

```text
Natural question
  → query construction
  → metadata-aware retrieval
  → topic-answer routing OR citation-backed answer
  → source-safe public output
```

This makes the project stronger than a basic PDF chatbot because the system can:

- understand the user query
- route the answer type
- retrieve from the correct document
- avoid unknown sources
- remove weak claims
- show page-level source grounding
- answer topic questions deterministically

This stage is ready to be pushed as a documented GitHub milestone.
