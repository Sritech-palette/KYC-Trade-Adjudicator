# KYC-Trade-Adjudicator

An agentic KYC and trade finance invoice adjudication workflow built with LangGraph and Gemini (`gemini-3.5-flash-lite`), including structured schema extraction, line-item math validation, and Human-in-the-Loop (HITL) approval/rejection with `JsonPlusSerializer` checkpointing.

## Project Structure

- `schemas.py` — Data schemas and validation rules (including missing/null `buyer_name` normalization to `'Unknown'` and math mismatch detection).
- `extractor.py` (`extracter.py`) — Extracts structured trade/invoice fields using `gemini-3.5-flash-lite` with timeout and retry handling.
- `adjudicator.py` — Adjudication logic and risk/math evaluation.
- `graph.py` — LangGraph workflow routing clean invoices to `AUTO_APPROVED` and pausing risky/high-value/flagged items at `human_review` for `'approve'` or `'reject'` resume.
- `test_schemas.py` — Unit tests for schema validation.

## Setup

1. Create and activate a virtual environment (optional, recommended):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
2. Install dependencies (LangGraph, LangChain Google GenAI / Google SDK, Pydantic, pytest): pip install -U langgraph langchain-google-genai pydantic pytest
3. Set your Gemini API key in PowerShell: $env:GOOGLE_API_KEY="your-api-key-here"

   Running Tests & Workflow:

Run schema tests: pytest test_schemas.py

Run the adjudication workflow: python graph.py




