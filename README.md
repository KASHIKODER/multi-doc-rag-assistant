# Metadata-Aware Multi-Document RAG Assistant

A production-style learning project that combines **Multi-Document RAG** and **Document Parsing / Metadata Extraction** into one practical document intelligence system.

The project reads multiple course-module PDFs, extracts useful module-level metadata, stores document chunks in a Chroma vector database, and answers questions using a local Ollama LLM with source-backed responses.

---

## 1. Project Overview

This project started as a hands-on extension of the **RAG From Scratch** learning path.

The initial goal was to understand the core RAG pipeline:

```text
Documents → Chunking → Embeddings → Vector Store → Retrieval → LLM Answer
```

After learning the individual RAG concepts from Part 1-17, this project was built to apply those ideas to a real-world use case:

```text
Multiple Course PDFs
        ↓
Local Course Metadata Parser
        ↓
Chunks + Metadata
        ↓
Chroma Vector Database
        ↓
Retriever + Optional Metadata Filters
        ↓
Ollama Local LLM
        ↓
Answer + Source References
```

---

## 2. What I Have Learned So Far

### RAG From Scratch: Part 1-17

Before building this project, I studied and implemented the major RAG concepts from scratch:

- Basic RAG pipeline
- Document loading
- Chunking
- Embeddings
- Vector stores
- Similarity search
- Retrieval
- Prompt-based generation
- Multi-Query Retrieval
- RAG-Fusion
- Decomposition
- Step-Back Prompting
- HyDE
- Routing
- Query Construction
- Multi-Representation Indexing
- RAPTOR-style hierarchical retrieval
- ColBERT-style retrieval idea
- Re-ranking
- Agentic RAG / CRAG-style flows

These concepts gave me the foundation to understand how a RAG system works internally and how each component improves retrieval quality, grounding, and answer reliability.

---

## 3. Two Major Concepts Added in This Project

This project combines two major document-intelligence concepts.

---

### Concept #5: Multi-Document RAG System

The first major concept is **Multi-Document RAG**.

Instead of answering from one document, the system reads a full folder of PDFs and builds a searchable knowledge base.

Current documents used for testing:

```text
Module 1-Bootstrap5.pdf
Module 1-CSS3.pdf
Module 1-HTML 5.pdf
Module 1-JavaScript.pdf
Module 2-ANSI SQL Using MySQL.pdf
```

The system can answer questions such as:

```text
What topics are covered in the CSS3 module?
Explain Bootstrap grid system based on the documents.
What SQL topics are covered in the MySQL module?
Compare HTML5, CSS3, Bootstrap5, JavaScript, and SQL based on these modules.
```

The answer is generated using retrieved context from the PDFs, and the system also prints the source chunks used.

---

### Concept #1: Document Parsing with LLMs / Metadata Extraction

The second major concept is **Document Parsing**.

Initially, the parsing concept was based on research-paper metadata extraction:

```text
PaperTitle
PublicationYear
Authors
AuthorContact
Abstract
SummaryAbstract
```

But the actual project documents were not research papers. They were course-module PDFs.

So the metadata schema was redesigned for course modules:

```text
ModuleTitle
Subject
ModuleNumber
TopicsCovered
LearningObjectives
KeyConcepts
Summary
```

This made the parser more aligned with the actual document type.

The current parser is local and rule-based, so it does not consume Groq or any external LLM quota.

Example metadata:

```json
{
  "DocumentType": "course_module",
  "ModuleTitle": "CSS3 Exercises",
  "Subject": "CSS3",
  "ModuleNumber": "1",
  "TopicsCovered": [
    "Why CSS? Inline vs. Internal vs. External",
    "CSS Syntax and Comments",
    "Selectors Playground",
    "Color & Background Styling",
    "Typography: Fonts and Text",
    "Link and List Styling",
    "Box Model & Layout Control",
    "Responsive Web Design with Media Queries"
  ],
  "LearningObjectives": [],
  "KeyConcepts": [],
  "Summary": "This module focuses on CSS3 and covers styling concepts for a local community event portal."
}
```

---

## 4. Why This Project Was Needed

