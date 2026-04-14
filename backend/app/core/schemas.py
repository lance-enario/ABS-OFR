from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import (
    CANONICAL_MEASUREMENT_FIELDS,
    MEASUREMENT_MAX_IN,
    MEASUREMENT_MIN_IN,
)


class ErrorEnvelope(BaseModel):
    error_code: str
    message: str
    recovery_suggestion: str | None = None


class HealthSection(BaseModel):
    connected: bool
    detail: str


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    backend: HealthSection
    database: HealthSection
    lm_studio: HealthSection
    timestamp: datetime


class OCRMeasurements(BaseModel):
    chest_upper_in: float | None = None
    chest_lower_in: float | None = None
    waist_upper_in: float | None = None
    waist_lower_in: float | None = None
    sleeve_in: float | None = None
    shoulder_in: float | None = None
    inseam_in: float | None = None
    hip_in: float | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def validate_range(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not (MEASUREMENT_MIN_IN <= value <= MEASUREMENT_MAX_IN):
            raise ValueError(
                f"measurement must be between {MEASUREMENT_MIN_IN} and {MEASUREMENT_MAX_IN} inches"
            )
        return value


class OCRExtractedData(BaseModel):
    student_name: str = Field(min_length=1, max_length=255)
    classification: str = Field(min_length=1, max_length=100)
    school_name: str | None = Field(default=None, max_length=255)
    measurements: OCRMeasurements


class OCRPreviewRequest(BaseModel):
    image_base64: str = Field(min_length=20)
    preview_mode: bool = True


class OCRPreviewResponse(BaseModel):
    status: Literal["success", "partial", "error"]
    preview_id: str | None = None
    extracted_data: OCRExtractedData | None = None
    warnings: list[str] = Field(default_factory=list)
    processing_time_ms: int | None = None
    error: ErrorEnvelope | None = None


class OrderCommitRequest(BaseModel):
    preview_id: str = Field(min_length=1, max_length=100)
    verified_data: OCRExtractedData


class OrderCommitResponse(BaseModel):
    status: Literal["committed"]
    order_id: int
    created_at: datetime
    message: str


class OrderListQuery(BaseModel):
    year: int | None = None
    month: int | None = None
    classification: str | None = None
    search: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class OrderListItem(BaseModel):
    id: int
    student_name: str
    classification: str
    school_name: str | None = None
    created_at: datetime


class OrderListResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    items: list[OrderListItem]


class ContractMetadata(BaseModel):
    canonical_measurement_fields: tuple[str, ...] = CANONICAL_MEASUREMENT_FIELDS
    unit: Literal["in"] = "in"
    min_in: float = MEASUREMENT_MIN_IN
    max_in: float = MEASUREMENT_MAX_IN
