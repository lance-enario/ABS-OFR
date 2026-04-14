# Phase 1 Contract Lock (V1)

This document locks the canonical request/response structure for Phase 1 and early Phase 2 implementation.

## Canonical measurement fields

- `chest_upper_in`
- `chest_lower_in`
- `waist_upper_in`
- `waist_lower_in`
- `sleeve_in`
- `shoulder_in`
- `inseam_in`
- `hip_in`

Unit is always `in`.

Allowed range per numeric field: 4.0 to 80.0.

## Preview contract (uncommitted)

Endpoint target: `POST /api/v1/ocr/preview`

### Request

```json
{
  "image_base64": "<base64 image>",
  "preview_mode": true
}
```

### Response shape

```json
{
  "status": "success | partial | error",
  "preview_id": "string | null",
  "extracted_data": {
    "student_name": "string",
    "classification": "string",
    "school_name": "string | null",
    "measurements": {
      "chest_upper_in": 0,
      "chest_lower_in": 0,
      "waist_upper_in": 0,
      "waist_lower_in": 0,
      "sleeve_in": 0,
      "shoulder_in": 0,
      "inseam_in": 0,
      "hip_in": 0
    }
  },
  "warnings": [],
  "processing_time_ms": 0,
  "error": {
    "error_code": "string",
    "message": "string",
    "recovery_suggestion": "string | null"
  }
}
```

## Commit contract (verified only)

Endpoint target: `POST /api/v1/orders`

```json
{
  "preview_id": "prev_xxx",
  "verified_data": {
    "student_name": "string",
    "classification": "string",
    "school_name": "string | null",
    "measurements": {
      "chest_upper_in": 33.5,
      "chest_lower_in": 32,
      "waist_upper_in": 28,
      "waist_lower_in": 27.5,
      "sleeve_in": 18,
      "shoulder_in": 14,
      "inseam_in": 24,
      "hip_in": 35
    }
  }
}
```

## Notes

- Preview response must never commit records.
- Commit endpoint accepts only user-verified payloads.
- No image blobs are stored in database.
