from app.services.extraction_service import ExtractionService


ocr_text = """
Co-amoxiclav

Amoxycillin Trihydrate IP
equivalent to Amoxycillin 500 mg

Potassium Clavulanate Diluted IP
equivalent to Clavulanic Acid 125 mg

10 Tablets

Each film-coated tablet contains.
"""


service = ExtractionService()

result = service.extract(ocr_text)

print("AI extraction successful!")
print(result.model_dump())