The earlier RAG implementations helped me understand individual RAG techniques, but real-world document systems need more than a basic pipeline.

A practical document assistant should be able to:

- Read multiple PDFs
- Understand which document each chunk came from
- Preserve metadata such as subject, module number, and title
- Answer using only retrieved context
- Show source references for trust
- Work without depending fully on paid API quotas
- Be extendable with advanced retrieval techniques

This project is the first practical step toward that kind of real document intelligence system.

---

## 5. Current Architecture

```text
                    ┌──────────────────────────┐
                    │      Course PDFs          │
                    │  HTML / CSS / JS / SQL    │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Local Metadata Parser     │
                    │ subject, module, title    │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ PDF Loader + Chunking     │
                    │ Recursive Text Splitter   │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ HuggingFace Embeddings    │
                    │ all-MiniLM-L6-v2          │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Chroma Vector Database    │
                    │ chunks + metadata         │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Retriever                 │
                    │ semantic search           │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Ollama Local LLM          │
                    │ grounded answer           │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Answer + Sources          │
                    └──────────────────────────┘
```

---

## 6. Current Features

### Implemented

- Load multiple PDFs from a `data/` folder
- Extract course-module metadata locally
- Attach metadata to every document chunk
- Split PDFs into overlapping chunks
- Generate embeddings using HuggingFace
- Store chunks in Chroma vector database
- Load existing vector DB without rebuilding every time
- Ask questions through CLI
- Use Ollama locally for answering
- Show retrieved source chunks
- Display metadata-rich source references

Example source output:

```text
Module 1-CSS3.pdf | page=0 | subject=CSS3 | module=1 | title=CSS3 Exercises
```

---

## 7. Tech Stack

| Area | Tool |
|---|---|
| Language | Python |
| RAG Framework | LangChain |
| PDF Loading | PyPDFLoader |
| Text Splitting | RecursiveCharacterTextSplitter |
| Embeddings | HuggingFace sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | Chroma |
| Local LLM | Ollama Llama3 |
| Metadata Parser | Local rule-based parser |
| Environment Management | python-dotenv |
| Interface | CLI |

---

## 8. Project Setup

### 1. Create virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
.\venv\Scripts\activate
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Install Ollama and pull model

Install Ollama from the official website, then run:

```bash
ollama pull llama3
```

---

### 4. Create `.env`

```bash
copy .env.example .env
```

Recommended `.env`:

```env
DATA_DIR=./data
CHROMA_DIR=./chroma_db
METADATA_DIR=./data/extracted_metadata

COLLECTION_NAME=combined_docs
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=4
FETCH_K=12

OLLAMA_MODEL=llama3

HF_TOKEN=
HUGGINGFACEHUB_API_TOKEN=
HF_HUB_DISABLE_PROGRESS_BARS=1
TOKENIZERS_PARALLELISM=false
```

---

### 5. Add PDFs

Put PDFs inside:

```text
data/
```

Example:

```text
data/
├── Module 1-Bootstrap5.pdf
├── Module 1-CSS3.pdf
├── Module 1-HTML 5.pdf
├── Module 1-JavaScript.pdf
├── Module 2-ANSI SQL Using MySQL.pdf
```

---

## 9. Commands

### Parse course metadata

```bash
python combined_document_intelligence.py parse
```

Force re-parse:

```bash
python combined_document_intelligence.py parse --force
```

---

### Build vector database

```bash
python combined_document_intelligence.py ingest --rebuild --parse
```

---

### Ask a question

```bash
python combined_document_intelligence.py ask "What topics are covered in the CSS3 module?"
```

---

### Ask with subject filter

```bash
python combined_document_intelligence.py ask "Explain Bootstrap grid system based on the documents." --subject Bootstrap5
```

---

### Interactive chat

```bash
python combined_document_intelligence.py chat
```

---

## 10. Errors Faced and How They Were Solved

### Error 1: Ollama command not recognized

Error:

```text
ollama : The term 'ollama' is not recognized
```

Reason:

Ollama was not installed or was not available in the system PATH.

Fix:

- Install Ollama
- Restart PowerShell
- Verify installation

