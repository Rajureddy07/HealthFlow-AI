from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Strength(BaseModel):
    value: Optional[str] = None


class PrescriptionExtraction(BaseModel):
    medicine_name: Optional[str] = None
    active_ingredients: List[str] = Field(default_factory=list)
    strength: Optional[Strength] = None
    dosage_form: Optional[str] = None
    quantity: Optional[Union[str, int]] = None
    instructions: Optional[str] = None
    frequency: Optional[str] = None


class FieldEvidence(BaseModel):
    field: str
    value: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    confidence: float
    status: str


class ExtractionEvidence(BaseModel):
    fields: List[FieldEvidence]