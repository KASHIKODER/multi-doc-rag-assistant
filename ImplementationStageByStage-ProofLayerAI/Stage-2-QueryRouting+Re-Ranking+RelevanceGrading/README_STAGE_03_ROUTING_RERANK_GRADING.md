# Stage 03 — Routed, Re-Ranked, and Graded Multi-Document RAG

## Query Routing + Local Re-Ranking + CRAG-Style Relevance Grading

This document explains the latest advanced retrieval upgrade added to the Course Module RAG project.

The project already had:

- PDF loading
- Course metadata parsing
- Multi-document RAG
- Chroma vector database
- HuggingFace embeddings
- Ollama-based local answering
- Query Construction
- Topic Answer Mode
- Claim-Level Citation

This stage adds three important production-style retrieval improvements:

1. **Query Routing**
2. **Local Re-Ranking**
3. **Relevance Grading**

These upgrades make the system more reliable when the user asks short, incomplete, or implicit questions.

---

## 1. Why This Stage Was Needed

Earlier, the system worked well when the question clearly mentioned the subject.

Example:

```text
Explain the Bootstrap grid system.
```

The system could detect:

```text
subject = Bootstrap5
semantic_query = grid system explanation
```

But real users do not always mention the subject.

Example:

```text
What are selectors?
```

The user does not say `CSS3`, but the topic clearly belongs to CSS.

Another example:

```text
What are foreign keys?
```

The user does not say `SQL`, but the topic clearly belongs to SQL.

So the project needed a better retrieval control layer.

---

## 2. New Final Pipeline

The new chat-mode pipeline is:

```text
User Question
   ↓
Query Construction
   ↓
Query Routing
   ↓
Metadata-Aware Candidate Retrieval
   ↓
Local Re-Ranking
   ↓
Relevance Grading
   ↓
Topic Answer Mode OR Claim-Level Citation
   ↓
Source-Grounded Final Answer
```

This is a major improvement over simple RAG.

Earlier:

```text
Question → Retrieval → Answer
```

Now:

```text
Question → Understand → Route → Retrieve many → Re-rank → Grade → Answer with citations
```

---

## 3. What Changed at a High Level

| Upgrade | What It Does | Why It Matters |
|---|---|---|
| Query Routing | Infers subject when the user does not mention it | Handles implicit queries like “What are selectors?” |
| Re-Ranking | Reorders retrieved chunks by local relevance score | Best chunks move to the top |
| Relevance Grading | Checks if each retrieved chunk genuinely helps answer | Reduces weak context and hallucination risk |
| Retrieval Stats | Shows candidates, reranked docs, and kept docs | Makes debugging easier |
| Backward Compatibility | `ask` mode stays simple | Old commands do not break |

---

# 4. Advanced Retrieval Controls

## Code Location

```text
Lines 90-93
```

## Code

```python
RERANK_CANDIDATE_LIMIT = int(os.getenv("RERANK_CANDIDATE_LIMIT", str(FETCH_K)))
GRADE_CANDIDATE_LIMIT = int(os.getenv("GRADE_CANDIDATE_LIMIT", "6"))
MIN_GRADED_DOCS = int(os.getenv("MIN_GRADED_DOCS", "2"))
ENABLE_LLM_GRADING = os.getenv("ENABLE_LLM_GRADING", "true").lower() in {"1", "true", "yes", "on"}
```

## Explanation

These environment variables control the advanced retrieval pipeline.

### `RERANK_CANDIDATE_LIMIT`

This decides how many retrieved chunks are sent into re-ranking.

Earlier, the system directly used top `TOP_K` chunks.

Now the system can first retrieve more candidates and then select better chunks.

Example:

```text
FETCH_K = 12
TOP_K = 4
```

Meaning:

```text
Retrieve 12 possible chunks
Re-rank them
Use best 4
```

### `GRADE_CANDIDATE_LIMIT`

This controls how many re-ranked chunks are sent to the relevance grader.

This prevents the system from grading too many chunks and becoming slow.

### `MIN_GRADED_DOCS`

This is a safety guard.

If the grader becomes too strict and removes too many chunks, the system still keeps a minimum number of good chunks.

### `ENABLE_LLM_GRADING`

This allows you to turn LLM-based grading on or off.

For faster testing:

```powershell
$env:ENABLE_LLM_GRADING="false"
python .\Kashi-Mate-RAG-QueryConstructor-Rerank-Grading.py chat
```

This keeps routing and re-ranking active, but grading uses local heuristic fallback.

---

# 5. Query Construction

## Code Location

```text
Lines 523-744
```

## Main Schema

```python
class CourseQuery(BaseModel):
    subject: Optional[str]
    module: Optional[str]
    semantic_query: str
```

## What It Does

Query Construction converts a natural question into structured fields.

Example:

```text
Question:
Explain the Bootstrap grid system.

Output:
subject = Bootstrap5
module = None
semantic_query = grid system explanation
```

## Why It Matters

Without Query Construction, the retriever searches the raw user question.

With Query Construction, the retriever gets:

```text
clean semantic query + metadata filters
```

This improves retrieval precision.

---

## 6. Rule-Based Query Construction

## Code Location

```text
Lines 554-684
```

## Purpose

The function:

```python
rule_based_query_construction(user_input)
```

detects known subjects using explicit subject names and to pic aliases.

Example mapping:

```text
selectors       → CSS3
grid            → Bootstrap5
semantic tags   → HTML5
events          → JavaScript
foreign keys    → SQL
```

## Important Improvement

The code first checks explicit subject mentions.

Example:

```text
What table relationships are described in the SQL module?
```

This query contains the word `table`, which could confuse the router toward HTML.

But because the query explicitly says `SQL module`, the system correctly chooses:

```text
subject = SQL
```

This fixed a real bug where SQL relationship questions were incorrectly routed to HTML5.

---

# 7. RelevanceGrade Schema

## Code Location

```text
Lines 548-551
```

## Code

```python
class RelevanceGrade(BaseModel):
    relevant: bool
    reason: str
```

## What It Does

This schema is used by the relevance grader.

For every retrieved chunk, the grader returns:

```text
relevant = true / false
reason = short explanation
```

## Why It Matters

This is a CRAG-style idea.

Instead of blindly trusting retrieved chunks, the system asks:

```text
Does this chunk actually help answer the question?
```

---

# 8. Query Routing

## Code Location

```text
Lines 778-859
```

## What Is Query Routing?

Query Routing is the layer that runs when Query Construction cannot detect a subject.

Example:

```text
Question:
What are selectors?
```

The question does not mention CSS.

Query Routing checks topic keywords and infers:

```text
subject = CSS3
```

---

## Routing Keywords

## Code Location

```text
Lines 778-807
```

## Example

```python
ROUTING_KEYWORDS = {
    "CSS3": {
        "selector": 4,
        "selectors": 4,
        "box model": 4,
        "media query": 4,
    },
    "Bootstrap5": {
        "grid": 5,
        "grid system": 6,
        "navbar": 4,
    },
    "SQL": {
        "join": 5,
        "foreign key": 5,
        "table relationships": 5,
    },
}
```

## How It Works

Every subject has weighted topic keywords.

Higher weight means stronger signal.

Example:

```text
selectors → CSS3 score +4
grid system → Bootstrap5 score +6
foreign key → SQL score +5
```

The subject with the strongest score wins.

---

## Conservative Routing

## Code Location

```text
Lines 809-840
```

The router uses a conservative threshold:

```python
if best_score >= 4 and best_score >= second_score + 2:
```

## Meaning

The system routes only if:

1. The best subject has enough score.
2. It is clearly better than the second-best subject.

This avoids wrong routing for ambiguous queries.

Example ambiguous word:

```text
forms
```

Forms can appear in:

- HTML5
- Bootstrap5
- JavaScript

So the router should not force a subject unless the signal is strong.

---

## Applying Routing

## Code Location