```bash
ollama --version
```

---

### Error 2: Python file not found

Error:

```text
can't open file 'combined_document_intelligence.py': [Errno 2] No such file or directory
```

Reason:

The project was extracted into a nested folder.

Actual structure:

```text
combined_document_intelligence_project/
└── combined_document_intelligence_project/
    └── combined_document_intelligence.py
```

Fix:

Move into the inner folder:

```bash
cd .\combined_document_intelligence_project
```

---

### Error 3: Dependencies installation cancelled

Error:

```text
ERROR: Operation cancelled by user
```

Reason:

The package installation was interrupted before completion.

Fix:

Use:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-user --no-cache-dir -r requirements.txt
```

---

### Error 4: No useful answer from RAG

Output:

```text
I don't know based on the provided documents.
```

Reason:

The `data/` folder did not contain any PDF files. Only `extracted_metadata/` folder existed.

Fix:

Add PDFs directly into:

```text
data/
```

Then rebuild:

```bash
python combined_document_intelligence.py ingest --rebuild
```

---

### Error 5: Sources showed blank metadata

Old output:

```text
Module 1-CSS3.pdf | page=0 | year= | title=
```

Reason:

The first parser schema was designed for research papers, not course modules.

Fix:

The parser schema was changed to course-module metadata:

```text
ModuleTitle
Subject
ModuleNumber
TopicsCovered
LearningObjectives
KeyConcepts
Summary
```

Updated output:

```text
Module 1-CSS3.pdf | page=0 | subject=CSS3 | module=1 | title=CSS3 Exercises
```

---

### Error 6: Answer added unnecessary "I don't know"

Old answer pattern:

```text
The CSS3 module covers...
I don't know based on the provided documents.
```

Reason:

The prompt was too strict and did not clearly prevent adding "I don't know" after a valid answer.

Fix:

Prompt was improved:

```text
If the context contains enough information to answer, answer directly.
Do NOT add "I don't know" after giving a valid answer.
```

---

## 11. Final Working Output

Example question:

```bash
python combined_document_intelligence.py ask "What topics are covered in the CSS3 module?"
```

Output:

```text
Answer:
Based on the provided documents, the topics covered in the CSS3 module include:

- Why CSS? Inline vs. Internal vs. External
- CSS Syntax and Comments
- Selectors Playground
- Color & Background Styling
- Typography: Fonts and Text
- Link and List Styling
- Box Model & Layout Control
- Multiple Columns in Text
- Responsive Web Design with Media Queries

