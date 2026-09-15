from app.schemas.extraction import (
    PrescriptionExtraction,
    Strength
)

from app.services.validation_service import (
    ValidationService
)


extraction = PrescriptionExtraction(
    medicine_name="Co-amoxiclav",
    active_ingredients=[
        "Amoxycillin Trihydrate IP",
        "Potassium Clavulanate Diluted IP"
    ],
    strength=None,
    dosage_form="tablet",
    quantity=10,
    instructions=None,
    frequency=None
)


ocr_text = """
Co-amoxiclav

Amoxycillin Trihydrate IP
500 mg

Potassium Clavulanate
125 mg

10 Tablets
"""


service = ValidationService()

result = service.validate(
    extraction,
    ocr_text
)

print("Validation completed!")
print(result.model_dump())