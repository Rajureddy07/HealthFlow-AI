from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.services.ocr_service import OCRService


router = APIRouter(
    prefix="/api/ocr",
    tags=["OCR"]
)


ocr_service = OCRService()


@router.post("/{filename}")
def extract_text(filename: str):

    file_path = Path("uploads") / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    results = ocr_service.extract_text(
        str(file_path)
    )

    return {
        "file_name": filename,
        "text": results
    }