```text
Lines 843-859
```

## Code

```python
def apply_query_routing(parsed, original_query):
    if parsed.subject:
        return None

    routing_decision = route_query_to_subject(original_query, parsed.semantic_query)

    if routing_decision:
        parsed.subject = routing_decision["subject"]
        return routing_decision
```

## Explanation

Routing only runs if Query Construction did not already detect a subject.

This is important.

If the user explicitly says:

```text
SQL module
```

the router should not override it.

---

# 9. Metadata-Aware Retrieval With Candidate Limit

## Code Location

```text
Lines 903-933
```

## What Changed

Earlier retrieval returned only top `TOP_K` docs.

Now `retrieve_docs()` supports:

```python
limit: int = TOP_K
fetch_k: int = FETCH_K
```

## Why This Matters

For `ask` mode:

```text
limit = TOP_K
```

So old behavior remains stable.

For `chat` mode:

```text
limit = RERANK_CANDIDATE_LIMIT
```

So the system gets more candidates for re-ranking.

## Benefit

This gives the re-ranker more options.

Instead of:

```text
retrieve 4 → answer
```

the system can do:

```text
retrieve 12 → re-rank → grade → answer with best 4
```

---

# 10. Local Re-Ranking

## Code Location

```text
Lines 935-1030
```

## What Is Re-Ranking?

Re-ranking means:

```text
Retrieve many chunks first.
Then reorder them by better relevance logic.
```

Vector search is good but not perfect.

Re-ranking improves the order of retrieved chunks.

---

## Tokenization

## Code Location

```text
Lines 935-945
```

```python
def retrieval_tokens(text: str) -> set:
```

This function removes common stopwords and keeps meaningful tokens.

Example:

```text
Question:
Explain the Bootstrap grid system.

Useful tokens:
bootstrap, grid, system
```

---

## Search Text

## Code Location

```text
Lines 947-959
```

```python
def doc_search_text(doc) -> str:
```

This combines:

- page content
- file name
- subject
- module title
- topics covered
- key concepts
- summary

## Why This Matters

Re-ranking should not only look at the raw chunk text.

Metadata is also useful.

Example:

```text
Chunk text may not mention CSS3 clearly,
but metadata subject = CSS3.
```

So metadata should help ranking.

---

## Re-Rank Score

## Code Location

```text
Lines 961-1010
```

```python
def doc_rerank_score(query, doc, subject=None, module=None):
```

This gives each chunk a score using:

1. Query-token overlap
2. Exact phrase match
3. Subject metadata match
4. Module metadata match
5. Topic/title metadata match

## Example

Question:

```text
Explain the Bootstrap grid system.
```

Chunk A:

```text
Grid classes, container, row, columns
```

Chunk B:

```text
Typography utilities and text-muted classes
```

Both may be from Bootstrap, but Chunk A should rank higher.

The re-ranker makes that happen.

---

## Re-Rank Function

## Code Location

```text
Lines 1012-1030
```

```python
def rerank_docs(query, docs, subject=None, module=None):
```

This sorts retrieved docs by their local score.

## Benefit

Better chunks reach the answer-generation stage.

This improves:

- answer quality
- citation quality
- grounding
- hallucination control

---

# 11. Relevance Grading

## Code Location

```text
Lines 1032-1164
```

## What Is Relevance Grading?

Relevance grading checks each retrieved chunk and asks:

```text
Is this chunk genuinely relevant to the user's question?
```

This is inspired by CRAG / Self-RAG style retrieval correction.

---

## Grading Prompt

## Code Location

```text
Lines 1032-1048
```

```python
RELEVANCE_GRADING_PROMPT = ChatPromptTemplate.from_template(...)
```

The prompt tells the model:

```text
Be strict.
If the chunk is only loosely related, mark relevant as false.
```

## Why It Matters

Without grading, weakly related chunks may enter the answer prompt.

With grading, weak chunks are filtered out.

---

## Heuristic Fallback Grading

## Code Location

```text
Lines 1050-1061
```

```python
def heuristic_relevance_grade(query, doc, subject=None):
```

If LLM grading is disabled or fails, the system uses local scoring.

This is important because the app should not break if local structured output fails.

---

## LLM-Based Grading

## Code Location

```text
Lines 1063-1080
```

```python
def grade_single_doc_with_llm(query, doc):
```

This asks Ollama to judge whether a chunk is relevant.

Because Ollama runs locally, it does not consume Groq/OpenAI quota.

---

## Grading Multiple Docs

## Code Location

```text
Lines 1082-1130
```

```python
def grade_docs_for_relevance(...)
```

This function:

1. Grades top re-ranked candidates.
2. Keeps relevant chunks.
3. Uses fallback if grading becomes too strict.

## Important Guardrail

```python
if len(kept_docs) < MIN_GRADED_DOCS:
```

If the grader removes too much, the system keeps some top re-ranked chunks anyway.

This prevents empty-context failures.

---

# 12. Combined Advanced Retrieval Pipeline

## Code Location

```text
Lines 1133-1164
```

## Function

```python
def retrieve_rerank_and_grade_docs(...)
```

## Flow

```text
retrieve_docs()
   ↓
rerank_docs()
   ↓
grade_docs_for_relevance()
   ↓
return final docs + stats
```

## Output Stats

This is why chat mode prints:

```text
Retrieval pipeline: candidates=5 | reranked=5 | kept_after_grading=2
```

## Why This Is Useful

This debug line tells you:

```text
How many docs were retrieved?
How many were re-ranked?
How many survived grading?
```

It makes the retrieval pipeline transparent.

---

# 13. Topic Answer Mode Still Works

## Code Location

```text
Lines 1446-1568
```

Topic Answer Mode is still deterministic.

It uses document metadata:

- topics_covered
- key_concepts
- learning_objectives

Example:

```text
Question:
List the important topics in JavaScript.

Output:
DOCUMENT-GROUNDED TOPIC ANSWER
```

## Why This Still Works After Routing/Re-Ranking/Grading

Routing/re-ranking/grading only improve which docs reach the topic-answer function.

The topic-answer function still reads metadata directly.

So it remains stable and fast.

---

# 14. Claim-Level Citation Still Works

## Code Location

```text
Lines 1259-1674
```

Claim-Level Citation still handles explanation questions.

Example:

```text
Question:
What are selectors?

Output:
CITATION-BACKED ANSWER
```

It prints:

- summary
- verified claims
- source file
- page number
- subject
- module
- confidence

This gives source-grounded answers.

---

# 15. Chat Mode Integration

## Code Location

```text
Lines 1745-1817
```

This is where all new pieces come together.

## Flow in `run_chat()`

```text
1. User enters question
2. parse_natural_query()
3. apply_query_routing()
4. retrieve_rerank_and_grade_docs()
5. print pipeline stats
6. if topic question → metadata answer
7. else → claim-level citation
8. fallback → plain RAG answer
```

## Important Code Logic

```python
parsed = parse_natural_query(query)
routing_decision = apply_query_routing(parsed, query)
docs, retrieval_stats = retrieve_rerank_and_grade_docs(...)
```

This is the heart of Stage 03.

---

# 16. Suggest Command

## Code Location

```text
Lines 1676-1726
```

The `suggest` command prints document-grounded test questions.

Run:

```powershell
python .\Kashi-Mate-RAG-QueryConstructor-Rerank-Grading.py suggest
```

## Why It Matters

It helps you ask questions that the PDFs can actually answer.

This avoids random unsupported questions.

---

# 17. Validated Outputs

## Test 1 — Query Routing

Question:

```text
What are selectors?
```

Output:

```text
Detected subject: CSS3
Retrieval pipeline: candidates=5 | reranked=5 | kept_after_grading=2
Source: Module 1-CSS3.pdf
```

This proves:

```text
Query Routing works.
```

---

## Test 2 — SQL Routing + Grading

Question:

```text
What table relationships are described in the SQL module?
```

Output:

```text
Detected subject: SQL
semantic_query: table relationships explanation
Retrieval pipeline: candidates=9 | reranked=9 | kept_after_grading=2
Source: Module 2-ANSI SQL Using MySQL.pdf
```

This proves:

```text
Explicit subject priority works.
Re-ranking works.
Grading works.
SQL source selection works.
```

---

# 18. Improvement Over Previous Version

## Before Stage 03

```text
User question
   ↓
Query Construction
   ↓
Retrieve top chunks
   ↓
Answer
```

## After Stage 03

```text
User question
   ↓
Query Construction
   ↓
Query Routing
   ↓
Retrieve more candidates
   ↓
Re-rank locally
   ↓
Grade relevance
   ↓
Answer with metadata or citations
```

## Practical Difference

Before:

```text
What are selectors?
```

could be weak or require the user to mention CSS.

After:

```text
What are selectors?
```

routes to CSS3 automatically.

Before:

```text
What table relationships are described in the SQL module?
```

could incorrectly route to HTML because of the word `table`.

After:

```text
SQL explicit mention wins.
```

---

# 19. Recommended Test Questions

## Topic Questions

These should produce:

```text
DOCUMENT-GROUNDED TOPIC ANSWER
```

Questions:

```text
List the important topics in JavaScript.
What topics are covered in the CSS3 module?
What does the HTML5 module cover about forms and semantic tags?
```

---

## Explanation Questions

These should produce:

```text
CITATION-BACKED ANSWER
```

Questions:

```text
What are selectors?
Explain the Bootstrap grid system.
What table relationships are described in the SQL module?
What are foreign keys?
```

---

## Hallucination Guard Questions

These should not hallucinate:

```text
What does the document say about React?
What does the document say about Docker deployment?
```

Expected:

```text
No supported claims found.
```

or a clear document-grounded refusal.

---

# 20. Performance Notes

## Why Some Answers Are Fast

Topic questions are fast because they use metadata directly.

Example:

```text
List the important topics in JavaScript.
```

This does not need full LLM answer generation.

## Why Some Answers Are Slower

Explanation questions may be slower because they use:

```text
LLM relevance grading
LLM claim-level citation
```

Both run locally through Ollama.

## Fast Testing Mode

To disable LLM grading:

```powershell
$env:ENABLE_LLM_GRADING="false"
python .\Kashi-Mate-RAG-QueryConstructor-Rerank-Grading.py chat
```

This keeps routing and re-ranking enabled, but uses local heuristic grading.

---

# 21. Project Rating

## Before Stage 03

```text
8.8 / 10
```

Strong, but still mostly metadata-aware RAG with citation support.

## After Stage 03

```text
9.4 / 10
```

Because the project now includes:

- query understanding
- implicit routing
- candidate re-ranking
- relevance grading
- source-safe citation
- deterministic metadata answers
- local-only pipeline

---

# 22. What Still Can Be Improved

To move closer to production level:

1. **Unit Tests**
   - Test query routing
   - Test metadata matching
   - Test topic answer mode
   - Test unsupported queries

2. **Evaluation Dataset**
   - Create a list of questions with expected source files.
   - Measure retrieval accuracy.

3. **Better Re-Ranker**
   - Use a cross-encoder reranker later.
   - Current re-ranking is local lexical + metadata scoring.

4. **UI**
   - Add Streamlit or FastAPI interface.

5. **Docker**
   - Make the project easier to run on another system.

6. **CI/CD**
   - Add automated checks before GitHub push.

---

# 23. Final Summary

Stage 03 converts the project from:

```text
Metadata-aware RAG assistant
```

into:

```text
Routed + re-ranked + graded source-grounded RAG assistant
```

The biggest improvement is that the system no longer blindly trusts first-pass retrieval.

It now:

```text
understands the question
routes it to the right subject
retrieves more candidates
re-ranks them locally
grades relevance
answers using metadata or verified claims
```

This makes the project much stronger for GitHub, LinkedIn, and interview discussion.

