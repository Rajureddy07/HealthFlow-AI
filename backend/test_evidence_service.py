from app.services.ocr_service import OCRService
from app.services.extraction_service import ExtractionService
from app.services.evidence_service import EvidenceService


file_path = "uploads/Screenshot 2026-08-15 200829.png"


# -----------------------------
# OCR
# -----------------------------

ocr_service = OCRService()

ocr_results = ocr_service.extract_text(
    file_path
)


# -----------------------------
# Convert OCR results to text
# -----------------------------

ocr_text = " ".join(
    result["text"]
    for result in ocr_results
)


# -----------------------------
# AI Extraction
# -----------------------------

extraction_service = ExtractionService()

extraction = extraction_service.extract(
    ocr_text
)


print("\nAI EXTRACTION")
print("----------------------")
print(extraction.model_dump())


# -----------------------------
# Evidence evaluation
# -----------------------------

evidence_service = EvidenceService()

evidence = evidence_service.evaluate(
    extraction,
    ocr_results
)


print("\nFIELD EVIDENCE")
print("----------------------")

for field in evidence.fields:

    print(f"\nField: {field.field}")
    print(f"Value: {field.value}")
    print(f"Status: {field.status}")
    print(f"Confidence: {field.confidence}")

    print("Evidence:")

    for item in field.evidence:
        print(f"  - {item}")