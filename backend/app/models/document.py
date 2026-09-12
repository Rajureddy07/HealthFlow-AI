from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    document_type = Column(String, nullable=False)

    status = Column(
        String,
        default="RECEIVED",
        nullable=False
    )

    file_name = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )