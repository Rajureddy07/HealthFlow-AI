from pathlib import Path
import shutil

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    BackgroundTasks,
)
import os

from fastapi import HTTPException, Depends

from sqlalchemy.orm import Session

from app.database.session import get_db


from app.schemas.review import (
    ReviewActionRequest,
    ExtractionCorrectionRequest,
)

from app.services.document_processing_service import (
    DocumentProcessingService,
)


from app.services.workflow_service import (
    process_document_background,
)
from app.models.document import (
    Document,
    OCRResult,
    ProcessingResult,
    ReviewAction,
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # ----------------------------------------------
    # Save uploaded file
    # ----------------------------------------------

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # ----------------------------------------------
    # Create document
    # ----------------------------------------------

    document = Document(
        document_type="UNKNOWN",
        status="QUEUED",
        review_status="NOT_REQUIRED",
        file_name=file.filename
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    # ----------------------------------------------
    # Start background workflow
    # ----------------------------------------------

    background_tasks.add_task(
        process_document_background,
        document.id
    )

    # ----------------------------------------------
    # Return immediately
    # ----------------------------------------------

    return {
        "message": "Document uploaded and queued for processing",
        "document_id": document.id,
        "file_name": document.file_name,
        "document_type": document.document_type,
        "status": document.status,
        "review_status": document.review_status,
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
# Review Queue
# ==================================================

@router.get("/review-queue")
def get_review_queue(
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document)
        .filter(Document.review_status == "PENDING")
        .order_by(Document.created_at.asc())
        .all()
    )

    return {
        "count": len(documents),
        "documents": [
            {
                "document_id": document.id,
                "file_name": document.file_name,
                "document_type": document.document_type,
                "status": document.status,
                "review_status": document.review_status,
                "created_at": document.created_at,
            }
            for document in documents
        ]
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
    # Prepare corrected extraction
    # ----------------------------------------------

    corrected_extraction = request.extraction.model_dump()

    # ----------------------------------------------
    # Prevent duplicate correction events
    # ----------------------------------------------

    if processing_result.extraction == corrected_extraction:
        return {
            "message": "No extraction changes detected",
            "document_id": document.id,
            "review_status": document.review_status,
            "extraction": processing_result.extraction,
            "action": "NO_CHANGE",
            "reviewer": request.reviewer,
            "comment": request.comment,
            "review_action_id": None
        }

    # ----------------------------------------------
    # Save corrected extraction
    # ----------------------------------------------

    processing_result.extraction = corrected_extraction


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


# ==================================================
# Audit Logs
# ==================================================

@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db)
):
    actions = (
        db.query(ReviewAction)
        .order_by(ReviewAction.created_at.desc())
        .all()
    )

    return {
        "count": len(actions),
        "logs": [
            {
                "id": action.id,
                "document_id": action.document_id,
                "action": action.action,
                "reviewer": action.reviewer,
                "comment": action.comment,
                "created_at": action.created_at,
            }
            for action in actions
        ]
    }

# ==================================================
# All Documents
# ==================================================

@router.get("/")
def get_documents(
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )

    return {
        "count": len(documents),
        "documents": [
            {
                "document_id": document.id,
                "file_name": document.file_name,
                "document_type": document.document_type,
                "status": document.status,
                "review_status": document.review_status,
                "created_at": document.created_at,
            }
            for document in documents
        ]
    }

# ==================================================
# Retry Failed Document
# ==================================================

@router.post("/{document_id}/retry")
def retry_document(
    document_id: int,
    background_tasks: BackgroundTasks,
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

    # --------------------------------------------------
    # Only failed documents can be retried
    # --------------------------------------------------

    if document.status != "PROCESSING_FAILED":
        raise HTTPException(
            status_code=400,
            detail=(
                "Only documents with "
                "PROCESSING_FAILED status can be retried."
            )
        )

    # --------------------------------------------------
    # Verify source file still exists
    # --------------------------------------------------

    file_path = UPLOAD_DIR / document.file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Source document file no longer exists."
        )

    # --------------------------------------------------
    # Reset workflow state
    # --------------------------------------------------

    document.status = "QUEUED"
    document.review_status = "NOT_REQUIRED"

    # --------------------------------------------------
    # Record retry event
    # --------------------------------------------------

    review_action = ReviewAction(
        document_id=document.id,
        action="RETRIED",
        reviewer="admin",
        comment="Document processing manually retried."
    )

    db.add(review_action)

    db.commit()

    # --------------------------------------------------
    # Start background processing again
    # --------------------------------------------------

    background_tasks.add_task(
        process_document_background,
        document.id
    )

    return {
        "message": "Document queued for retry",
        "document_id": document.id,
        "status": document.status,
        "review_status": document.review_status,
    }

# ==================================================
# DEVELOPMENT ONLY - Simulate Processing Failure
# ==================================================

@router.post("/{document_id}/simulate-failure")
def simulate_processing_failure(
    document_id: int,
    db: Session = Depends(get_db)
):
    # Never allow this endpoint in production.
    environment = os.getenv(
        "ENVIRONMENT",
        "development"
    ).lower()

    if environment == "production":
        raise HTTPException(
            status_code=403,
            detail="Development failure simulation is disabled in production."
        )

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    # Set the workflow into failed state.
    document.status = "PROCESSING_FAILED"

    # A failed processing document is not automatically
    # a human-review item.
    document.review_status = "NOT_REQUIRED"

    # Record the failure in the audit trail.
    review_action = ReviewAction(
        document_id=document.id,
        action="PROCESSING_FAILED",
        reviewer="system",
        comment="Development test: simulated processing failure."
    )

    db.add(review_action)
    db.commit()
    db.refresh(document)
    db.refresh(review_action)

    return {
        "message": "Development processing failure simulated.",
        "document_id": document.id,
        "status": document.status,
        "review_status": document.review_status,
        "audit_action_id": review_action.id
    }