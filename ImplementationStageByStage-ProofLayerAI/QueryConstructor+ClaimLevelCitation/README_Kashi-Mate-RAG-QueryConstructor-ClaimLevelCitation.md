# DocuMind RAG — Stage Documentation

## Metadata-Aware Multi-Document RAG with Query Construction and Claim-Level Citation

DocuMind RAG is a learning-to-production style project that evolves a basic RAG pipeline into a metadata-aware, source-grounded, multi-document assistant.

The current version combines:

1. **Course Module Metadata Parsing**
2. **Multi-Document RAG**
3. **Query Construction**
4. **Claim-Level Citation**

This README explains the complete code flow, what was added on top of the earlier version, where the new logic lives in the code, and why each upgrade matters.

> Note: Line numbers in this document are based on the current `combined_document_intelligence.py` version used for this stage. If the file changes later, line numbers may shift.

---

## 1. Project Goal

The goal of this project is not to build a basic chatbot.

The goal is to build a real document intelligence system that can:

- Read multiple course PDFs
- Extract useful metadata from each document
- Store document chunks with metadata
- Retrieve relevant context using semantic search
- Understand natural-language questions and convert them into filters
- Generate answers grounded in retrieved context
- Break answers into cited claims with supporting sources
- Run locally without Groq/OpenAI dependency for the current course-module version

---

## 2. High-Level Architecture

```text
Course PDFs
   ↓
Local Course Metadata Parser
   ↓
PDF Pages + Metadata
   ↓
Chunking
   ↓
HuggingFace Embeddings
   ↓
Chroma Vector Database
   ↓
Retriever
   ↓
Query Construction
   ↓
Metadata-Aware Retrieval
   ↓
Claim-Level Citation
   ↓
Answer + Source References
```

---

## 3. What Was Already Present in the Earlier Project

Before this stage, the project already had the base metadata-aware RAG pipeline.

### Earlier implemented logic

| Feature | Purpose | Code Location |
|---|---|---|
| Course metadata parser | Extracts `ModuleTitle`, `Subject`, `ModuleNumber`, `TopicsCovered`, etc. | Lines 151-354 |
| PDF loading + metadata attachment | Loads PDFs and attaches metadata to each page | Lines 378-393 |
| Multi-document ingestion | Loads all PDFs from the `data/` folder | Lines 396-414 |
| Chunking | Splits PDFs into overlapping chunks | Lines 417-424 |
| Embeddings | Converts chunks into vectors | Lines 427-431 |
| Chroma vector store | Stores chunks + metadata | Lines 434-442 |
| Existing vector DB loading | Loads saved Chroma DB | Lines 445-452 |
| Basic retrieval | Retrieves documents using semantic similarity + optional filters | Lines 548-566 |
| Prompt formatting | Formats retrieved documents with source metadata | Lines 569-584 |
| Plain RAG answer | Generates normal answer using retrieved context | Lines 586-627 |
| Source printing | Prints file, page, subject, module, title, and preview | Lines 630-645 |

This earlier version already solved a major problem:

```text
Basic RAG → Metadata-Aware Multi-Document RAG
```

Earlier source output looked like this:

```text
Module 1-CSS3.pdf | page=0 | subject=CSS3 | module=1 | title=CSS3 Exercises
```

That made the system more trustworthy than a normal PDF chatbot.

---

## 4. What Was Added in This Stage

This stage added two major upgrades:

```text
1. Query Construction
2. Claim-Level Citation
```

These upgrades make the project closer to production-style RAG.

---

# Stage 1: Query Construction

## 5. What Problem Did Query Construction Solve?

Earlier, the user had to manually pass filters.

Example:

```bash
python combined_document_intelligence.py ask "Explain grid system" --subject Bootstrap5
```

This works, but it is not natural.

A real user will ask:

```text
Module 1 ke CSS topics batao
```

or:

```text
Explain Bootstrap grid system
```

The system should understand:

```json
{
  "subject": "CSS3",
  "module": "1",
  "semantic_query": "topics covered"
}
```

This is where Query Construction comes in.

Query Construction converts a natural-language question into:

```text
structured filters + clean semantic query
```

---

## 6. Query Construction Code Locations

### New Pydantic import

Query construction uses Pydantic schema classes.

```text
Lines 65-66
```

```python
from pydantic import BaseModel, Field
```

### Known subjects list

The system needs to know the valid subjects.

```text
Lines 88-89
```

```python
KNOWN_SUBJECTS = ["HTML5", "CSS3", "Bootstrap5", "JavaScript", "SQL"]
```

This list helps the model classify user questions into valid course-module subjects.

---

## 7. `CourseQuery` Schema

Main schema:

```text
Lines 476-496
```

Purpose:

`CourseQuery` defines the structured output format.

It has three fields:

```text
subject
module
semantic_query
```

### Field 1: `subject`

Used when the question clearly mentions a subject.

Example:

```text
"What topics are covered in CSS3?"
```

Expected:

```json
{
  "subject": "CSS3"
}
```

### Field 2: `module`

Used when the question mentions a module number.

Example:

```text
"Module 1 ke CSS topics batao"
```

Expected:

```json
{
  "module": "1"
}
```

### Field 3: `semantic_query`

This is the cleaned version of the user query used for semantic retrieval.

Example:

```text
Input: Module 1 ke CSS topics batao
semantic_query: topics covered
```

This helps retrieval focus on the actual meaning rather than wasting vector search on filter words like `module 1`.

---

## 8. `parse_natural_query()` Function

Main function:

```text
Lines 499-521
```

Purpose:

This function uses local Ollama with structured output to extract filters from the question.

Flow:

```text
User question
   ↓
Prompt asks model to extract filters
   ↓
Ollama returns structured CourseQuery
   ↓
System gets subject/module/semantic_query
```

Important code idea:

```python
structured_llm = llm.with_structured_output(CourseQuery)
```

This tells the model:

> Do not return random text. Return output that matches the `CourseQuery` schema.

### Fallback logic

If query construction fails, the function safely falls back to:

```python
CourseQuery(subject=None, module=None, semantic_query=user_input)
```

This is important because the app should not crash if structured output fails.

---

## 9. Where Query Construction Is Used

Query Construction is currently used inside `chat` mode.

Code location:

```text
Lines 778-788
```

Flow:

```text
User enters natural question
   ↓
parse_natural_query(query)
   ↓
System prints detected subject/module/semantic query
   ↓
retrieve_docs() uses these filters
```

Important lines:

```text
Line 779: parsed = parse_natural_query(query)
Lines 783-788: retrieve_docs() uses parsed.semantic_query, parsed.subject, parsed.module
```

### Important Current Limitation

At this stage:

```text
chat mode uses automatic Query Construction
ask mode still uses manual CLI filters
```

So:

```bash
python combined_document_intelligence.py chat
```

supports auto-detected filters.

But:

```bash
python combined_document_intelligence.py ask "Module 1 ke CSS topics batao"
```

still follows the older plain `ask` path unless subject/module are manually provided.

This is not a bug. It is the current stage boundary.

Future stage can upgrade `ask` mode to use Query Construction too.

---

## 10. Benefit of Query Construction

Before:

```text
User had to know the CLI flags:
--subject CSS3
--module 1
```

After:

```text
User can ask naturally:
Module 1 ke CSS topics batao
```

The system can detect:

```text
subject = CSS3
module = 1
semantic_query = topics covered
```

Benefits:

- More natural user experience
- Less manual filtering
- Better retrieval precision
- Direct connection to Part 11 Query Construction from RAG learning
- Foundation for future routing and agentic RAG

---

# Stage 2: Claim-Level Citation

## 11. What Problem Did Claim-Level Citation Solve?

Earlier, the system generated one answer and then printed source chunks separately.

Example:

```text
Answer:
CSS3 covers selectors, typography, box model, and media queries.

Sources:
1. Module 1-CSS3.pdf page 0
2. Module 1-CSS3.pdf page 1
```

This is good, but it does not say which exact claim came from which source.

A stronger RAG system should answer like this:

```text
Claim 1:
CSS3 covers selectors.
Source: Module 1-CSS3.pdf page 0
Confidence: high

Claim 2:
CSS3 covers box model.
Source: Module 1-CSS3.pdf page 2
Confidence: high
```

This is what Claim-Level Citation adds.

---

## 12. Claim-Level Citation Code Locations

### New section starts

```text
Lines 648-650
```

This section introduces the claim-level citation logic.

---

## 13. `Claim` Schema

Code location:

```text
Lines 654-663
```

Purpose:

Represents one factual statement.

Fields:

```text
claim_text
source_number
confidence
```

### `claim_text`

The actual factual statement.

Example:

```text
CSS3 module covers Responsive Web Design with Media Queries.
```

### `source_number`

Which numbered source supports the claim.

Example:

```text
Source 1
```

### `confidence`

How strongly the source supports the claim.

Allowed style:

```text
high
medium
low
```

This helps users understand whether the answer is directly stated or inferred.

---

## 14. `CitedAnswer` Schema

Code location:

```text
Lines 666-671
```

Purpose:

Represents the full cited answer.

Fields:

```text
claims
overall_summary
```

### `claims`

List of individually cited claims.

### `overall_summary`

A short summary tying the claims together.

---

## 15. Claim Extraction Prompt

Code location:

```text
Lines 674-691
```

Purpose:

This prompt tells the model:

```text
Use only numbered sources.
Break answer into separate factual claims.
For each claim, attach exact source number.
Rate confidence.
Do not include unsupported claims.
Return empty claims if nothing is supported.
```

This prompt is stricter than a normal RAG prompt.

Normal RAG prompt asks:

```text
Answer using context.
```

Claim citation prompt asks:

```text
Answer as verifiable claims with source mapping.
```

That is a much stronger grounding pattern.

---

## 16. `generate_cited_answer()`

Code location:

```text
Lines 694-713
```

Purpose:

Generates structured cited answer.

Flow:

```text
Retrieved docs
   ↓
Format docs with numbered sources
   ↓
Send context + question to LLM
   ↓
LLM returns CitedAnswer schema
   ↓
Each claim has source number and confidence
```

Important structured output line:

```python
structured_llm = llm.with_structured_output(CitedAnswer)
```

This again uses schema-guided generation.

If it fails, the function returns `None`.

That allows fallback to the original plain answer path.

---

## 17. `print_cited_answer()`

Code location:

```text
Lines 716-737
```

Purpose:

Print cited answer nicely.

It prints:

```text
Summary
Claims with sources
Source file name
Page number
Confidence icon
```

Example style:

```text
1. CSS3 covers selectors.
   🟢 Source: Module 1-CSS3.pdf (page 0) | Confidence: high
```

This makes the RAG output much more professional.

---

## 18. Where Claim-Level Citation Is Used

Current usage is inside `chat` mode.

Code location:

```text
Lines 790-804
```

Flow:

```text
Retrieve docs
   ↓
generate_cited_answer()
   ↓
If successful:
      print_cited_answer()
   Else:
      fall back to plain answer_question()
```

Important lines:

```text
Line 791: cited_answer = generate_cited_answer(...)
Lines 793-794: print_cited_answer(...)
Lines 796-802: fallback to plain answer
```

This is safe design because the project still works even if structured citation fails.

---

## 19. Benefit of Claim-Level Citation

Before:

```text
Answer and sources were separate.
```

After:

```text
Each claim points to a source.
```

Benefits:

- Higher trust
- Better answer verification
- More professional RAG output
- Easier debugging
- Less hallucination risk
- Strong foundation for evaluation
- Helpful for enterprise/internal-document use cases

This is the difference between:

```text
"Here is an answer"
```

and:

```text
"Here is an answer, and here is exactly where each claim came from"
```

---

# 20. Complete Current Code Flow

## Command 1: Parse

```bash
python combined_document_intelligence.py parse
```

Code path:

```text
main()
  ↓
parse_all_pdfs()
  ↓
parse_course_pdf_if_needed()
  ↓
build_course_metadata()
  ↓
save_metadata_json()
```

Line locations:

```text
main(): Lines 837-855
parse_all_pdfs(): Lines 343-354
parse_course_pdf_if_needed(): Lines 330-340
build_course_metadata(): Lines 265-304
save_metadata_json(): Lines 307-312
```

---

## Command 2: Ingest

```bash
python combined_document_intelligence.py ingest --rebuild --parse
```

