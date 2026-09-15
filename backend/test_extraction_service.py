from app.services.extraction_service import ExtractionService


ocr_text = """
Co-amoxiclav
Amoxycillin Trihydrate IP
500 mg
Potassium Clavulanate
125 mg
10 Tablets
"""


service = ExtractionService()

result = service.extract(ocr_text)

print("Extraction service working!")
print(result.model_dump())