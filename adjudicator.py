from datetime import date
from schemas import DocumentExtraction


def adjudicate_document(
    doc: DocumentExtraction,
    as_of_date: date | None = None,
    high_value_threshold: float = 50_000.0,
    min_confidence: float = 0.85,
) -> dict[str, str]:
    """
    Decide whether a validated document can be AUTO_APPROVED,
    needs HUMAN_REVIEW (HITL), or should be REJECTED.
    """
    today = as_of_date or date.today()
    reasons: list[str] = []

    # 1. Check if an expiry date (like a trade license expiry) has passed
    if doc.expiry_date is not None and doc.expiry_date < today:
        return {
            "decision": "REJECTED",
            "reason": f"Document expired on {doc.expiry_date} (checked against {today}).",
        }

    # 2. Check extraction confidence
    if doc.confidence_score < min_confidence:
        reasons.append(
            f"Low extraction confidence ({doc.confidence_score:.2f} < {min_confidence:.2f})."
        )

    # 3. Check high-value trade finance threshold
    if doc.total_amount >= high_value_threshold:
        reasons.append(
            f"High-value amount ({doc.currency} {doc.total_amount:,.2f} >= {high_value_threshold:,.2f})."
        )

    if reasons:
        return {
            "decision": "HUMAN_REVIEW",
            "reason": " | ".join(reasons),
        }

    return {
        "decision": "AUTO_APPROVED",
        "reason": "Passed math checks, within value limit, and confidence is high.",
    }


if __name__ == "__main__":
    # Case 1: Normal lower-value invoice -> AUTO_APPROVED
    low_doc = DocumentExtraction(
        document_type="commercial_invoice",
        vendor_name="Gulf Logistics LLC",
        subtotal=1000.0,
        total_amount=1000.0,
        confidence_score=0.95,
    )
    print("Case 1:", adjudicate_document(low_doc))

    # Case 2: High-value invoice -> HUMAN_REVIEW
    high_doc = DocumentExtraction(
        document_type="commercial_invoice",
        vendor_name="Emirates Heavy Steel PJSC",
        subtotal=120000.0,
        total_amount=120000.0,
        confidence_score=0.92,
    )
    print("Case 2:", adjudicate_document(high_doc))

    # Case 3: Expired document -> REJECTED
    expired_doc = DocumentExtraction(
        document_type="trade_license",
        vendor_name="Desert Traders DMCC",
        subtotal=5000.0,
        total_amount=5000.0,
        expiry_date=date(2024, 1, 15),
        confidence_score=0.98,
    )
    print("Case 3:", adjudicate_document(expired_doc, as_of_date=date(2026, 11, 19)))