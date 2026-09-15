from typing import List

from pydantic import BaseModel


class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: str


class ValidationResult(BaseModel):
    status: str
    confidence: float
    issues: List[ValidationIssue]