from pathlib import Path
import shutil

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.models.document import (
    Document,
    ProcessingResult,
    ReviewAction,
)

from app.schemas.review import (
    ReviewActionRequest,
    ExtractionCorrectionRequest,
)

from app.services.document_processing_service import (
    DocumentProcessingService,
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ==================================================
# Upload Document
# ==================================================

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
        review_status="NOT_REQUIRED",
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
        "status": document.status,
        "review_status": document.review_status
    }


# ==================================================
# Process Document
# ==================================================

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
    # Mark document as processing
    # ----------------------------------------------

    document.status = "PROCESSING"

    db.commit()

    # ----------------------------------------------
    # Run processing pipeline
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
        document.review_status = "NOT_REQUIRED"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}"
        )

    # ----------------------------------------------
    # Update document status
    # ----------------------------------------------

    document.status = result["status"]

    if result["status"] == "NEEDS_REVIEW":
        document.review_status = "PENDING"
    else:
        document.review_status = "NOT_REQUIRED"

    db.commit()

    # ----------------------------------------------
    # Check existing processing result
    # ----------------------------------------------

    processing_result = (
        db.query(ProcessingResult)
        .filter(
            ProcessingResult.document_id == document.id
        )
        .first()
    )

    # ----------------------------------------------
    # Update existing result
    # ----------------------------------------------

    if processing_result:

        processing_result.status = (
            result["status"]
        )

        processing_result.stage = (
            result["stage"]
        )

        processing_result.quality = (
            result["quality"]
        )

        processing_result.extraction = (
            result["extraction"]
        )

        processing_result.evidence = (
            result["evidence"]
        )

        processing_result.validation = (
            result["validation"]
        )

    # ----------------------------------------------
    # Create new processing result
    # ----------------------------------------------

    else:

        processing_result = ProcessingResult(
            document_id=document.id,
            status=result["status"],
            stage=result["stage"],
            quality=result["quality"],
            extraction=result["extraction"],
            evidence=result["evidence"],
            validation=result["validation"]
        )

        db.add(processing_result)

    # ----------------------------------------------
    # Save everything
    # ----------------------------------------------

    db.commit()

    db.refresh(processing_result)

    # ----------------------------------------------
    # Return result
    # ----------------------------------------------

    return {
        "message": "Document processed successfully",
        "document_id": document.id,
        "file_name": document.file_name,
        "status": result["status"],
        "review_status": document.review_status,
        "stage": result["stage"],
        "quality": result["quality"],
        "extraction": result["extraction"],
        "evidence": result["evidence"],
        "validation": result["validation"]
    }


# ==================================================
# Get Document Review
# ==================================================

@router.get("/{document_id}/review")
def get_document_review(
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
    # Get saved processing result
    # ----------------------------------------------

    processing_result = (
        db.query(ProcessingResult)
        .filter(
            ProcessingResult.document_id == document_id
        )
        .first()
    )

    # ----------------------------------------------
    # Processing has not happened yet
    # ----------------------------------------------

    if not processing_result:

        raise HTTPException(
            status_code=404,
            detail="Document has not been processed yet"
        )

    # ----------------------------------------------
    # Return saved result
    # ----------------------------------------------

    return {
        "document_id": document.id,
        "file_name": document.file_name,
        "status": processing_result.status,
        "review_status": document.review_status,
        "stage": processing_result.stage,
        "quality": processing_result.quality,
        "extraction": processing_result.extraction,
        "evidence": processing_result.evidence,
        "validation": processing_result.validation
    }



# ==================================================
# Save Extraction Correction
# ==================================================

@router.put("/{document_id}/extraction")
def update_extraction(
    document_id: int,
    request: ExtractionCorrectionRequest,
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
    # Only pending documents can be corrected
    # ----------------------------------------------

    if document.review_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=(
                "Document is not waiting for human review. "
                f"Current review status: {document.review_status}"
            )
        )

    # ----------------------------------------------
    # Find processing result
    # ----------------------------------------------

    processing_result = (
        db.query(ProcessingResult)
        .filter(
            ProcessingResult.document_id == document_id
        )
        .first()
    )

    if not processing_result:
        raise HTTPException(
            status_code=404,
            detail="Processing result not found"
        )

    # ----------------------------------------------
    # Save corrected extraction
    # ----------------------------------------------

    corrected_extraction = (
        request.extraction.model_dump()
    )

    processing_result.extraction = (
        corrected_extraction
    )

    # ----------------------------------------------
    # Create audit record
    # ----------------------------------------------

    review_action = ReviewAction(
        document_id=document.id,
        action="CORRECTED",
        reviewer=request.reviewer,
        comment=request.comment
    )

    db.add(review_action)

    # ----------------------------------------------
    # Save
    # ----------------------------------------------

    db.commit()

    db.refresh(processing_result)
    db.refresh(review_action)

    # ----------------------------------------------
    # Return
    # ----------------------------------------------

    return {
        "message": "Extraction corrected successfully",
        "document_id": document.id,
        "review_status": document.review_status,
        "extraction": processing_result.extraction,
        "action": review_action.action,
        "reviewer": review_action.reviewer,
        "comment": review_action.comment,
        "review_action_id": review_action.id
    }
# ==================================================
# Approve Document
# ==================================================

@router.post("/{document_id}/approve")
def approve_document(
    document_id: int,
    request: ReviewActionRequest,
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
    # Check review status
    # ----------------------------------------------

    if document.review_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=(
                "Document is not waiting for human review. "
                f"Current review status: {document.review_status}"
            )
        )

    # ----------------------------------------------
    # Create audit record
    # ----------------------------------------------

    review_action = ReviewAction(
        document_id=document.id,
        action="APPROVED",
        reviewer=request.reviewer,
        comment=request.comment
    )

    db.add(review_action)

    # ----------------------------------------------
    # Update review status
    # ----------------------------------------------

    document.review_status = "APPROVED"

    db.commit()

    db.refresh(review_action)

    # ----------------------------------------------
    # Return result
    # ----------------------------------------------

    return {
        "message": "Document approved successfully",
        "document_id": document.id,
        "status": document.status,
        "review_status": document.review_status,
        "action": review_action.action,
        "reviewer": review_action.reviewer,
        "comment": review_action.comment,
        "review_action_id": review_action.id
    }

# ==================================================
# Send Document Back
# ==================================================

@router.post("/{document_id}/send-back")
def send_back_document(
    document_id: int,
    request: ReviewActionRequest,
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
    # Check review status
    # ----------------------------------------------

    if document.review_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=(
                "Document is not waiting for human review. "
                f"Current review status: {document.review_status}"
            )
        )

    # ----------------------------------------------
    # Require comment for send-back
    # ----------------------------------------------

    if not request.comment or not request.comment.strip():

        raise HTTPException(
            status_code=400,
            detail="A comment is required when sending a document back"
        )

    # ----------------------------------------------
    # Create audit record
    # ----------------------------------------------

    review_action = ReviewAction(
        document_id=document.id,
        action="SENT_BACK",
        reviewer=request.reviewer,
        comment=request.comment
    )

    db.add(review_action)

    # ----------------------------------------------
    # Update review status
    # ----------------------------------------------

    document.review_status = "SENT_BACK"

    db.commit()

    db.refresh(review_action)

    # ----------------------------------------------
    # Return result
    # ----------------------------------------------

    return {
        "message": "Document sent back successfully",
        "document_id": document.id,
        "status": document.status,
        "review_status": document.review_status,
        "action": review_action.action,
        "reviewer": review_action.reviewer,
        "comment": review_action.comment,
        "review_action_id": review_action.id
    }