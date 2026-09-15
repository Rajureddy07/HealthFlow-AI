from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document, OCRResult
from app.services.ocr_service import OCRService
from app.services.ocr_quality_service import OCRQualityService


router = APIRouter(
    prefix="/api/ocr",
    tags=["OCR"]
)


ocr_service = OCRService()
quality_service = OCRQualityService()


@router.post("/{document_id}")
def extract_text(
    document_id: int,
    db: Session = Depends(get_db)
):
    # 1. Find document
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # 2. Locate uploaded file
    file_path = Path("uploads") / document.file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Uploaded file not found"
        )

    # 3. Run OCR
    results = ocr_service.extract_text(
        str(file_path)
    )

    # 4. Save OCR results
    for result in results:
        ocr_record = OCRResult(
            document_id=document.id,
            text=result["text"],
            confidence=str(result["confidence"])
        )

        db.add(ocr_record)

    db.commit()

    # 5. Check OCR quality
    quality_result = quality_service.check_quality(results)

    # 6. Update document status
    if quality_result["quality_status"] == "PASSED":
        document.status = "OCR_QUALITY_PASSED"
    else:
        document.status = "NEEDS_REVIEW"

    db.commit()

    # 7. Return processing result
    return {
        "document_id": document.id,
        "file_name": document.file_name,
        "status": document.status,
        "quality": quality_result,
        "text": results
    }