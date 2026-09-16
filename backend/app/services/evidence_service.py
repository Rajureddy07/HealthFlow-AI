import re

from rapidfuzz import fuzz

from app.schemas.extraction import (
    PrescriptionExtraction,
    FieldEvidence,
    ExtractionEvidence,
)


class EvidenceService:

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------

    HIGH_OCR_CONFIDENCE = 0.80
    MEDIUM_OCR_CONFIDENCE = 0.60

    FUZZY_SIMILARITY_THRESHOLD = 80

    MIN_EVIDENCE_TEXT_LENGTH = 3

    # --------------------------------------------------
    # Text normalization
    # --------------------------------------------------

    def normalize_text(self, text: str) -> str:

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9]+",
            " ",
            text
        )

        text = " ".join(
            text.split()
        )

        return text.strip()

    # --------------------------------------------------
    # Exact evidence
    # --------------------------------------------------

    def find_exact_evidence(
        self,
        value: str,
        ocr_results: list
    ) -> list[str]:

        evidence = []

        value_normalized = self.normalize_text(
            value
        )

        if not value_normalized:
            return evidence

        for result in ocr_results:

            text = result["text"].strip()
            confidence = float(
                result["confidence"]
            )

            if len(text) < self.MIN_EVIDENCE_TEXT_LENGTH:
                continue

            text_normalized = self.normalize_text(
                text
            )

            if value_normalized in text_normalized:

                evidence.append(
                    f"{text} "
                    f"(OCR confidence: "
                    f"{confidence:.4f})"
                )

        return list(
            dict.fromkeys(evidence)
        )

    # --------------------------------------------------
    # Fuzzy evidence
    # --------------------------------------------------

    def find_fuzzy_evidence(
        self,
        value: str,
        ocr_results: list
    ) -> list[str]:

        evidence = []

        value_normalized = self.normalize_text(
            value
        )

        if not value_normalized:
            return evidence

        if len(value_normalized) < 4:

            return self.find_exact_evidence(
                value,
                ocr_results
            )

        for result in ocr_results:

            text = result["text"].strip()
            confidence = float(
                result["confidence"]
            )

            if len(text) < self.MIN_EVIDENCE_TEXT_LENGTH:
                continue

            text_normalized = self.normalize_text(
                text
            )

            if not text_normalized:
                continue

            similarity = fuzz.token_set_ratio(
                value_normalized,
                text_normalized
            )

            if similarity >= self.FUZZY_SIMILARITY_THRESHOLD:

                evidence.append(
                    f"{text} "
                    f"(OCR confidence: "
                    f"{confidence:.4f}, "
                    f"similarity: "
                    f"{similarity:.1f})"
                )

        return list(
            dict.fromkeys(evidence)
        )

    # --------------------------------------------------
    # Strength evidence
    # --------------------------------------------------

    def find_strength_evidence(
        self,
        strength: str,
        ocr_results: list
    ) -> list[str]:

        evidence = []

        strength_values = re.findall(
            r"\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|%)",
            strength.lower()
        )

        strength_values = list(
            dict.fromkeys(
                strength_values
            )
        )

        for result in ocr_results:

            text = result["text"].strip()
            text_lower = text.lower()
            confidence = float(
                result["confidence"]
            )

            if len(text) < 2:
                continue

            for value in strength_values:

                if value in text_lower:

                    evidence.append(
                        f"{text} "
                        f"(OCR confidence: "
                        f"{confidence:.4f})"
                    )

        return list(
            dict.fromkeys(evidence)
        )

    # --------------------------------------------------
    # Extract OCR confidence from evidence
    # --------------------------------------------------

    def extract_confidence(
        self,
        evidence_item: str
    ) -> float:

        match = re.search(
            r"OCR confidence:\s*(0\.\d+|1\.0+)",
            evidence_item
        )

        if not match:
            return 0.0

        return float(
            match.group(1)
        )

    # --------------------------------------------------
    # Calculate evidence confidence
    # --------------------------------------------------

    def calculate_confidence(
        self,
        evidence: list[str]
    ) -> float:

        if not evidence:
            return 0.0

        confidences = [
            self.extract_confidence(item)
            for item in evidence
        ]

        confidences = [
            confidence
            for confidence in confidences
            if confidence > 0
        ]

        if not confidences:
            return 0.0

        # Strongest OCR evidence
        strongest = max(
            confidences
        )

        # Multiple independent detections
        # provide additional consistency evidence.
        #
        # We intentionally keep this contribution
        # small so repeated weak OCR does not
        # automatically become high confidence.

        count_bonus = min(
            0.05,
            (len(confidences) - 1) * 0.025
        )

        confidence = min(
            1.0,
            strongest + count_bonus
        )

        return round(
            confidence,
            4
        )

    # --------------------------------------------------
    # Evaluate individual field
    # --------------------------------------------------

    def evaluate_field(
        self,
        field: str,
        value: str | None,
        evidence: list[str]
    ) -> FieldEvidence:

        confidence = self.calculate_confidence(
            evidence
        )

        if not value:

            status = "MISSING"

        elif not evidence:

            status = "UNSUPPORTED"

        elif confidence >= self.HIGH_OCR_CONFIDENCE:

            status = "HIGH"

        elif confidence >= self.MEDIUM_OCR_CONFIDENCE:

            status = "MEDIUM"

        else:

            status = "LOW"

        return FieldEvidence(
            field=field,
            value=value,
            evidence=evidence,
            confidence=confidence,
            status=status
        )

    # --------------------------------------------------
    # Evaluate complete extraction
    # --------------------------------------------------

    def evaluate(
        self,
        extraction: PrescriptionExtraction,
        ocr_results: list
    ) -> ExtractionEvidence:

        fields = []

        # ==================================================
        # Medicine Name
        # ==================================================

        medicine_evidence = []

        if extraction.medicine_name:

            medicine_evidence = self.find_fuzzy_evidence(
                extraction.medicine_name,
                ocr_results
            )

        fields.append(
            self.evaluate_field(
                field="medicine_name",
                value=extraction.medicine_name,
                evidence=medicine_evidence
            )
        )

        # ==================================================
        # Strength
        # ==================================================

        strength_value = None

        if extraction.strength:

            strength_value = extraction.strength.value

        strength_evidence = []

        if strength_value:

            strength_evidence = self.find_strength_evidence(
                strength_value,
                ocr_results
            )

        fields.append(
            self.evaluate_field(
                field="strength",
                value=strength_value,
                evidence=strength_evidence
            )
        )

        # ==================================================
        # Dosage Form
        # ==================================================

        dosage_evidence = []

        if extraction.dosage_form:

            dosage_evidence = self.find_fuzzy_evidence(
                extraction.dosage_form,
                ocr_results
            )

        fields.append(
            self.evaluate_field(
                field="dosage_form",
                value=extraction.dosage_form,
                evidence=dosage_evidence
            )
        )

        # ==================================================
        # Quantity
        # ==================================================

        quantity_value = None

        if extraction.quantity is not None:

            quantity_value = str(
                extraction.quantity
            )

        quantity_evidence = []

        if quantity_value:

            quantity_evidence = self.find_exact_evidence(
                quantity_value,
                ocr_results
            )

        fields.append(
            self.evaluate_field(
                field="quantity",
                value=quantity_value,
                evidence=quantity_evidence
            )
        )

        # ==================================================
        # Final Evidence Object
        # ==================================================

        return ExtractionEvidence(
            fields=fields
        )