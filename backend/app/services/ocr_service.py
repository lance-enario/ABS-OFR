from __future__ import annotations

from app.core.schemas import OCRExtractedData, OCRMeasurements


class OCRService:
    """
    Phase 2 scaffold: returns a valid contract payload.
    LM Studio extraction will be plugged in after preprocessing implementation.
    """

    async def extract(self, image_path: str) -> OCRExtractedData:
        _ = image_path
        return OCRExtractedData(
            student_name="PENDING_REVIEW",
            classification="PENDING_REVIEW",
            school_name=None,
            measurements=OCRMeasurements(),
        )


ocr_service = OCRService()
