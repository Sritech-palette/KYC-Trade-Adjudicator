from pydantic import ValidationError
from schemas import DocumentExtraction, LineItem

# 1. Test a valid line item: 10 * 100 = 1000
good_item = LineItem(
    description="Steel Pipes",
    quantity=10,
    unit_price=100,
    line_total=1000,
)

good_doc = DocumentExtraction(
    document_type="commercial_invoice",
    vendor_name="Gulf Logistics LLC",
    subtotal=1000.0,
    total_amount=1000.0,
    line_items=[good_item],
)
print("GOOD DOC PASSED:", good_doc.vendor_name, good_doc.total_amount)

# 2. Test a bad line item: 10 * 100 is 1000, NOT 900
try:
    bad_item = LineItem(
        description="Steel Pipes",
        quantity=10,
        unit_price=100,
        line_total=900,
    )
    print("BAD ITEM PASSED (unexpected)")
except ValidationError as err:
    print("BAD ITEM CAUGHT BY PYDANTIC:")
    print(err)