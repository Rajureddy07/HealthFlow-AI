class OCRQualityService:

    MIN_TEXT_LENGTH = 5
    MIN_AVERAGE_CONFIDENCE = 0.60
    MIN_INDIVIDUAL_CONFIDENCE = 0.40

    def check_quality(self, ocr_results):

        if not ocr_results:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "No text detected"
            }

        # Combine OCR text
        full_text = " ".join(
            result["text"]
            for result in ocr_results
        )

        # Calculate average confidence
        total_confidence = sum(
            result["confidence"]
            for result in ocr_results
        )

        average_confidence = (
            total_confidence / len(ocr_results)
        )

        # Check text length
        if len(full_text.strip()) < self.MIN_TEXT_LENGTH:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "Insufficient text detected",
                "average_confidence": round(
                    average_confidence, 4
                )
            }

        # Find low-confidence OCR results
        low_confidence_results = [
            result
            for result in ocr_results
            if result["confidence"] < self.MIN_INDIVIDUAL_CONFIDENCE
        ]

        # Check average confidence
        if average_confidence < self.MIN_AVERAGE_CONFIDENCE:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "Low average OCR confidence",
                "average_confidence": round(
                    average_confidence, 4
                ),
                "low_confidence_results": low_confidence_results
            }

        # Check individual confidence
        if low_confidence_results:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "One or more OCR results have low confidence",
                "average_confidence": round(
                    average_confidence, 4
                ),
                "low_confidence_results": low_confidence_results
            }

        return {
            "quality_status": "PASSED",
            "reason": "OCR quality is acceptable",
            "average_confidence": round(
                average_confidence, 4
            ),
            "low_confidence_results": []
        }