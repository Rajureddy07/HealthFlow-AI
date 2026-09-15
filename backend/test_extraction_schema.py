from app.schemas.extraction import PrescriptionExtraction


# Valid example
data = {
    "medicine_name": "Co-amoxiclav",
    "active_ingredients": [
        "Amoxicillin",
        "Clavulanic acid"
    ],
    "strength": {
        "amoxicillin": "500 mg",
        "clavulanic_acid": "125 mg"
    },
    "dosage_form": "tablet",
    "quantity": "10 tablets",
    "instructions": None,
    "frequency": None
}


extraction = PrescriptionExtraction.model_validate(data)

print("Schema validation successful!")
print(extraction.model_dump())