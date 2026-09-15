from app.schemas.extraction import PrescriptionExtraction
from app.schemas.validation import (
    ValidationIssue,
    ValidationResult
)


class ValidationService:

    def validate(
        self,
        extraction: PrescriptionExtraction,
        ocr_text: str
    ) -> ValidationResult:

        issues = []

        # --------------------------------
        # 1. Medicine name validation
        # --------------------------------

        if not extraction.medicine_name:
            issues.append(
                ValidationIssue(
                    field="medicine_name",
                    message="Medicine name was not extracted",
                    severity="HIGH"
                )
            )

        # --------------------------------
        # 2. Strength validation
        # --------------------------------

        if not extraction.strength:
            issues.append(
                ValidationIssue(
                    field="strength",
                    message="Medicine strength was not extracted",
                    severity="HIGH"
                )
            )

        # --------------------------------
        # 3. Dosage form validation
        # --------------------------------

        if not extraction.dosage_form:
            issues.append(
                ValidationIssue(
                    field="dosage_form",
                    message="Dosage form was not extracted",
                    severity="MEDIUM"
                )
            )

        # --------------------------------
        # 4. Check extracted values against
        #    original OCR text
        # --------------------------------

        ocr_lower = ocr_text.lower()

        if extraction.medicine_name:

            medicine_name = (
                extraction.medicine_name.lower()
            )

            if medicine_name not in ocr_lower:
                issues.append(
                    ValidationIssue(
                        field="medicine_name",
                        message=(
                            "Extracted medicine name "
                            "was not found in OCR text"
                        ),
                        severity="HIGH"
                    )
                )

        # --------------------------------
        # 5. Calculate validation confidence
        # --------------------------------

        if not issues:
            confidence = 1.0
            status = "PASSED"

        else:

            high_issues = sum(
                1
                for issue in issues
                if issue.severity == "HIGH"
            )

            if high_issues > 0:
                confidence = 0.40
            else:
                confidence = 0.70

            status = "NEEDS_REVIEW"

        return ValidationResult(
            status=status,
            confidence=confidence,
            issues=issues
        )