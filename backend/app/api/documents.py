from pathlib import Path
import shutil
from fastapi import HTTPException
from app.services.document_processing_service import DocumentProcessingService

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document
from app.services.document_processing_service import (
    DocumentProcessingService,
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# Upload Document
# --------------------------------------------------

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    document = Document(
        document_type="UNKNOWN",
        status="RECEIVED",
        file_name=file.filename
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "file_name": document.file_name,
        "document_type": document.document_type,
        "status": document.status
    }


# --------------------------------------------------
# Process Document
# --------------------------------------------------

@router.post("/{document_id}/process")
def process_document(
    document_id: int,
    db: Session = Depends(get_db)
):

    # ----------------------------------------------
    # Find document
    # ----------------------------------------------

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # ----------------------------------------------
    # Find uploaded file
    # ----------------------------------------------

    file_path = (
        UPLOAD_DIR /
        document.file_name
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Uploaded file not found"
        )

    # ----------------------------------------------
    # Update processing status
    # ----------------------------------------------

    document.status = "PROCESSING"

    db.commit()

    # ----------------------------------------------
    # Run complete processing pipeline
    # ----------------------------------------------

    try:

        processing_service = (
            DocumentProcessingService()
        )

        result = processing_service.process(
            str(file_path)
        )

    except Exception as exc:

        document.status = "PROCESSING_FAILED"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}"
        )

    # ----------------------------------------------
    # Update final document status
    # ----------------------------------------------

    document.status = result["status"]

    db.commit()

    # ----------------------------------------------
    # Return result
    # ----------------------------------------------

    return {
        "document_id": document.id,
        "file_name": document.file_name,
        "status": result["status"],
        "stage": result["stage"],
        "quality": result["quality"],
        "extraction": result["extraction"],
        "evidence": result["evidence"],
        "validation": result["validation"]
    }



@router.get("/{document_id}/review")
def get_document_review(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    file_path = UPLOAD_DIR / document.file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file not found"
        )

    try:
        service = DocumentProcessingService()

        result = service.process(
            str(file_path)
        )

        return {
            "document_id": document.id,
            "file_name": document.file_name,
            "status": result["status"],
            "stage": result["stage"],
            "quality": result["quality"],
            "extraction": result["extraction"],
            "evidence": result["evidence"],
            "validation": result["validation"]
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}"
        )