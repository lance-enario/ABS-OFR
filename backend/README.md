# Tailoring OCR Backend (Phase 2 In Progress)

This backend is the Phase 1 foundation for the Annies Boutique Scan - Order Form Record System.

## Current scope

- Shared contracts for OCR preview and order commit flows.
- FastAPI app skeleton with versioned routing.
- Baseline health endpoint for backend, database, and LM Studio checks.
- Core config, constants, and standard API error envelope.
- SQLAlchemy data models for orders and measurements.
- OCR preview route scaffold with temp image cleanup.
- Order commit and list routes with graceful DB failure responses.

## Quick start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and update values.
4. Run:

```powershell
uvicorn app.main:app --reload
```

## API base URL

- `http://127.0.0.1:8000`
- Versioned routes under `/api/v1`

## Implemented endpoints

- `GET /`
- `GET /api/v1/health`
- `GET /api/v1/contracts/metadata`
- `POST /api/v1/ocr/preview`
- `POST /api/v1/orders`
- `GET /api/v1/orders/list`

## Next in Phase 2

- Implement OpenCV preprocessing pipeline (fiducial + homography + resize).
- Replace OCR scaffold with LM Studio extraction + JSON validation.
- Add migration tooling (Alembic) and export endpoint.
