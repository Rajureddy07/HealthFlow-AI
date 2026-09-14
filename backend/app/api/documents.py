from pathlib import Path
import shutil

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.document import Document


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Save uploaded file
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Create database record
    document = Document(
        document_type="UNKNOWN",
        status="RECEIVED",
        file_name=file.filename
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # 3. Return document information
    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "file_name": document.file_name,
        "document_type": document.document_type,
        "status": document.status
    }