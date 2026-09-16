from app.services.document_processing_service import (
    DocumentProcessingService
)


file_path = "uploads/Screenshot 2026-08-15 200829.png"


service = DocumentProcessingService()

result = service.process(
    file_path
)

print("Document processing completed!")
print(result)