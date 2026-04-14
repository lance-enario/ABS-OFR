# Tailoring OCR Backend (Phase 1)

This backend is the Phase 1 foundation for the Annies Boutique Scan - Order Form Record System.

## Current scope

- Shared contracts for OCR preview and order commit flows.
- FastAPI app skeleton with versioned routing.
- Baseline health endpoint for backend, database, and LM Studio checks.
- Core config, constants, and standard API error envelope.

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

## Next in Phase 1

- Add SQLAlchemy models and migrations.
- Add OCR preview route skeleton with request validation only.
- Lock canonical measurement schema with examples.
