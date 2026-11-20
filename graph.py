from datetime import date
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from adjudicator import adjudicate_document
from extractor import extract_document
from schemas import DocumentExtraction


class AdjudicationState(TypedDict):
    raw_text: str
    doc: DocumentExtraction
    decision: str
    reason: str
    final_status: str
    summary: str


def extract_node(state: AdjudicationState) -> dict:
    """Turn raw document text into a Pydantic-validated DocumentExtraction."""
    doc = extract_document(state["raw_text"])
    return {"doc": doc}


def evaluate_node(state: AdjudicationState) -> dict:
    """Run the policy rules from adjudicator.py."""
    result = adjudicate_document(state["doc"], as_of_date=date(2026, 11, 19))
    return {
        "decision": result["decision"],
        "reason": result["reason"],
    }


def human_review_node(state: AdjudicationState) -> dict:
    """Pause the graph and wait for a human compliance officer's decision."""
    human_reply = interrupt(
        {
            "message": "Human review required before proceeding.",
            "vendor": state["doc"].vendor_name,
            "amount": f"{state['doc'].currency} {state['doc'].total_amount:,.2f}",
            "reason": state["reason"],
            "expected_input": "Type 'approve' or 'reject'",
        }
    )
    normalized = str(human_reply).strip().lower()
    if normalized == "approve":
        return {"final_status": "APPROVED_BY_HUMAN"}
    return {"final_status": "REJECTED_BY_HUMAN"}


def finalize_node(state: AdjudicationState) -> dict:
    """Set final_status for non-HITL paths and build a clean summary."""
    final_status = state.get("final_status") or state["decision"]
    doc = state["doc"]
    summary = (
        f"[{final_status}] {doc.vendor_name} ({doc.document_type}) | "
        f"Amount: {doc.currency} {doc.total_amount:,.2f} | "
        f"Rule: {state['decision']} — {state['reason']}"
    )
    return {
        "final_status": final_status,
        "summary": summary,
    }


def route_after_evaluate(state: AdjudicationState) -> str:
    """Route to human_review only when needed; otherwise go straight to finalize."""
    if state["decision"] == "HUMAN_REVIEW":
        return "human_review"
    return "finalize"


def build_graph():
    builder = StateGraph(AdjudicationState)

    builder.add_node("extract", extract_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "extract")
    builder.add_edge("extract", "evaluate")
    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "human_review": "human_review",
            "finalize": "finalize",
        },
    )
    builder.add_edge("human_review", "finalize")
    builder.add_edge("finalize", END)

    checkpointer = InMemorySaver(
        serde=JsonPlusSerializer(
            allowed_msgpack_modules=[
                ("schemas", "DocumentExtraction"),
                ("schemas", "LineItem"),
            ]
        )
    )
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    app = build_graph()

    sample_invoice_text = """
    COMMERCIAL INVOICE
    Vendor: Gulf Logistics LLC
    Document Type: commercial_invoice
    Currency: AED
    Line Item: Freight Handling — Qty 5 @ 400.00 = 2000.00
    Subtotal: 2000.00
    Total Amount: 2000.00
    Extraction Confidence: 0.95
    """

    config = {"configurable": {"thread_id": "case-301-llm"}}
    for chunk in app.stream({"raw_text": sample_invoice_text}, config=config, stream_mode="updates"):
        print(chunk)

    final_state = app.get_state(config).values
    print("FINAL SUMMARY:", final_state.get("summary"))

    risky_invoice_text = """
    COMMERCIAL INVOICE
    Invoice No: INV-2026-8841
    Supplier: Horizon Global Trading DMCC
    Buyer: Crescent Imports LLC
    Currency: AED
    Line Items:
    - Industrial Valves x 12 @ AED 15,000.00 = AED 185,000.00
    Subtotal: AED 185,000.00
    Total Amount: AED 185,000.00
    """

    risky_config = {"configurable": {"thread_id": "test-human-review-001"}}

    print("\n--- PAUSING AT HUMAN REVIEW ---")
    for chunk in app.stream(
        {"raw_text": risky_invoice_text},
        config=risky_config,
        stream_mode="updates",
    ):
        print(chunk)

    print("\n--- RESUMING WITH 'approve' ---")
    for chunk in app.stream(
        Command(resume="approve"),
        config=risky_config,
        stream_mode="updates",
    ):
        print(chunk)

    reject_config = {"configurable": {"thread_id": "test-human-review-002"}}

    print("\n--- PAUSING AT HUMAN REVIEW (REJECT TEST) ---")
    for chunk in app.stream(
        {"raw_text": risky_invoice_text},
        config=reject_config,
        stream_mode="updates",
    ):
        print(chunk)

    print("\n--- RESUMING WITH 'reject' ---")
    for chunk in app.stream(
        Command(resume="reject"),
        config=reject_config,
        stream_mode="updates",
    ):
        print(chunk)
        