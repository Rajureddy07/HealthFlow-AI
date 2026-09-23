from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)

from app.database.session import Base


# ==================================================
# Document
# ==================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_type = Column(
        String,
        nullable=False
    )

    # AI processing status
    status = Column(
        String,
        default="RECEIVED",
        nullable=False
    )

    # Human review status
    review_status = Column(
        String,
        default="NOT_REQUIRED",
        nullable=False
    )

    file_name = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==================================================
# OCR Result
# ==================================================

class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    text = Column(
        Text,
        nullable=False
    )

    confidence = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==================================================
# Processing Result
# ==================================================

class ProcessingResult(Base):
    __tablename__ = "processing_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False,
        unique=True
    )

    status = Column(
        String,
        nullable=False
    )

    stage = Column(
        String,
        nullable=False
    )

    quality = Column(
        JSON,
        nullable=True
    )

    extraction = Column(
        JSON,
        nullable=True
    )

    evidence = Column(
        JSON,
        nullable=True
    )

    validation = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# ==================================================
# Review Action / Audit Trail
# ==================================================

class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    # APPROVED or SENT_BACK
    action = Column(
        String,
        nullable=False
    )

    # Reviewer identity
    reviewer = Column(
        String,
        nullable=False
    )

    # Optional reviewer comment
    comment = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )