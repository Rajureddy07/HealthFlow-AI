from pathlib import Path

from app.database.session import SessionLocal
from app.models.document import Document, ProcessingResult
from app.services.document_processing_service import (
    DocumentProcessingService,
)


UPLOAD_DIR = Path("uploads")


def process_document_background(document_id: int):
    """
    Background workflow for automatic document processing.

    Creates its own database session because the FastAPI
    request session must not be reused inside a background task.
    """

    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if not document:
            return

        file_path = (
            UPLOAD_DIR /
            document.file_name
        )

        if not file_path.exists():

            document.status = "PROCESSING_FAILED"
            document.review_status = "NOT_REQUIRED"

            db.commit()

            return

        # ----------------------------------------------
        # Mark as processing
        # ----------------------------------------------

        document.status = "PROCESSING"

        db.commit()

        # ----------------------------------------------
        # Run existing AI/OCR pipeline
        # ----------------------------------------------

        processing_service = (
            DocumentProcessingService()
        )

        result = processing_service.process(
            str(file_path)
        )

        # ----------------------------------------------
        # Update document status
        # ----------------------------------------------

        document.status = result["status"]

        if result["status"] == "NEEDS_REVIEW":
            document.review_status = "PENDING"
        else:
            document.review_status = "NOT_REQUIRED"

        # ----------------------------------------------
        # Save processing result
        # ----------------------------------------------

        processing_result = (
            db.query(ProcessingResult)
            .filter(
                ProcessingResult.document_id ==
                document.id
            )
            .first()
        )

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

        else:

            processing_result = ProcessingResult(
                document_id=document.id,
                status=result["status"],
                stage=result["stage"],
                quality=result["quality"],
                extraction=result["extraction"],
                evidence=result["evidence"],
                validation=result["validation"],
            )

            db.add(processing_result)

        db.commit()

    except Exception as exc:

        db.rollback()

        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if document:

            document.status = "PROCESSING_FAILED"
            document.review_status = "NOT_REQUIRED"

            db.commit()

        print(
            f"[WORKFLOW ERROR] "
            f"Document {document_id}: {exc}"
        )

    finally:

        db.close()