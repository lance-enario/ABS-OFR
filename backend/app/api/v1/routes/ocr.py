from __future__ import annotations

import base64
import binascii
import time

from fastapi import APIRouter, HTTPException, status

from app.core.schemas import ErrorEnvelope, OCRPreviewRequest, OCRPreviewResponse
from app.infrastructure.temp_manager import TempImageManager
from app.services.ocr_service import OCRServiceError, ocr_service
from app.services.preview_store import preview_store

router = APIRouter(prefix="/ocr")
temp_manager = TempImageManager()


def _decode_image(image_base64: str) -> bytes:
    payload = image_base64
    if "," in image_base64 and image_base64.startswith("data:"):
        payload = image_base64.split(",", 1)[1]

    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"invalid image_base64 payload: {exc.__class__.__name__}",
        ) from exc


@router.post("/preview", response_model=OCRPreviewResponse)
async def preview(payload: OCRPreviewRequest) -> OCRPreviewResponse:
    started = time.perf_counter()
    image_bytes = _decode_image(payload.image_base64)

    try:
        with temp_manager.temp_image(image_bytes) as temp_path:
            result = await ocr_service.extract(str(temp_path))
    except OCRServiceError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return OCRPreviewResponse(
            status="error",
            processing_time_ms=elapsed_ms,
            error=ErrorEnvelope(
                error_code=exc.error_code,
                message=exc.message,
                recovery_suggestion=exc.recovery_suggestion,
            ),
        )

    preview_id = preview_store.create(result.extracted_data)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    response_status = "partial" if result.warnings else "success"

    return OCRPreviewResponse(
        status=response_status,
        preview_id=preview_id,
        extracted_data=result.extracted_data,
        warnings=result.warnings,
        processing_time_ms=elapsed_ms,
    )
