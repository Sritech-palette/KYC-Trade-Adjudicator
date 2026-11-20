import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas import DocumentExtraction


def extract_document(raw_text: str) -> DocumentExtraction:
    """Extract raw document text into a validated DocumentExtraction model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Set it in PowerShell with: $env:GOOGLE_API_KEY='...'"
        )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(DocumentExtraction)

    return structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a KYC and Trade Finance document extraction specialist. "
                    "Extract fields accurately from the document text. "
                    "Ensure line_items, subtotal, and total_amount are consistent."
                )
            ),
            HumanMessage(content=raw_text),
        ]
    )