Code path:

```text
main()
  ↓
ingest_documents()
  ↓
load_all_documents_for_rag()
  ↓
load_pdf_pages_with_metadata()
  ↓
flatten_metadata_for_chroma()
  ↓
split_documents()
  ↓
create_vector_store()
```

Line locations:

```text
main(): Lines 837-855
ingest_documents(): Lines 455-467
load_all_documents_for_rag(): Lines 396-414
load_pdf_pages_with_metadata(): Lines 378-393
flatten_metadata_for_chroma(): Lines 360-375
split_documents(): Lines 417-424
create_vector_store(): Lines 434-442
```

---

## Command 3: Ask

```bash
python combined_document_intelligence.py ask "What topics are covered in CSS3?"
```

Current `ask` flow:

```text
main()
  ↓
run_ask()
  ↓
load_vector_store()
  ↓
answer_question()
  ↓
retrieve_docs()
  ↓
format_docs_for_prompt()
  ↓
LLM answer
  ↓
print_sources()
```

Line locations:

```text
run_ask(): Lines 744-758
answer_question(): Lines 586-627
retrieve_docs(): Lines 548-566
format_docs_for_prompt(): Lines 569-584
print_sources(): Lines 630-645
```

Important:

`ask` mode currently uses manual filters and normal answer generation.

---

## Command 4: Chat

```bash
python combined_document_intelligence.py chat
```

Current `chat` flow:

```text
main()
  ↓
run_chat()
  ↓
load_vector_store()
  ↓
parse_natural_query()
  ↓
retrieve_docs()
  ↓
generate_cited_answer()
  ↓
print_cited_answer()
```

Line locations:

```text
run_chat(): Lines 761-804
parse_natural_query(): Lines 499-521
retrieve_docs(): Lines 548-566
generate_cited_answer(): Lines 694-713
print_cited_answer(): Lines 716-737
```

This is the most advanced flow in the current version.

---

# 21. What Logic Was Added to the Older Project?

## Added Logic 1: Pydantic Structured Output

Added at:

```text
Lines 65-66
Lines 476-496
Lines 654-671
```

Purpose:

Instead of relying on free-form LLM text, the system now expects structured objects.

Used for:

```text
CourseQuery
Claim
CitedAnswer
```

---

## Added Logic 2: Query Construction

Added at:

```text
Lines 470-521
```

Purpose:

Natural language question becomes:

```text
subject filter
module filter
semantic query
```

---

## Added Logic 3: Query Construction in Chat Flow

Added at:

```text
Lines 778-788
```

Purpose:

Chat mode automatically detects filters before retrieval.

---

## Added Logic 4: Claim-Level Citation Schema

Added at:

```text
Lines 648-671
```

Purpose:

The model must produce claims with source numbers and confidence.

---

## Added Logic 5: Claim Extraction Prompt

Added at:

```text
Lines 674-691
```

Purpose:

Forces every answer claim to be backed by a numbered source.

---

## Added Logic 6: Cited Answer Generation

Added at:

```text
Lines 694-713
```

Purpose:

Generates structured cited answer from retrieved context.

---

## Added Logic 7: Cited Answer Printing

Added at:

```text
Lines 716-737
```

Purpose:

Displays claims, sources, pages, and confidence.

---

## Added Logic 8: Citation Flow in Chat

Added at:

```text
Lines 790-804
```

Purpose:

Chat mode now tries citation-based answering first, then falls back to plain answer if needed.

---

# 22. Why These Additions Matter

## Query Construction improves retrieval precision

Without Query Construction:

```text
Question: Module 1 ke CSS topics batao
```

The retriever may search the whole sentence.

With Query Construction:

```text
subject = CSS3
module = 1
semantic_query = topics covered
```

This makes retrieval more targeted.

---

## Claim-Level Citation improves trust

Without citation:

```text
CSS3 covers media queries.
```

User has to trust the model.

With citation:

```text
CSS3 covers media queries.
Source: Module 1-CSS3.pdf page 2
Confidence: high
```

Now the user can verify the answer.

---

## Structured output improves system reliability

Instead of parsing random LLM text manually, the system uses schemas:

```text
CourseQuery
CitedAnswer
Claim
```

