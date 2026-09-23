from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.extraction import PrescriptionExtraction


class ReviewActionRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=100
    )

    comment: Optional[str] = Field(
        default=None,
        max_length=1000
    )


class ExtractionCorrectionRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=100
    )

    comment: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    extraction: PrescriptionExtraction