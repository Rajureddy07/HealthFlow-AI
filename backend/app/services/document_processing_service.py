from app.services.ocr_service import OCRService
from app.services.ocr_quality_service import OCRQualityService
from app.services.extraction_service import ExtractionService
from app.services.evidence_service import EvidenceService
from app.services.validation_service import ValidationService


class DocumentProcessingService:

    def __init__(self):
        self.ocr_service = OCRService()
        self.quality_service = OCRQualityService()
        self.extraction_service = ExtractionService()
        self.evidence_service = EvidenceService()
        self.validation_service = ValidationService()

    def process(self, file_path: str):

        # --------------------------------
        # 1. OCR
        # --------------------------------

        ocr_results = self.ocr_service.extract_text(
            file_path
        )

        # --------------------------------
        # 2. OCR Quality Check
        # --------------------------------

        quality_result = self.quality_service.check_quality(
            ocr_results
        )

        # Convert OCR results into plain text
        ocr_text = " ".join(
            result["text"]
            for result in ocr_results
        )

        # --------------------------------
        # 3. Stop if OCR quality is poor
        # --------------------------------

        if quality_result["quality_status"] != "PASSED":

            return {
                "status": "NEEDS_REVIEW",
                "stage": "OCR_QUALITY",
                "quality": quality_result,
                "extraction": None,
                "evidence": None,
                "validation": None
            }

        # --------------------------------
        # 4. AI Structured Extraction
        # --------------------------------

        extraction = self.extraction_service.extract(
            ocr_text
        )

        # --------------------------------
        # 5. Field-level Evidence
        # --------------------------------

        evidence = self.evidence_service.evaluate(
            extraction,
            ocr_results
        )

        # --------------------------------
        # 6. Deterministic Validation
        # --------------------------------

        validation = self.validation_service.validate(
            extraction,
            evidence,
            ocr_text
        )

        # --------------------------------
        # 7. Final Workflow Decision
        # --------------------------------

        if validation.status == "PASSED":

            final_status = "APPROVED"

        else:

            final_status = "NEEDS_REVIEW"

        # --------------------------------
        # 8. Final Processing Result
        # --------------------------------

        return {
            "status": final_status,
            "stage": "VALIDATION",

            "quality": quality_result,

            "extraction": extraction.model_dump(),

            "evidence": evidence.model_dump(),

            "validation": validation.model_dump()
        }