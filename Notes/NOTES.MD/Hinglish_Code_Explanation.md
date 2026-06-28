# combined_document_intelligence.py — Line-by-Line Explanation
> Hinglish mein, simple analogies ke saath, koi jargon nahi

---

## ⚡ PEHLE EK CHHOTA OVERVIEW

Yeh code ek smart Q&A system banata hai teri course PDFs ke upar. Kaam 3 steps mein hota hai:

**Step 1 — PARSE:** PDF files ka naam aur content padhke automatically metadata banao
(subject kya hai, topics kya hain, objectives kya hain) — bina kisi API call ke.

**Step 2 — INGEST:** PDFs ko chhote-chhote pieces (chunks) mein kaat ke unhe numbers
(vectors) mein convert karo aur ek local database mein store karo.

**Step 3 — ASK/CHAT:** User ka question lo, database mein relevant pieces dhundo,
local AI model (Ollama) se answer generate karo — zero API cost.

**Analogy:** Socho ek library mein books hain (PDFs). Pehle librarian books ka index
banata hai (Parse). Phir sab books ko scan karke index database mein daalta hai (Ingest).
Ab jab tu kuch puchhe, librarian index mein dhundh ke relevant page nikalta hai aur
answer deta hai (Ask).

---

## ⚠️ IMPORTANT — PEHLE PADHLO (Version Warning)

```python
from PyPDF2 import PdfReader
```

**Yeh library DEPRECATED ho chuki hai.** PyPDF2 ka last version 3.0.1 tha aur
ab yeh updates nahi leti. Official successor `pypdf` hai jo ab version **6.13.3** tak
aa chuka hai. Agar tu fresh project start kar raha hai toh `pypdf` use karna chahiye:

```bash
pip install pypdf          # sahi package
# pip install PyPDF2       # deprecated — mat use karo
```

`pypdf` mein import change hoga:
```python
from pypdf import PdfReader   # PyPDF2 ki jagah pypdf
# Baaki code same rehta hai — bas import change karo
```

**Current verified library versions (June 2026):**
| Library | Latest Version |
|---------|---------------|
| `pypdf` (PyPDF2 ka successor) | 6.13.3 |
| `langchain` | 1.3.11 |
| `langchain-ollama` | 1.1.0 |
| `langchain-huggingface` | 1.2.0 |
| `langchain-chroma` | 1.1.0 |
| `chromadb` | 1.5.9 |

---

## BLOCK 1 — DOCSTRING (Code ka Intro Comment)

```python
"""
COMBINED DOCUMENT INTELLIGENCE — COURSE MODULE VERSION

This version combines:

1. Course Module Metadata Parser
   Course PDF -> local metadata JSON

2. Multi-Document RAG
   PDFs + metadata -> chunks -> embeddings -> Chroma -> Ollama answer

Important:
- Course parser is LOCAL and does NOT consume Groq quota.
- RAG answering uses Ollama locally and does NOT consume Groq quota.

Commands:
    python combined_document_intelligence.py parse
    python combined_document_intelligence.py ingest --rebuild --parse
    python combined_document_intelligence.py ask "What topics are covered in CSS3?"
    python combined_document_intelligence.py chat
"""
```

**Kya hai yeh?** Triple quotes ke beech yeh text Python ka "docstring" hota hai — code
ka documentation jo code ke andar hi likhte hain. Jab koi `help(module)` call kare toh
yeh dikhta hai.

**"Course Module Version" kyu likha hai?** Kyunki yeh code ek pichle version ka
extension hai jisme scientific papers PDF se Groq LLM se metadata extract hota tha.
Us version mein `paper_title`, `authors`, `publication_year` nikalta tha. Is version mein
us Groq call ko completely hataa ke local regex-based parser daal diya — cost zero.

---

## BLOCK 2 — IMPORTS

```python
import argparse
```
Command-line arguments handle karne ke liye. Jab tu `python script.py ask "question"` 
likhta hai, `argparse` woh "ask" aur "question" parts parse karta hai.

```python
import json
```
JSON format mein data read/write karne ke liye. Metadata `data/extracted_metadata/Module1-CSS3.json`
mein save hota hai — yahi library kaam aati hai.

```python
import logging
```
Python ke built-in log system ko control karne ke liye. Yahan HuggingFace, LangChain
ki noisy warnings ko suppress karne ke liye use kiya hai.

```python
import os
```
Operating system se interact karne ke liye — mainly environment variables padhne ke liye
jaise `os.getenv("DATA_DIR", "./data")`.

```python
import re
```
Regular Expressions — text mein patterns dhundne ke liye. Is code mein sabse zyada use
hota hai topics aur module numbers extract karne ke liye. Real-world analogy: jaise Word
mein "Find & Replace" use karte ho, `re` isse programmatically karta hai.

```python
import shutil
```
File operations ke liye jo `os` se zyada powerful hain — jaise poora folder delete karna.
`shutil.rmtree(CHROMA_DIR)` se poori Chroma database folder delete hoti hai.

```python
import warnings
```
Python warnings system control karne ke liye. Libraries bahut saari deprecation/future
warnings print karti hain — inhe suppress karne ke liye.

```python
from pathlib import Path
```
File paths handle karne ka modern Python way. `./data/module.pdf` jaisi strings ki jagah
`Path("./data/module.pdf")` use karo — Windows aur Linux dono pe kaam karta hai
automatically (`\` vs `/`).

```python
from typing import Any, Dict, List, Optional
```
Type hints ke liye. Python loosely typed hai, yeh imports sirf readability ke liye hain:
- `Dict[str, Any]` → dictionary jisme keys strings hain, values kuch bhi
- `List[str]` → strings ki list
- `Optional[str]` → string ya None dono ho sakta hai

---

### Third-Party Imports:

```python
from dotenv import load_dotenv
```
`.env` file se environment variables load karta hai. `.env` file mein likha hota hai
`GROQ_API_KEY=abc123`. Yeh line us file ko padhke variables ko memory mein set kar deti hai.

**Analogy:** Jaise ghar ki safe mein passwords rakhe hain, `.env` file woh safe hai.
`load_dotenv()` safe kholta hai.

```python
from PyPDF2 import PdfReader
```
⚠️ Yeh DEPRECATED hai (upar dekho). PDF ke pages se raw text extract karta hai.

```python
from langchain_community.document_loaders import PyPDFLoader
```
LangChain ka PDF loader. Yeh PyPDF2 se alag kaise? PyPDF2/pypdf sirf text deta hai.
LangChain ka PyPDFLoader `Document` objects banata hai jinke saath metadata attach hoti
hai — yeh RAG ke liye perfect hai.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```
Long documents ko chhote pieces (chunks) mein kaat-ta hai. "Recursive" isliye kyunki
yeh intelligently kaat-ta hai — pehle paragraphs pe, phir lines pe, phir words pe.

**Analogy:** Ek lambi kitaab ko chapters mein, chapters ko pages mein, pages ko paragraphs
mein todna — yahi kaam yeh karta hai automatically.

```python
from langchain_huggingface import HuggingFaceEmbeddings
```
Text ko numbers (vectors) mein convert karta hai. Model: `all-MiniLM-L6-v2`. Yeh model
offline kaam karta hai, koi internet/API nahi chahiye query time pe.

**Analogy:** Yeh ek "meaning calculator" hai. "CSS selectors" aur "CSS targeting elements"
ko similar numbers milenge kyunki dono ka matlab same hai. Calculator in numbers ke basis
pe compare kar sakta hai.

```python
from langchain_chroma import Chroma
```
Vector database. Yeh un numbers (embeddings) ko store karta hai aur "is question se
milta-julta content kahan hai?" dhundh sakta hai.

**Analogy:** Ek library catalog jisme books sirf numbers se dhundhi jaati hain — naam se
nahi, meaning se.

```python
from langchain_ollama import ChatOllama
```
Local Ollama LLM se baat karne ka interface. Ollama tera computer pe locally run hota
hai — Groq/OpenAI pe nahi jaata.

```python
from langchain_core.prompts import ChatPromptTemplate
```
LLM ko dene wale prompt ka template banata hai. Variables fill-in-the-blank style mein
insert hote hain.

**Analogy:** Jaise form mein blank spaces hoti hain — "Dear {name}, your order {order_id}
has shipped." — ChatPromptTemplate exactly yahi karta hai AI ke liye.

```python
from langchain_core.output_parsers import StrOutputParser
```
LLM ka response (jo `AIMessage` object hota hai) ko plain Python string mein convert
karta hai. Bina iske raw object milta, string nahi.

---

### Warning Suppression Block:

```python
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*langchain-community.*")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*HF Hub.*")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
```

**Kya ho raha hai?** Libraries install hoti hain toh chhoti-chhoti warnings print karti
hain — "yeh deprecated hai", "please authenticate", "progress bars disabled" etc. User
ke liye yeh spam hai. Is block se sab suppress kar diya.

`logging.ERROR` level set karne ka matlab: sirf real errors dikhenge (library fail ho
jaaye tab), warnings nahi.

`.*langchain-community.*` mein `.*` regex hai — `.*` matlab kuch bhi. "Koi bhi warning
message jisme 'langchain-community' ho — ignore karo."

---

## BLOCK 3 — ENV + CONFIG

```python
load_dotenv()
```
`.env` file padhta hai. Yeh sirf ek baar call karna hota hai, usually file ke shuru mein.

```python
DATA_DIR     = Path(os.getenv("DATA_DIR",     "./data"))
CHROMA_DIR   = Path(os.getenv("CHROMA_DIR",   "./chroma_db"))
METADATA_DIR = Path(os.getenv("METADATA_DIR", "./data/extracted_metadata"))
```

`os.getenv("DATA_DIR", "./data")` — pehle `.env` file ya environment mein `DATA_DIR`
dhundho. Agar mile toh use lo, agar nahi mile toh default `"./data"` use karo.

`Path(...)` — string ko `Path` object mein wrap karo taaki `DATA_DIR / "file.pdf"` jaise
operations kaam karein.

```python
COLLECTION_NAME  = os.getenv("COLLECTION_NAME", "combined_docs")
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "llama3")
```

**COLLECTION_NAME:** Chroma DB ke andar ek "collection" hoti hai — socho database ke
andar ek table. Yeh uska naam hai.

**EMBEDDING_MODEL:** Kaun sa HuggingFace model text → vector convert karega. `all-MiniLM-L6-v2`
chhota, fast, aur offline hai.

**OLLAMA_MODEL:** Local mein kaun sa LLM answers generate karega.

```python
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE",    "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K         = int(os.getenv("TOP_K",         "4"))
FETCH_K       = int(os.getenv("FETCH_K",       "12"))
```
       
`int(os.getenv(...))` — environment variables strings mein hoti hain, `int()` se
number mein convert karo.

**CHUNK_SIZE=1000:** Ek piece mein maximum 1000 characters.

**CHUNK_OVERLAP=200:** Do adjacent pieces ke beech 200 characters common rahenge.
Kyun? Agar koi important sentence chunk ke end mein aadhi cut gayi toh next chunk
mein bhi rahegi — information miss nahi hogi.

```
Bina overlap:        [0-1000] [1000-2000] [2000-3000]
Overlap ke saath:    [0-1000] [800-1800]  [1600-2600]
                               ↑200 char overlap↑
```

**TOP_K=4:** Final answer ke liye sirf top 4 relevant chunks use karo.

**FETCH_K=12:** Similarity search mein pehle 12 candidates fetch karo, phir filter
lagao, phir top 4 rakho. Zyada fetch isliye kyunki filter ke baad bahut kam bachte hain.

```python
os.environ["TOKENIZERS_PARALLELISM"]       = os.getenv("TOKENIZERS_PARALLELISM", "false")
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = os.getenv("HF_HUB_DISABLE_PROGRESS_BARS", "1")
```

**TOKENIZERS_PARALLELISM=false:** HuggingFace tokenizer parallel threads use karta hai.
Multi-processing environments mein yeh deadlock create kar sakta hai — "false" se
safe single-thread mode on hota hai.

**HF_HUB_DISABLE_PROGRESS_BARS=1:** Jab model download ho, progress bar mat dikhaao.
Clean output ke liye.

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

Yeh ek fallback template hai. Jab bhi metadata load karna ho aur kuch miss ho jaaye
(file corrupt ho, field na ho) — toh crash hone ki jagah yeh empty template use hoga.

**`Dict[str, Any]`:** Type hint — dictionary jisme keys strings hain (`"Subject"` etc.)
aur values kuch bhi ho sakti hain (string, list, etc.)

---

## BLOCK 4 — DISPLAY HELPERS

Yeh simple utility functions hain — sirf terminal output ko sundar banane ke liye:

```python
def section(title: str):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
```

`"=" * 72` — `=` character 72 baar repeat karo. Output:
```
========================================================================
COURSE MODULE PARSING — PDF TO JSON METADATA
========================================================================
```

```python
def status(label: str, value: str):
    print(f"✅ {label}: {value}")

def info(label: str, value: str):
    print(f"• {label}: {value}")

def warn(message: str):
    print(f"⚠️ {message}")
```

`f"..."` — f-string, Python 3.6+ mein aaya. `{label}` placeholder automatically
value se replace ho jaata hai. Yeh pehle waale `.format()` se faster aur readable hai.

```python
def clean_preview(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "..."
```

**Line 1:** `re.sub(r"\s+", " ", str(text))` — regex se multiple spaces/newlines/tabs
ko single space se replace karo.
- `r"\s+"` — `\s` matlab any whitespace (space, tab, newline), `+` matlab ek ya zyada
- `" "` — isse replace karo single space se

`.strip()` — starting/ending whitespace hata do.

**Line 2:** Agar text limit se chhota hai toh as-is return karo, warna pehle 260
characters lo aur `"..."` lagao.

`text[:limit].rstrip()` — pehle `limit` characters lo, phir `.rstrip()` se trailing
whitespace hata do (taaki `"Hello world   ..."` ki jagah `"Hello world..."` aaye).

```python
def ensure_folders():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
```

`mkdir(parents=True, exist_ok=True)` —
- `parents=True`: Agar `./data/extracted_metadata/` chahiye aur `./data/` exist nahi
  karta, toh dono banao automatically.
- `exist_ok=True`: Agar folder already exist karta hai toh error mat do — chup-chaap
  skip karo.

```python
def get_pdf_files() -> List[Path]:
    ensure_folders()
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in '{DATA_DIR}'. Add PDFs first.")
    return pdfs
```

`DATA_DIR.glob("*.pdf")` — `data/` folder mein saari `.pdf` extension wali files
dhundho. `*` wildcard hai — kuch bhi match karo.

`sorted(...)` — alphabetical order mein sort karo. Consistent order important hai taaki
har run pe same sequence mile.

`raise FileNotFoundError(...)` — agar koi PDF nahi mili toh custom error message ke
saath exception throw karo. Program crash ho jaayega is useful message ke saath.

---

## BLOCK 5 — COURSE MODULE METADATA PARSER

Yeh section ka kaam: PDF file ka naam aur content padhke JSON metadata banana — bina
kisi API (Groq/OpenAI) ke.

**Pichle version se comparison:** Pichle scientific-papers version mein Groq LLM ko
raw text bheja jaata tha aur woh JSON return karta tha — expensive aur quota consume
karta tha. Is course-module version mein yeh kaam pure Python (regex + heuristics) se
ho raha hai — free.

---

### `extract_text_from_pdf(pdf_path, max_pages=None)`

```python
def extract_text_from_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    
    total = len(reader.pages)
    limit = min(total, max_pages) if max_pages else total
```

`PdfReader(str(pdf_path))` — PyPDF2 ka reader object banao. `str(pdf_path)` isliye
kyunki `Path` object ko string mein convert karna padta hai kuch purani libraries ke liye.

`len(reader.pages)` — PDF mein kitne pages hain.

`min(total, max_pages) if max_pages else total` — Ternary operator:
```
max_pages diya hai? 
→ YES → min(total, max_pages)  [jitna diya ya total, jo chhota ho]
→ NO  → total  [sab pages]
```

**Kyun sirf 3 pages?** Parse step mein `max_pages=3` pass hota hai kyunki course ka
table of contents usually first 3 pages mein hi hota hai. Baki pages padhne ki zarurat
nahi.

```python
    for idx in range(limit):
        try:
            text = reader.pages[idx].extract_text() or ""
            pages.append(f"\n\n--- PAGE {idx + 1} ---\n{text}")
        except Exception as e:
            warn(f"Could not extract page {idx + 1} from {pdf_path.name}: {e}")
    
    return "\n".join(pages)
```

`reader.pages[idx].extract_text()` — page se text nikalo. Kuch pages pe fail ho sakta
hai (scanned images, encrypted PDF) — isliye `try/except`.

`or ""` — agar `extract_text()` `None` return kare toh empty string le lo. Python mein
`None or ""` ka result `""` hota hai.

`f"\n\n--- PAGE {idx + 1} ---\n{text}"` — har page ke aage marker lagao taaki baad mein
pata chale kahan se kahan tak kahan ka text hai. `idx + 1` isliye kyunki `range(limit)`
0 se start karta hai, pages 1 se shuru hoti hain.

---

### `metadata_path_for(pdf_path)`

```python
def metadata_path_for(pdf_path: Path) -> Path:
    return METADATA_DIR / f"{pdf_path.stem}.json"
```

`pdf_path.stem` — filename bina extension ke.
`Path("data/Module 1-CSS3.pdf").stem` → `"Module 1-CSS3"`

`METADATA_DIR / f"{pdf_path.stem}.json"` — Path objects mein `/` operator folder join
karta hai:
`Path("./data/extracted_metadata") / "Module 1-CSS3.json"` → `"./data/extracted_metadata/Module 1-CSS3.json"`

---

### `guess_module_number(filename)`

```python
def guess_module_number(filename: str) -> str:
    match = re.search(r"module\s*(\d+)", filename, flags=re.IGNORECASE)
    return match.group(1) if match else ""
```

**Regex breakdown:** `r"module\s*(\d+)"`
- `module` → literally "module"
- `\s*` → zero ya zyada whitespace (tab, space) — "Module1" aur "Module 1" dono match
- `(\d+)` → ek ya zyada digits — `()` capture group hai, `\d` digit hai, `+` ek ya zyada

`re.IGNORECASE` → "module", "Module", "MODULE" sab match.

`match.group(1)` → pehla capture group (jo `(\d+)` ne pakda).

Examples:
```
"Module 1-CSS3.pdf"   → "1"
"module3-html.pdf"    → "3"
"Bootstrap5.pdf"      → "" (koi match nahi)
```

---

### `guess_subject_from_filename(filename)`

```python
def guess_subject_from_filename(filename: str) -> str:
    stem = Path(filename).stem           # "Module 1-Bootstrap5"
    if "-" in stem:
        subject = stem.split("-", 1)[1]  # "Bootstrap5"
    else:
        subject = re.sub(r"module\s*\d+", "", stem, flags=re.IGNORECASE)
    
    subject = subject.replace("_", " ").strip()
    subject = re.sub(r"\s+", " ", subject)
    return subject
```

`stem.split("-", 1)` — string ko `-` pe split karo, lekin sirf ek baar (second argument
`1` = max splits). Result list hogi:
```
"Module 1-Bootstrap5".split("-", 1) → ["Module 1", "Bootstrap5"]
[1] → "Bootstrap5"
```

`re.sub(r"module\s*\d+", "", stem, flags=re.IGNORECASE)` — "module" + spaces + digits
ko empty string se replace karo.
`"HTML5module2"` → `"HTML5"` (module2 hata diya)

`.replace("_", " ")` — underscore ko space mein badlo.
`.strip()` — leading/trailing whitespace hata do.
`re.sub(r"\s+", " ", subject)` — multiple spaces ko single space mein badlo.

---

### `first_meaningful_line(text)`

```python
def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 5 and not line.startswith("--- PAGE"):
            return line
    return ""
```

`text.splitlines()` — text ko lines mein todo (`\n` pe split).

Har line check karo:
- `len(line) >= 5` — at least 5 characters hone chahiye (single words skip)
- `not line.startswith("--- PAGE")` — hamara artificial page marker skip karo

Pehli valid line milte hi return. Yeh module title ban sakti hai.

---

### `extract_numbered_topics(text)` — Sabse Complex Function

```python
def extract_numbered_topics(text: str) -> List[str]:
    topics = []
    
    # METHOD 1: Line-wise
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())
        match = re.match(r"^(\d{1,2})\.\s+(.{4,100})$", line)
```

**Regex:** `r"^(\d{1,2})\.\s+(.{4,100})$"`
- `^` → line ka shuru
- `(\d{1,2})` → 1 ya 2 digits (topics 1-99 handle karta hai)
- `\.` → literal dot (`.` normally "any char" hota hai, `\.` se escape karo)
- `\s+` → ek ya zyada whitespace
- `(.{4,100})` → 4 se 100 characters kuch bhi — topic text
- `$` → line ka end

`re.match(...)` — sirf line ke shuru se match karta hai (`re.search` kahin bhi dhundta hai).

Examples jo match karte hain:
```
"1. Why CSS?"                        → groups: ("1", "Why CSS?")
"18. Bootstrap 5 JavaScript Plugins" → groups: ("18", "Bootstrap 5 JavaScript Plugins")
"Module Overview"                    → match nahi (number nahi hai)
```

```python
        if match:
            candidate = match.group(2).strip()
            candidate = re.split(r"\s+Exercise\s+\d", candidate)[0].strip()
```

`re.split(r"\s+Exercise\s+\d", candidate)[0]` — agar topic ke saath exercise number
attached ho jaise "Why CSS? Exercise 1" toh "Exercise 1" hata do, sirf "Why CSS?" rakho.
`[0]` — split ke baad pehla element lo.

```python
    # METHOD 2: Agar PDF ne lines merge kar diye
    if len(topics) < 3:
        pattern = r"(?:^|\s)(\d{1,2})\.\s+([A-Z][A-Za-z0-9 &:/,()\-]+?)(?=\s+Exercise\s+\d|\s+\d{1,2}\.\s+[A-Z]|\n|$)"
        for _, candidate in re.findall(pattern, text):
```

**Kyun Method 2?** Kuch PDFs text extract karte waqt lines merge kar dete hain — ek
lambi string bana dete hain jisme sab topics ek saath hain. Line-wise Method 1 fail ho
jaata hai. Broader regex ek badi string mein bhi topics dhundh sakti hai.

**Method 2 Regex breakdown:**
- `(?:^|\s)` — line start ya whitespace (non-capturing `(?:...)`)
- `(\d{1,2})` — 1-2 digit number
- `\.\s+` — dot + spaces
- `([A-Z][A-Za-z0-9 &:/,()\-]+?)` — Capital letter se shuru, phir valid chars (lazy `?`)
- `(?=...)` — "lookahead" — yahan khatam hota hai agar Exercise, ya next numbered topic, ya newline aaye

```python
    # De-duplicate while preserving order
    seen = set()
    unique = []
    for topic in topics:
        key = topic.lower()
        if key not in seen:
            seen.add(key)
            unique.append(topic)
    
    return unique[:20]
```

**De-duplication:** Method 1 aur 2 dono se duplicates aa sakte hain. Set mein lowercase
key rakhte hain (`seen`) — "Why CSS?" aur "why css?" same key hai toh duplicate skip.
`unique` list mein original case preserve hota hai.

`unique[:20]` — max 20 topics return karo (zyada hone pe truncate).

---

### `subject_key_concepts(subject)`

```python
def subject_key_concepts(subject: str) -> List[str]:
    s = subject.lower()
    
    if "bootstrap" in s:
        return ["Bootstrap setup", "Containers and rows", ...]
    if "css" in s:
        return ["CSS syntax", "Selectors", ...]
    # ...
    return []
```

Yeh hardcoded knowledge hai — per-subject manually likhaa key concepts ki list. Jab
regex se topics nahi nikle ya list incomplete ho tab yeh fallback kaam aata hai.

`subject.lower()` → case-insensitive comparison ke liye.
`"bootstrap" in s` → partial match — "Bootstrap5", "Bootstrap 5", "Bootstrap CSS" sab
match karenge.

---

### `build_course_metadata(pdf_path)` — Sab Parts Ek Saath

```python
def build_course_metadata(pdf_path: Path) -> Dict[str, Any]:
    text = extract_text_from_pdf(pdf_path, max_pages=3)
    subject = guess_subject_from_filename(pdf_path.name)
    module_number = guess_module_number(pdf_path.name)
    
    first_line = first_meaningful_line(text)
    topics = extract_numbered_topics(text)
    key_concepts = subject_key_concepts(subject)
```

Pehle sabse chhoti, fast cheezein — filename se guess karo. Phir PDF text padhke
topics nikalo.

```python
    if first_line and len(first_line) < 120:
        module_title = first_line
    else:
        module_title = f"{subject} Module"
```

Agar PDF ki pehli valid line reasonable hai (120 chars se chhoti) toh woh module title.
Warna fallback: `"CSS3 Module"`.

```python
    if not topics and key_concepts:
        topics = key_concepts
```

Agar PDF se topics extract nahi hue (khali list) lekin subject ke hardcoded concepts
hain — unhe hi topics maan lo.

```python
    learning_objectives = [
        f"Understand and practice {topic.lower()}."
        for topic in topics[:8]
    ]
```

List comprehension — topics se automatically learning objectives generate karo.
`topics[:8]` — max 8 objectives.

Example: `"Why CSS?"` → `"Understand and practice why css?."`

```python
    if topics:
        summary = (
            f"This module focuses on {subject}. It covers topics such as "
            f"{', '.join(topics[:6])}."
        )
    else:
        summary = f"This module focuses on {subject}."
```

`', '.join(topics[:6])` — pehle 6 topics ko comma+space se join karo:
`["CSS syntax", "Selectors", "Box model"]` → `"CSS syntax, Selectors, Box model"`

---

### `save_metadata_json(pdf_path, metadata)`

```python
def save_metadata_json(pdf_path: Path, metadata: Dict[str, Any]):
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    path = metadata_path_for(pdf_path)
    path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
```

`json.dumps(metadata, indent=2, ensure_ascii=False)`:
- `json.dumps()` — Python dict ko JSON string mein convert karo
- `indent=2` — 2-space indentation (pretty-print, readable)
- `ensure_ascii=False` — Unicode characters (Hindi, Chinese etc.) as-is save karo,
  escape codes mein nahi

`path.write_text(content, encoding="utf-8")` — file mein likho.

---

### `load_metadata_json(pdf_path)`

```python
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
```

`DEFAULT_COURSE_METADATA.copy()` — `.copy()` zaruri hai. Agar directly assign karo
`normalized = DEFAULT_COURSE_METADATA` toh dono same object point karenge — ek mein
change dono mein aayega. `.copy()` ek alag copy banata hai.

**Safe merge:**
```python
for key in normalized:
    normalized[key] = parsed.get(key, normalized[key])
```
`parsed.get(key, default)` — agar JSON mein yeh key hai toh uski value lo, warna
default (jo `normalized[key]` hai — empty string ya empty list) rakho.

**Kyun?** JSON file corrupt ho sakti hai, ya purani version mein koi field na ho — crash
hone ki jagah gracefully default use karo.

---

### `parse_course_pdf_if_needed(pdf_path, force_parse=False)`

```python
def parse_course_pdf_if_needed(pdf_path: Path, force_parse: bool = False) -> Dict[str, Any]:
    path = metadata_path_for(pdf_path)
    
    if path.exists() and not force_parse:
        info("Metadata loaded", path.name)
        return load_metadata_json(pdf_path)
    
    info("Parsing course metadata locally", pdf_path.name)
    metadata = build_course_metadata(pdf_path)
    save_metadata_json(pdf_path, metadata)
    return metadata
```

Smart caching — agar JSON already bana hua hai toh dobara parse mat karo (time waste):
```
JSON exists? 
  → YES + force=False → Load from JSON (fast)
  → YES + force=True  → Re-parse PDF (fresh)
  → NO               → Parse PDF → Save JSON → Return
```

---

## BLOCK 6 — RAG INGESTION

### `flatten_metadata_for_chroma(raw, pdf_path)`

```python
def flatten_metadata_for_chroma(raw: Dict[str, Any], pdf_path: Path) -> Dict[str, Any]:
    topics = raw.get("TopicsCovered", [])
    
    return {
        "file_name": pdf_path.name,
        "topics_covered": " | ".join(topics) if isinstance(topics, list) else str(topics),
        # ...
    }
```

**Kyun flatten?** Chroma metadata mein sirf simple values store ho sakti hain: string,
int, float. List (`["Why CSS?", "Selectors"]`) directly store nahi ho sakti.

Solution — list ko pipe-separated string mein convert karo:
`["Why CSS?", "Selectors", "Box model"]` → `"Why CSS? | Selectors | Box model"`

`isinstance(topics, list)` — check karo ki `topics` list hai ya nahi (corrupted data
ke liye safeguard).

---

### `load_pdf_pages_with_metadata(pdf_path, parse_metadata, force_parse)`

```python
def load_pdf_pages_with_metadata(pdf_path, parse_metadata, force_parse):
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
```

`PyPDFLoader.load()` — LangChain ka PDF loader. Returns list of `Document` objects —
ek per page. Har Document ke paas:
- `page.page_content` — page ka text
- `page.metadata` — dict with `{"source": "path/to/file.pdf", "page": 0}`

`page.metadata.update(flat_meta)` — hamari custom metadata merge karo existing metadata
mein. Ab har page ko pata hai woh kis subject ka hai, kaunse module ka hai.

**Analogy:** Socho 50 pages ek folder mein hain. Pehle har page pe sirf page number
likha tha. Ab hum har page pe sticky note lagaate hain: "Subject: CSS3, Module: 1,
Topics: Selectors, Box Model..."

---

### `split_documents(documents)`

```python
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,       # 1000 chars
        chunk_overlap=CHUNK_OVERLAP, # 200 chars
    )
    chunks = splitter.split_documents(documents)
    return chunks
```

**RecursiveCharacterTextSplitter algorithm (step by step):**
1. Pehle `"\n\n"` (paragraph breaks) pe split karo
2. Agar chunk still > 1000 chars → `"\n"` pe split karo
3. Agar still too big → `" "` (space) pe split karo
4. Agar still too big → character-by-character split karo

Metadata automatically carry over hoti hai — har chunk ko pata hai woh kis page se aaya.

---

### `get_embedding_function()`

```python
def get_embedding_function():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        show_progress=False,
    )
```

HuggingFace ka embedding model load karo. First time mein model download hoga (~22MB).
Next time cached rahega.

**Embedding kya hota hai?**
```
"CSS selectors target HTML elements"
         ↓ model ke andar
[0.23, -0.11, 0.87, ..., 0.56]   ← 384 numbers
```

Similar meaning wale texts → similar numbers. Yeh numbers compare karke "kaun sa chunk
most relevant hai" pata chalta hai.

---

### `create_vector_store(chunks)` vs `load_vector_store()`

```python
def create_vector_store(chunks):
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding_function(),
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )
    return vector_store

def load_vector_store():
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embedding_function(),
        collection_name=COLLECTION_NAME,
    )
    return vector_store
```

**Dono mein farq:**
| | `create_vector_store` | `load_vector_store` |
|---|---|---|
| Kab use hota hai | First time / rebuild | Har query pe |
| Kya karta hai | Chunks + embeddings likhta hai | Existing DB se load karta hai |
| Speed | Slow (ek baar) | Fast (seconds) |

`Chroma.from_documents()` → nayi DB banao, documents daalo, disk pe save karo.
`Chroma(persist_directory=...)` → existing disk DB se load karo.

---

### `ingest_documents(rebuild, parse_metadata, force_parse)`

```python
def ingest_documents(rebuild=False, parse_metadata=False, force_parse=False):
    if rebuild and CHROMA_DIR.exists():
        warn("Rebuild enabled. Removing old Chroma DB.")
        shutil.rmtree(CHROMA_DIR)  # Poora folder delete
    
    if CHROMA_DIR.exists() and not rebuild:
        info("Existing Chroma DB", "Already exists. Use --rebuild to recreate.")
        return load_vector_store()
    
    documents = load_all_documents_for_rag(parse_metadata, force_parse)
    chunks = split_documents(documents)
    return create_vector_store(chunks)
```

`shutil.rmtree(CHROMA_DIR)` — recursive tree remove — folder aur usके andar saab kuch
delete. `os.remove()` sirf files delete karta hai, folders nahi. `shutil.rmtree()`
nested folders bhi handle karta hai.

---

## BLOCK 7 — QUESTION ANSWERING

### `metadata_matches(doc, subject, module, title)`

```python
def metadata_matches(doc, subject=None, module=None, title=None) -> bool:
    meta = doc.metadata
    
    if subject and subject.lower() not in str(meta.get("subject", "")).lower():
        return False
    
    if module and str(module).lower() != str(meta.get("module_number", "")).lower():
        return False
    
    if title and title.lower() not in str(meta.get("module_title", "")).lower():
        return False
    
    return True
```

**Short-circuit evaluation:** Agar `subject` filter diya hai aur match nahi kiya toh
`False` return karo — baaki checks mat karo. Python mein `if a and b` mein agar `a`
False hai toh `b` evaluate hi nahi hota.

**Filter types:**
- `subject` → substring match (case-insensitive): `"css3" in "CSS3"` ✅
- `module` → exact match: `"1" == "1"` ✅, `"1" == "2"` ❌
- `title` → substring match: `"grid" in "Bootstrap Grid System"` ✅

---

### `retrieve_docs(query, vector_store, subject, module, title)`

```python
def retrieve_docs(query, vector_store, subject=None, module=None, title=None):
    candidates = vector_store.similarity_search(query, k=FETCH_K)  # k=12
    
    filtered = [
        doc for doc in candidates
        if metadata_matches(doc, subject=subject, module=module, title=title)
    ]
    
    if not filtered and any([subject, module, title]):
        warn("No docs matched metadata filters. Falling back to semantic search only.")
        filtered = candidates
    
    return filtered[:TOP_K]  # Top 4
```

`vector_store.similarity_search(query, k=12)` — Query ko vector mein convert karo,
Chroma mein top 12 similar chunks dhundho.

List comprehension with filter:
`[doc for doc in candidates if metadata_matches(...)]` — sirf woh chunks rakho jo
metadata conditions satisfy karte hain.

`any([subject, module, title])` — agar koi bhi filter diya gaya tha, lekin kuch nahi
mila → fallback warning aur unfiltered results use karo.

**Kyun FETCH_K > TOP_K?**
12 candidates fetch → filter → shayad 5-6 bachein → top 4 return.
Seedha 4 fetch karo → filter ke baad sirf 0-1 bachein → poor answer.

---

### `answer_question(query, vector_store, subject, module, title)`

```python
def answer_question(query, vector_store, subject=None, module=None, title=None):
    docs = retrieve_docs(query, vector_store, subject=subject, module=module, title=title)
    
    if not docs:
        return "I don't know based on the provided documents.", []
    
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)
```

`ChatOllama(model="llama3", temperature=0)`:
- `temperature=0` → deterministic, no randomness. Har baar same input pe same answer.
  Factual Q&A ke liye perfect.
- `temperature=1` → random, creative — creative writing ke liye
- **Analogy:** 0 = strict teacher jo sirf facts bolega, 1 = creative writer jo experiment
  karega

```python
    prompt = ChatPromptTemplate.from_template(
        """
You are a helpful course-module QA assistant.

Answer ONLY using the context below.
If the answer is not present in the context, say exactly:
"I don't know based on the provided documents."

Context:
{context}

Question:
{question}

Answer:
"""
    )
```

**Prompt engineering:**
- "Answer ONLY using the context below" → AI apni training se guess nahi karega, sirf
  diye gaye text se answer dega. Hallucination prevent karta hai.
- "say exactly: 'I don't know...'" → Predictable failure mode — AI kabhi bhi random
  kuch nahi bolega.

`{context}` aur `{question}` — placeholders jo `.invoke()` pe fill honge.

```python
    answer = (prompt | llm | StrOutputParser()).invoke(
        {"context": format_docs_for_prompt(docs), "question": query}
    )
    
    return answer, docs
```

**LangChain Chain — `|` operator:**
```
prompt | llm | StrOutputParser()
```

Yeh LangChain ka LCEL (LangChain Expression Language) hai. `|` ek chain banata hai:

```
.invoke({"context": ..., "question": ...})
    ↓
prompt.invoke() → ChatPromptValue (formatted messages)
    ↓
llm.invoke() → AIMessage (raw LLM output)
    ↓
StrOutputParser().invoke() → plain Python string
```

**Analogy:** Assembly line — ek kaam karo, result agle step ko do, woh kaam kare,
aage do. `|` pipe operator unix/linux se inspired hai jahan `cat file | grep "text"`.

---

### `run_chat()`

```python
def run_chat():
    vector_store = load_vector_store()   # Ek baar load karo — loop ke bahar
    
    while True:
        query = input("❓ Question: ").strip()
        
        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting.")
            break
        
        if not query:
            continue       # Empty input → agle iteration pe jao
        
        answer, docs = answer_question(query, vector_store)
        print("\n🧠 Answer:")
        print(answer)
        print_sources(docs)
        print("\n" + "-" * 72 + "\n")
```

`vector_store = load_vector_store()` — loop ke bahar hai. Agar loop ke andar hota toh
har question pe DB reload hota — bahut slow.

`while True:` — infinite loop. Sirf `break` se niklega.

`{"exit", "quit"}` — yeh set hai (list nahi). `in` operator set mein O(1) time mein
check karta hai vs list mein O(n). Good practice.

**Stateless hai:** Yeh chatbot nahi hai — conversation history nahi rakha. Har question
independent hai. Pehle wala question yaad nahi rahega.

---

## BLOCK 8 — CLI (Command Line Interface)

```python
def build_cli():
    parser = argparse.ArgumentParser(
        description="Course Metadata Parser + Multi-Document RAG"
    )
    
    sub = parser.add_subparsers(dest="command", required=True)
```

`ArgumentParser` — CLI banata hai.
`add_subparsers(dest="command")` — subcommands support karta hai (`parse`, `ingest`,
`ask`, `chat`). Jo subcommand select karo woh `args.command` mein store hoga.
`required=True` — koi command dena zaroori hai, warna error.

```python
    p_parse = sub.add_parser("parse", help="Extract course metadata JSON from PDFs locally")
    p_parse.add_argument("--force", action="store_true")
```

`action="store_true"` — yeh ek flag hai. Flag present hai → `True`. Absent → `False`.
Koi value nahi dete, bas flag lagaate hain:
```
python script.py parse            → args.force = False
python script.py parse --force    → args.force = True
```

```python
    p_ask = sub.add_parser("ask", help="Ask one question")
    p_ask.add_argument("question", type=str)           # Positional — required
    p_ask.add_argument("--subject", type=str, default=None)  # Optional
    p_ask.add_argument("--module", type=str, default=None)
    p_ask.add_argument("--title", type=str, default=None)
```

`"question"` — bina `--` ke matlab yeh positional argument hai — value directly likhte hain:
```
python script.py ask "What are CSS selectors?"
```
`args.question = "What are CSS selectors?"`

`"--subject"` — optional argument — `--` se start:
```
python script.py ask "..." --subject CSS3
```

---

## BLOCK 9 — main()

```python
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
```

`if __name__ == "__main__":` — Jab yeh file directly run ho tab `main()` call karo.
Agar koi dusri file yeh import kare toh `main()` automatically mat chalao.

**`__name__`:** Python har file mein automatically yeh variable set karta hai:
- Directly run karein → `__name__ = "__main__"`
- Import karein → `__name__ = "combined_document_intelligence"`

---

## PICHLE CODE SE COMPARISON

**Jo same pattern hai:**
- LangChain chain `|` operator — tune pehle bhi dekha hoga
- `RecursiveCharacterTextSplitter` — standard RAG pattern
- `.env` se configuration — same pattern as before

**Jo naya hai is version mein:**
- ✅ Groq LLM parser **completely hata diya** → local regex parser
- ✅ `subject_key_concepts()` — hardcoded per-subject knowledge (pehle nahi tha)
- ✅ `guess_subject_from_filename()` — filename se intelligence (pehle PDF content pe depend tha)
- ✅ `FETCH_K` + `metadata_matches()` combo — zyada sophisticated retrieval
- ✅ Dual-method topic extraction (line-wise + broad regex fallback)

**Compared to scientific papers version:**
```
Scientific Papers Version:          Course Module Version:
PDF → Groq LLM → JSON             PDF → Local Regex → JSON
fields: title, authors, year       fields: subject, topics, module_number
cost: quota use karta tha          cost: FREE, fully local
```

---

## SETUP — APNE SYSTEM PE KAISE RUN KARO

### Step 1 — Python 3.10+ check karo

```bash
python --version
# Python 3.10.x ya usse upar chahiye
```

### Step 2 — Virtual environment banao

```bash
cd your-project-folder
python -m venv venv

# Windows:
.\venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Dependencies install karo

⚠️ `PyPDF2` deprecated hai — `pypdf` use karo:

```bash
pip install pypdf                    # PyPDF2 ki jagah
pip install langchain==1.3.11
pip install langchain-ollama==1.1.0
pip install langchain-huggingface==1.2.0
pip install langchain-chroma==1.1.0
pip install langchain-community
pip install langchain-text-splitters
pip install chromadb==1.5.9
pip install python-dotenv
pip install sentence-transformers
```

Ya agar `requirements.txt` diya hai project mein:
```bash
pip install -r requirements.txt
```

### Step 4 — Code mein PyPDF2 fix karo

`combined_document_intelligence.py` file mein yeh line badlo:
```python
# Purana (deprecated):
from PyPDF2 import PdfReader

# Naya (sahi):
from pypdf import PdfReader
# Baaki sab same rahega
```

### Step 5 — Ollama install + model pull karo

Ollama download karo: https://ollama.com/download

```bash
ollama pull llama3          # model download karo (~4GB)
# Agar Ollama server manually start karna pade:
ollama serve
```

### Step 6 — .env file banao

Project folder mein `.env` file banao:
```
DATA_DIR=./data
CHROMA_DIR=./chroma_db
METADATA_DIR=./data/extracted_metadata
OLLAMA_MODEL=llama3
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
COLLECTION_NAME=combined_docs
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=4
FETCH_K=12
```

**Note:** Is course-module version mein `GROQ_API_KEY` ki zarurat NAHI hai.

### Step 7 — PDFs daalo aur run karo

```bash
# data/ folder mein PDFs daalo
mkdir data
# Module 1-CSS3.pdf, Module 1-Bootstrap5.pdf etc. daalo

# Metadata parse karo
python combined_document_intelligence.py parse

# Vector DB build karo
python combined_document_intelligence.py ingest --rebuild --parse

# Question puchho
python combined_document_intelligence.py ask "What are CSS selectors?"

# Subject filter ke saath
python combined_document_intelligence.py ask "Explain grid system" --subject Bootstrap5

# Chat mode
python combined_document_intelligence.py chat
```

---

## QUICK MENTAL MODEL

```
PDF Files (data/)
    │
    ├── [PARSE] → regex + filename analysis → JSON metadata (extracted_metadata/)
    │
    └── [INGEST]
         ├── PyPDFLoader → Document objects (text + metadata)
         ├── RecursiveCharacterTextSplitter → chunks
         ├── HuggingFaceEmbeddings → vectors
         └── Chroma → disk (chroma_db/)
                │
                ▼
         [ASK/CHAT]
         User query
              │
              ├── similarity_search (k=12)
              ├── metadata_matches filter
              ├── top 4 chunks
              ├── format as context
              ├── ChatOllama (llama3, temp=0)
              └── StrOutputParser → plain string answer
```

---

