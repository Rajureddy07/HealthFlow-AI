class OCRQualityService:

    MIN_TEXT_LENGTH = 10
    RELIABLE_CONFIDENCE = 0.60
    MIN_RELIABLE_RESULTS = 3

    def check_quality(self, ocr_results):

        if not ocr_results:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "No text detected",
                "average_confidence": 0.0,
                "reliable_result_count": 0
            }

        # Combine detected text
        full_text = " ".join(
            result["text"].strip()
            for result in ocr_results
            if result["text"].strip()
        )

        # Calculate average OCR confidence
        total_confidence = sum(
            result["confidence"]
            for result in ocr_results
        )

        average_confidence = (
            total_confidence / len(ocr_results)
        )

        # Identify reliable OCR detections
        reliable_results = [
            result
            for result in ocr_results
            if (
                result["confidence"] >= self.RELIABLE_CONFIDENCE
                and len(result["text"].strip()) >= 2
            )
        ]

        # Identify low-confidence detections
        low_confidence_results = [
            result
            for result in ocr_results
            if result["confidence"] < self.RELIABLE_CONFIDENCE
        ]

        # Basic readability check
        if len(full_text.strip()) < self.MIN_TEXT_LENGTH:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "Insufficient readable text detected",
                "average_confidence": round(
                    average_confidence, 4
                ),
                "reliable_result_count": len(reliable_results)
            }

        # Need enough reliable OCR evidence
        if len(reliable_results) < self.MIN_RELIABLE_RESULTS:
            return {
                "quality_status": "NEEDS_REVIEW",
                "reason": "Insufficient high-confidence OCR results",
                "average_confidence": round(
                    average_confidence, 4
                ),
                "reliable_result_count": len(reliable_results),
                "low_confidence_count": len(
                    low_confidence_results
                )
            }

        # Document is readable.
        # Low-confidence noise does NOT automatically block processing.
        return {
            "quality_status": "PASSED",
            "reason": "Document contains sufficient reliable OCR text",
            "average_confidence": round(
                average_confidence, 4
            ),
            "reliable_result_count": len(reliable_results),
            "low_confidence_count": len(
                low_confidence_results
            ),
            "low_confidence_results": low_confidence_results
        }