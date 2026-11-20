from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator


class LineItem(BaseModel):
    """One row on an invoice (for example, 10 boxes at 100 each)."""

    description: str
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    line_total: float = Field(..., ge=0)
    math_mismatch: bool = False
    math_note: str | None = None

    @model_validator(mode="after")
    def check_line_math(self) -> "LineItem":
        expected = round(self.quantity * self.unit_price, 2)
        if abs(expected - self.line_total) > 0.05:
            self.math_mismatch = True
            self.math_note = (
                f"Math mismatch on '{self.description}': "
                f"{self.quantity} x {self.unit_price} should be {expected}, got {self.line_total}."
            )
        else:
            self.math_mismatch = False
            self.math_note = None
        return self


class DocumentExtraction(BaseModel):
    """The main information pulled out of a trade or KYC document."""

    document_type: str
    vendor_name: str
    buyer_name: str = "Unknown"
    currency: str = "AED"
    subtotal: float = Field(..., ge=0)
    total_amount: float = Field(..., ge=0)
    issue_date: date | None = None
    expiry_date: date | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)

    @field_validator("buyer_name", mode="before")
    @classmethod
    def normalize_buyer_name(cls, value: object) -> str:
        if value is None:
            return "Unknown"
        cleaned = str(value).strip()
        if not cleaned or cleaned.lower() in {"null", "none", "n/a", "na", "unknown"}:
            return "Unknown"
        return cleaned