This is more reliable and easier to extend later.

---

# 23. Current Stage Status

| Stage | Status |
|---|---|
| Multi-PDF loading | Done |
| Course metadata parser | Done |
| Metadata attached to chunks | Done |
| Chroma vector DB | Done |
| Manual subject/module filters | Done |
| Plain RAG answer | Done |
| Source display | Done |
| Query Construction | Added in chat mode |
| Claim-Level Citation | Added in chat mode |
| Claim confidence | Added |
| Fallback to plain answer | Added |
| Query Construction in ask mode | Planned |
| Citation in ask mode | Planned |
| Routing | Planned |
| Multi-Query | Planned |
| RAG-Fusion | Planned |
| Re-ranking | Planned |
| Evaluation | Planned |

---

# 24. Current Limitations

## 1. Query Construction is currently only in chat mode

Current:

```bash
python combined_document_intelligence.py chat
```

uses Query Construction.

But:

```bash
python combined_document_intelligence.py ask "Module 1 ke CSS topics batao"
```

still uses the plain ask flow.

Planned improvement:

```text
Add --auto or default query construction to ask mode.
```

---

## 2. Claim-Level Citation is currently only in chat mode

Current:

```bash
python combined_document_intelligence.py chat
```

tries Claim-Level Citation.

But:

```bash
python combined_document_intelligence.py ask "..."
```

prints normal answer + sources.

Planned improvement:

```text
Add --cite flag to ask mode.
```

Example:

```bash
python combined_document_intelligence.py ask "What topics are covered in CSS3?" --cite
```

---

## 3. Structured output depends on local model support

The code uses:

```python
llm.with_structured_output(...)
```

Some local models may not reliably follow structured schemas.

Fallback is already added, so the app does not crash.

---

# 25. Recommended Next Stage

The next recommended stage is:

```text
Query Construction in ask mode + optional citation flag
```

Planned commands:

```bash
python combined_document_intelligence.py ask "Module 1 ke CSS topics batao" --auto
```

```bash
python combined_document_intelligence.py ask "What topics are covered in CSS3?" --cite
```

This will make the CLI more powerful and more demo-friendly.

---

# 26. Future Stages

This project will be upgraded stage by stage.

## Stage: Routing

Automatically decide which subject/module route to search.

Example:

```text
"What are selectors?" → CSS3
"What is grid system?" → Bootstrap5
"What are joins?" → SQL
```

---

## Stage: Multi-Query

Generate multiple query variants for better recall.

Example:

```text
grid system
responsive columns
Bootstrap row column layout
mobile tablet desktop grid
```

---

## Stage: RAG-Fusion

Combine multiple ranked retrieval results using Reciprocal Rank Fusion.

---

## Stage: Re-ranking

Retrieve more candidates first, then choose the most relevant chunks.

---

## Stage: Decomposition

Break complex comparison questions into smaller sub-questions.

Example:

```text
Compare HTML5, CSS3, Bootstrap5, JavaScript, and SQL.
```

---

## Stage: Step-Back Retrieval

Retrieve broader conceptual context along with the original query.

Example:

```text
Original: Why use Bootstrap grid classes?
Step-back: What is responsive web design?
```

---

## Stage: HyDE

Generate a hypothetical answer passage first, then use it for retrieval.

Useful for vague queries like:

```text
grid?
```

---

## Stage: Evaluation

Add a test set and measure:

```text
correct source retrieved
answer generated
citation present
metadata displayed
```

---

## Stage: Streamlit UI

Build a UI for:

```text
PDF upload
Index build
Question answering
Source display
Citation display
```

---

# 27. Final Summary

This stage moves DocuMind RAG from a normal metadata-aware RAG system toward a more reliable, structured, and source-verifiable RAG assistant.

The two biggest upgrades are:

```text
Query Construction:
Natural language → structured filters + semantic query

Claim-Level Citation:
Answer → supported claims + source mapping + confidence
```

Together, these improve:

```text
retrieval precision
answer trust
source verification
system reliability
future extensibility
```

This stage is a strong foundation for the upcoming advanced RAG upgrades such as routing, multi-query retrieval, RAG-Fusion, re-ranking, decomposition, HyDE, and agentic RAG.
