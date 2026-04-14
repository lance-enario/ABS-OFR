from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

import cv2
import httpx
import numpy as np
from pydantic import ValidationError

from app.core.config import settings
from app.core.constants import CANONICAL_MEASUREMENT_FIELDS
from app.core.schemas import OCRExtractedData, OCRMeasurements


@dataclass
class OCRExtractionResult:
    extracted_data: OCRExtractedData
    warnings: list[str]


class OCRServiceError(Exception):
    def __init__(self, error_code: str, message: str, recovery_suggestion: str | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.recovery_suggestion = recovery_suggestion


class OCRService:
    def __init__(self, max_edge_px: int = 1280) -> None:
        self.max_edge_px = max_edge_px

    async def extract(self, image_path: str) -> OCRExtractionResult:
        processed_image_b64, preprocess_warnings = self._preprocess_image(image_path)
        raw_text = await self._query_lm_studio(processed_image_b64)
        extracted_data, normalize_warnings = self._parse_and_validate(raw_text)

        warnings = [*preprocess_warnings, *normalize_warnings]
        return OCRExtractionResult(extracted_data=extracted_data, warnings=warnings)

    def _preprocess_image(self, image_path: str) -> tuple[str, list[str]]:
        warnings: list[str] = []

        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            raise OCRServiceError(
                error_code="IMAGE_UNREADABLE",
                message="Unable to read uploaded image.",
                recovery_suggestion="Retake the photo and ensure the image is not corrupted.",
            )

        corners = self._detect_fiducials(image)
        warped = self._warp_perspective(image, corners)

        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        enhanced = self._resize_max_edge(enhanced, self.max_edge_px)

        blur_score = float(cv2.Laplacian(enhanced, cv2.CV_64F).var())
        mean_luma = float(np.mean(enhanced))
        if blur_score < 40.0:
            warnings.append("Image appears blurry. Verify values carefully.")
        if mean_luma < 40.0 or mean_luma > 220.0:
            warnings.append("Image exposure is suboptimal. Verify values carefully.")

        ok, encoded = cv2.imencode(".jpg", enhanced, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            raise OCRServiceError(
                error_code="PREPROCESSING_FAILED",
                message="Failed to encode preprocessed image.",
                recovery_suggestion="Retake the photo and retry.",
            )

        return base64.b64encode(encoded.tobytes()).decode("utf-8"), warnings

    def _detect_fiducials(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 65, 255, cv2.THRESH_BINARY_INV)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[float, float]] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 40 or area > 25000:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            if h == 0:
                continue
            aspect = w / h
            if aspect < 0.4 or aspect > 2.5:
                continue

            m = cv2.moments(cnt)
            if m["m00"] == 0:
                continue
            cx = float(m["m10"] / m["m00"])
            cy = float(m["m01"] / m["m00"])
            candidates.append((cx, cy))

        if len(candidates) < 4:
            raise OCRServiceError(
                error_code="FIDUCIAL_NOT_FOUND",
                message="Could not detect all four corner fiducial markers.",
                recovery_suggestion="Ensure all four black corner markers are visible and retake the image.",
            )

        h, w = image.shape[:2]
        targets = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)

        points = np.array(candidates, dtype=np.float32)
        selected: list[np.ndarray] = []
        used: set[int] = set()

        for target in targets:
            dists = np.linalg.norm(points - target, axis=1)
            for idx in np.argsort(dists):
                if int(idx) not in used:
                    used.add(int(idx))
                    selected.append(points[idx])
                    break

        if len(selected) != 4:
            raise OCRServiceError(
                error_code="FIDUCIAL_NOT_FOUND",
                message="Failed to determine four unique fiducial corners.",
                recovery_suggestion="Retake the image with all corner markers fully visible.",
            )

        return np.array(selected, dtype=np.float32)

    @staticmethod
    def _warp_perspective(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        top_left, top_right, bottom_right, bottom_left = corners

        width_a = np.linalg.norm(bottom_right - bottom_left)
        width_b = np.linalg.norm(top_right - top_left)
        max_width = int(max(width_a, width_b))

        height_a = np.linalg.norm(top_right - bottom_right)
        height_b = np.linalg.norm(top_left - bottom_left)
        max_height = int(max(height_a, height_b))

        if max_width <= 0 or max_height <= 0:
            raise OCRServiceError(
                error_code="PERSPECTIVE_ERROR",
                message="Computed invalid output dimensions during perspective transform.",
                recovery_suggestion="Retake the image with the form fully inside the frame.",
            )

        destination = np.array(
            [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(corners, destination)
        return cv2.warpPerspective(image, matrix, (max_width, max_height))

    @staticmethod
    def _resize_max_edge(image: np.ndarray, max_edge_px: int) -> np.ndarray:
        h, w = image.shape[:2]
        longest = max(h, w)
        if longest <= max_edge_px:
            return image

        scale = max_edge_px / float(longest)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    async def _query_lm_studio(self, image_b64: str) -> str:
        system_prompt = (
            "Extract tailoring order data from the provided form image and return JSON only. "
            "Use inch fields only: chest_upper_in, chest_lower_in, waist_upper_in, waist_lower_in, "
            "sleeve_in, shoulder_in, inseam_in, hip_in. "
            "Do not include markdown fences or explanations."
        )

        user_instruction = (
            "Read handwritten values and output this JSON schema: "
            "{student_name, classification, school_name, measurements{...inch fields...}}. "
            "If unreadable, set value to null."
        )

        payload = {
            "model": settings.lm_studio_model,
            "temperature": 0.1,
            "max_tokens": 700,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_instruction},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                },
            ],
        }

        url = f"{settings.lm_studio_base_url}/v1/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            raise OCRServiceError(
                error_code="LM_STUDIO_UNAVAILABLE",
                message="LM Studio is unavailable for OCR extraction.",
                recovery_suggestion="Check LM Studio server status and retry, or proceed with manual entry.",
            ) from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OCRServiceError(
                error_code="OCR_RESPONSE_INVALID",
                message="LM Studio returned an unexpected response format.",
                recovery_suggestion="Retry OCR extraction or proceed with manual entry.",
            ) from exc

    def _parse_and_validate(self, raw_text: str) -> tuple[OCRExtractedData, list[str]]:
        warnings: list[str] = []

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise OCRServiceError(
                error_code="OCR_JSON_MISSING",
                message="Could not find JSON object in OCR response.",
                recovery_suggestion="Retry OCR extraction or enter values manually.",
            )

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise OCRServiceError(
                error_code="OCR_JSON_INVALID",
                message="OCR response contained malformed JSON.",
                recovery_suggestion="Retry OCR extraction or enter values manually.",
            ) from exc

        normalized_payload, normalize_warnings = self._normalize_payload(parsed)
        warnings.extend(normalize_warnings)

        try:
            extracted = OCRExtractedData(**normalized_payload)
        except ValidationError as exc:
            raise OCRServiceError(
                error_code="OCR_SCHEMA_INVALID",
                message=f"OCR response did not match required schema: {exc.errors()[0]['msg']}",
                recovery_suggestion="Retry OCR extraction or enter values manually.",
            ) from exc

        return extracted, warnings

    def _normalize_payload(self, payload: dict) -> tuple[dict, list[str]]:
        warnings: list[str] = []

        raw_measurements = payload.get("measurements")
        if not isinstance(raw_measurements, dict):
            raw_measurements = {}
            warnings.append("OCR did not return a measurements object.")

        measurements: dict[str, float | None] = {}
        for field in CANONICAL_MEASUREMENT_FIELDS:
            value = raw_measurements.get(field)
            if value is None:
                # Compatibility shim in case the model outputs cm fields.
                cm_field = field.replace("_in", "_cm")
                cm_value = raw_measurements.get(cm_field)
                if cm_value is not None:
                    try:
                        measurements[field] = round(float(cm_value) / 2.54, 2)
                        warnings.append(f"Converted {cm_field} to {field} from cm to inches.")
                    except (TypeError, ValueError):
                        measurements[field] = None
                        warnings.append(f"Could not parse {cm_field}; value set to null.")
                else:
                    measurements[field] = None
                continue

            try:
                measurements[field] = float(value)
            except (TypeError, ValueError):
                measurements[field] = None
                warnings.append(f"Could not parse {field}; value set to null.")

        student_name = str(payload.get("student_name") or "").strip()
        if not student_name:
            student_name = "PENDING_REVIEW"
            warnings.append("student_name missing; set to PENDING_REVIEW.")

        classification = str(payload.get("classification") or "").strip()
        if not classification:
            classification = "PENDING_REVIEW"
            warnings.append("classification missing; set to PENDING_REVIEW.")

        school_name_raw = payload.get("school_name")
        school_name = str(school_name_raw).strip() if school_name_raw is not None else None
        if school_name == "":
            school_name = None

        normalized = {
            "student_name": student_name,
            "classification": classification,
            "school_name": school_name,
            "measurements": measurements,
        }
        return normalized, warnings


ocr_service = OCRService()