Retrieved sources:
1. Module 1-CSS3.pdf | page=0 | subject=CSS3 | module=1 | title=CSS3 Exercises
2. Module 1-CSS3.pdf | page=1 | subject=CSS3 | module=1 | title=CSS3 Exercises
3. Module 1-CSS3.pdf | page=2 | subject=CSS3 | module=1 | title=CSS3 Exercises
```

This confirms that:

- PDFs are loaded correctly
- Chroma retrieval works
- Metadata is attached to chunks
- Ollama generates grounded answers
- Source references are displayed properly

---

## 12. What Makes This Project Different

This is not just a basic PDF chatbot.

The system is metadata-aware.

A normal RAG system may only retrieve chunks.

This project retrieves chunks with structured document identity:

```text
file_name
subject
module_number
module_title
topics_covered
summary
```

That makes the system more transparent, searchable, and easier to extend toward advanced query construction.

---

## 13. Future Roadmap

The next improvements will be added topic by topic.

---

### Query Construction

Current version supports manual filters:

```bash
--subject CSS3
--module 1
```

Future version will automatically convert natural language into structured filters.

Example:

```text
User: Module 1 ke CSS topics batao
```

System should infer:

```json
{
  "subject": "CSS3",
  "module": "1",
  "semantic_query": "topics covered"
}
```

This will connect directly to the Query Construction concept studied earlier.

---

### Routing

The system will route questions to the right module.

Example:

```text
What are selectors?
```

The router should identify that this is likely a CSS-related question and prioritize the CSS3 module.

Possible routes:

```text
HTML5
CSS3
Bootstrap5
JavaScript
SQL
General
```

---

### Multi-Query Retrieval

For vague questions, the system will generate multiple query variants.

Example:

```text
User query: grid system
```

Generated variants:

```text
Bootstrap grid system
responsive columns
container row column layout
mobile tablet desktop layout
```

This will improve recall.

---

### RAG-Fusion

After generating multiple query variants, the system will combine ranked results using Reciprocal Rank Fusion.

This will help identify documents that consistently appear near the top across different query views.

---

### Re-ranking

The system will retrieve more chunks initially, then re-rank them to select the best ones before sending context to the LLM.

This will improve answer quality and reduce irrelevant context.

---

### Decomposition

For broad or comparison-based questions, the system will split the question into smaller sub-questions.

Example:

```text
Compare HTML5, CSS3, Bootstrap5, JavaScript, and SQL.
```

Sub-questions:

```text
What does the HTML5 module cover?
What does the CSS3 module cover?
What does the Bootstrap5 module cover?
What does the JavaScript module cover?
What does the SQL module cover?
```

Then the final answer will combine all sub-answers.

---

### Step-Back Retrieval

For specific technical questions, the system will also retrieve broader conceptual context.

Example:

```text
Why use Bootstrap grid classes?
```

Step-back query:

```text
What is responsive web design?
```

This will help the system answer with both practical and conceptual grounding.

---

### HyDE Retrieval

For very short or vague questions, the system will first generate a hypothetical answer-style passage and use that for retrieval.

Example:

```text
Question: grid?
```

Hypothetical document:

```text
Bootstrap grid system uses containers, rows, and columns to create responsive layouts.
```

This can improve retrieval for ambiguous queries.

---

### Evaluation

A small evaluation set will be added to test retrieval quality.

Example:

```json
{
  "question": "What topics are covered in CSS3?",
  "expected_source": "Module 1-CSS3.pdf"
}
```

Metrics:

- correct source retrieved
- answer generated
- source shown
- metadata displayed

---

### Streamlit UI

A simple UI will be added for easier demos.

Planned features:

- Upload PDFs
- Build vector DB
- Ask questions
- Use subject filters
- Show answers
- Show sources

---

### Public Demo Mode

A clean terminal demo script will be added for LinkedIn/GitHub screenshots.

It will show:

- Loaded PDFs
- Metadata extraction
- Vector DB creation
- Example questions
- Answers with sources
- No API keys
- Clean output formatting

---

## 14. Current Status

| Feature | Status |
|---|---|
| Multi-PDF loading | Done |
| Local course metadata parser | Done |
| Metadata attached to chunks | Done |
| Chroma vector DB | Done |
| Ollama local answering | Done |
| Source references | Done |
| Manual subject/module filters | Done |
| Query construction | Planned |
| Routing | Planned |
| Multi-query retrieval | Planned |
| RAG-Fusion | Planned |
| Re-ranking | Planned |
| Decomposition | Planned |
| Step-back retrieval | Planned |
| HyDE | Planned |
| Evaluation | Planned |
| Streamlit UI | Planned |
| Public demo script | Planned |

---

## 15. Final Learning Summary

This project helped me move from tutorial-level RAG concepts to a real document intelligence system.

Earlier, I studied RAG components individually.

Now, I have implemented a working system that:

- reads multiple PDFs
- extracts course-specific metadata
- stores metadata with vector chunks
- retrieves relevant context
- answers using a local LLM
- displays reliable source references

This project will continue evolving as advanced RAG concepts are added one by one.

---

## 16. Safety Notes

Do not commit:

```text
.env
venv/
chroma_db/
data/*.pdf
data/extracted_metadata/*.json
```

Use `.env.example` for public configuration.

---

## 17. Project Direction

The final goal is to build a complete **metadata-aware, multi-document RAG assistant** that supports:

- semantic search
- structured metadata filtering
- query construction
- multi-query retrieval
- fusion ranking
- re-ranking
- decomposition
- step-back retrieval
- HyDE
- evaluation
- UI-based interaction

The project is being improved incrementally, with each update adding one advanced RAG concept in a clear and testable way.
