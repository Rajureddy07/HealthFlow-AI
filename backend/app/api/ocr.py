from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document, OCRResult
from app.services.ocr_service import OCRService


router = APIRouter(
    prefix="/api/ocr",
    tags=["OCR"]
)


ocr_service = OCRService()


@router.post("/{document_id}")
def extract_text(
    document_id: int,
    db: Session = Depends(get_db)
):
    # 1. Find the document in the database
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # 2. Locate the uploaded file
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

    # 4. Save OCR results to database
    for result in results:

        ocr_record = OCRResult(
            document_id=document.id,
            text=result["text"],
            confidence=str(result["confidence"])
        )

        db.add(ocr_record)

    db.commit()

    # 5. Update document status
    document.status = "OCR_COMPLETED"

    db.commit()

    # 6. Return OCR results
    return {
        "document_id": document.id,
        "file_name": document.file_name,
        "status": document.status,
        "text": results
    }