from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Dict
from uuid import uuid4

from app.core.schemas import OCRExtractedData


@dataclass
class PreviewRecord:
    preview_id: str
    created_at: datetime
    extracted_data: OCRExtractedData


class PreviewStore:
    def __init__(self) -> None:
        self._items: Dict[str, PreviewRecord] = {}
        self._lock = Lock()

    def create(self, extracted_data: OCRExtractedData) -> str:
        preview_id = f"prev_{uuid4().hex[:12]}"
        record = PreviewRecord(
            preview_id=preview_id,
            created_at=datetime.now(timezone.utc),
            extracted_data=extracted_data,
        )
        with self._lock:
            self._items[preview_id] = record
        return preview_id

    def exists(self, preview_id: str) -> bool:
        with self._lock:
            return preview_id in self._items


preview_store = PreviewStore()
