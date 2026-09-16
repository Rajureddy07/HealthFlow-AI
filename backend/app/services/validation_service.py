from app.schemas.extraction import PrescriptionExtraction
from app.schemas.extraction import ExtractionEvidence
from app.schemas.validation import (
    ValidationIssue,
    ValidationResult,
)


class ValidationService:

    # Critical fields must have strong evidence
    CRITICAL_FIELDS = {
        "medicine_name",
        "strength",
    }

    # Minimum evidence confidence required
    # for critical fields
    MIN_CRITICAL_CONFIDENCE = 0.80

    def validate(
        self,
        extraction: PrescriptionExtraction,
        evidence: ExtractionEvidence,
        ocr_text: str
    ) -> ValidationResult:

        issues = []

        # --------------------------------------------------
        # Create easy lookup for field evidence
        # --------------------------------------------------

        evidence_map = {
            field.field: field
            for field in evidence.fields
        }

        # ==================================================
        # 1. MEDICINE NAME
        # ==================================================

        medicine_evidence = evidence_map.get(
            "medicine_name"
        )

        if not extraction.medicine_name:

            issues.append(
                ValidationIssue(
                    field="medicine_name",
                    message="Medicine name was not extracted",
                    severity="HIGH"
                )
            )

        elif not medicine_evidence:

            issues.append(
                ValidationIssue(
                    field="medicine_name",
                    message="No evidence found for medicine name",
                    severity="HIGH"
                )
            )

        elif medicine_evidence.status in {
            "MISSING",
            "UNSUPPORTED"
        }:

            issues.append(
                ValidationIssue(
                    field="medicine_name",
                    message="Medicine name is not sufficiently supported by OCR evidence",
                    severity="HIGH"
                )
            )

        elif (
            medicine_evidence.confidence
            < self.MIN_CRITICAL_CONFIDENCE
        ):

            issues.append(
                ValidationIssue(
                    field="medicine_name",
                    message="Medicine name has low OCR evidence confidence",
                    severity="HIGH"
                )
            )

        # ==================================================
        # 2. STRENGTH
        # ==================================================

        strength_evidence = evidence_map.get(
            "strength"
        )

        if (
            not extraction.strength
            or not extraction.strength.value
        ):

            issues.append(
                ValidationIssue(
                    field="strength",
                    message="Medicine strength was not extracted",
                    severity="HIGH"
                )
            )

        elif not strength_evidence:

            issues.append(
                ValidationIssue(
                    field="strength",
                    message="No evidence found for medicine strength",
                    severity="HIGH"
                )
            )

        elif strength_evidence.status in {
            "MISSING",
            "UNSUPPORTED"
        }:

            issues.append(
                ValidationIssue(
                    field="strength",
                    message="Medicine strength is not supported by OCR evidence",
                    severity="HIGH"
                )
            )

        elif (
            strength_evidence.confidence
            < self.MIN_CRITICAL_CONFIDENCE
        ):

            issues.append(
                ValidationIssue(
                    field="strength",
                    message="Medicine strength has low OCR evidence confidence",
                    severity="HIGH"
                )
            )

        # ==================================================
        # 3. DOSAGE FORM
        # ==================================================

        dosage_evidence = evidence_map.get(
            "dosage_form"
        )

        if not extraction.dosage_form:

            issues.append(
                ValidationIssue(
                    field="dosage_form",
                    message="Dosage form was not extracted",
                    severity="MEDIUM"
                )
            )

        elif not dosage_evidence:

            issues.append(
                ValidationIssue(
                    field="dosage_form",
                    message="No evidence found for dosage form",
                    severity="MEDIUM"
                )
            )

        elif dosage_evidence.status in {
            "MISSING",
            "UNSUPPORTED"
        }:

            issues.append(
                ValidationIssue(
                    field="dosage_form",
                    message="Dosage form is not supported by OCR evidence",
                    severity="MEDIUM"
                )
            )

        # ==================================================
        # 4. FINAL DECISION
        # ==================================================

        high_issues = sum(
            1
            for issue in issues
            if issue.severity == "HIGH"
        )

        medium_issues = sum(
            1
            for issue in issues
            if issue.severity == "MEDIUM"
        )

        # --------------------------------------------------
        # Any HIGH severity issue requires human review
        # --------------------------------------------------

        if high_issues > 0:

            status = "NEEDS_REVIEW"

            confidence = 0.40

        # --------------------------------------------------
        # Medium issues can also require review
        # depending on future policy
        # --------------------------------------------------

        elif medium_issues > 0:

            status = "NEEDS_REVIEW"

            confidence = 0.70

        # --------------------------------------------------
        # No validation issues
        # --------------------------------------------------

        else:

            status = "PASSED"

            confidence = 1.0

        return ValidationResult(
            status=status,
            confidence=confidence,
            issues=issues
        )