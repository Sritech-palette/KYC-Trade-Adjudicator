# KYC & Trade Finance Adjudicator

An agentic KYC and trade finance invoice adjudication pipeline built with **LangGraph** and **Gemini (`gemini-3.5-flash-lite`)**. It automates structured data extraction from trade documents, enforces deterministic schema and line-item arithmetic checks, auto-approves low-risk invoices, and pauses flagged or high-value cases at a durable **Human-in-the-Loop (`human_review`)** checkpoint for compliance officer sign-off.

---

## Architecture & Workflow

The workflow is implemented as a stateful **LangGraph** state machine backed by `JsonPlusSerializer` checkpointing so interrupted reviews can be safely resumed across sessions:

1. **Structured Extraction (`extractor.py`):** Parses unstructured invoice/trade text into typed records via `gemini-3.5-flash-lite` with built-in timeout and retry handling.
2. **Deterministic Validation (`schemas.py`):** Enforces Pydantic schema constraints, normalizes missing or `null` `buyer_name` fields to `"Unknown"`, and cross-checks line-item quantities/unit prices against invoice totals to catch math mismatches.
3. **Adjudication & Risk Evaluation (`adjudicator.py`):** Evaluates extracted records against compliance rules, value thresholds, and validation flags.
4. **Conditional Routing (`graph.py`):**
   - **Clean & within threshold** $\rightarrow$ Routes directly to `AUTO_APPROVED`.
   - **High-value, incomplete, or math-mismatched** $\rightarrow$ Triggers a `human_review` interrupt and awaits an explicit `"approve"` or `"reject"` decision before finalizing state.

---

## Key Engineering Highlights

- **Hybrid AI + Deterministic Guardrails:** Uses an LLM for unstructured document parsing while keeping arithmetic verification and threshold enforcement strictly deterministic in Python/Pydantic.
- **Durable Human-in-the-Loop (HITL):** Uses LangGraph interrupts with `JsonPlusSerializer` checkpointing so compliance reviewers can inspect flagged cases and resume execution without losing state.
- **Resilient Inference:** Handles transient API latency and failures with configured timeouts and retries in the extraction layer.

---

## Repository Structure

| File | Responsibility |
| :--- | :--- |
| `graph.py` | LangGraph state graph, conditional routing edges, `human_review` interrupt/resume loop, and `JsonPlusSerializer` checkpointer |
| `schemas.py` | Pydantic models, `"Unknown"` fallback normalization for missing `buyer_name`, and line-item math validation |
| `extractor.py` | Gemini (`gemini-3.5-flash-lite`) structured extraction pipeline with timeout and retry logic |
| `adjudicator.py` | Business rule evaluation, risk flagging, and adjudication decision logic |
| `test_schemas.py` | Unit tests covering schema validation, null handling, and arithmetic mismatch detection |
| `.gitignore` | Excludes `.venv/`, `.env`, and Python bytecode caches (`__pycache__/`) |

---

## Quickstart

### 1. Prerequisites
- Python **3.11+** (tested on Python 3.14 and 3.16)
- A Google Gemini API key

### 2. Installation
```powershell
git clone [https://github.com/Sritech-palette/KYC-Trade-Adjudicator.git](https://github.com/Sritech-palette/KYC-Trade-Adjudicator.git)
cd KYC-Trade-Adjudicator

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -U langgraph langchain-google-genai pydantic pytest

### 3. Configure Environment Variable
Set your API key in your PowerShell session: $env:GOOGLE_API_KEY="your-gemini-api-key"

### 4. Usage & Verification
Run Unit Tests: Verify schema validation and math-mismatch rules before running the graph

### 5. Run the Adjudication Workflow
Execute sample trade finance scenarios demonstrating both automated approval and Human-in-the-Loop review: python graph.py


---

## Challenges & Solutions

- **Missing Python Dependencies:** Installing `langgraph`, `langchain-google-genai`, `pydantic`, and `pytest` inside a dedicated virtual environment resolved missing-module errors and made runs repeatable across setups.
- **Gemini Model Availability (`2.5` vs. `3.5`):** When one Gemini tier was busy or unavailable during testing, switching across `gemini-2.5` / `gemini-3.5-flash-lite` alongside timeout and retry handling kept extraction moving reliably.
- **Edge Cases & HITL Serialization:** Handling missing or `null` `buyer_name` values (normalized to `"Unknown"`), checking line-item arithmetic, and using `JsonPlusSerializer` ensured `human_review` interrupts and resumes stayed intact.
