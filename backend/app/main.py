from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import Base, engine
from app.models.document import (
    Document,
    OCRResult,
    ProcessingResult,
    ReviewAction
)
from app.api.documents import router as documents_router
from app.api.ocr import router as ocr_router
from fastapi.staticfiles import StaticFiles

# Create database tables
Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="HealthFlow AI",
    description="Healthcare Document & Workflow Automation",
    version="1.0.0"
)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Document APIs
app.include_router(
    documents_router
)


# OCR APIs
app.include_router(
    ocr_router
)


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