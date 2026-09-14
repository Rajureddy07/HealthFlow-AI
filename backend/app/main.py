from fastapi import FastAPI

from app.database.session import Base, engine
from app.models.document import Document
from app.api.documents import router as documents_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HealthFlow AI",
    description="Healthcare Document & Workflow Automation",
    version="1.0.0"
)

app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "HealthFlow AI API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }