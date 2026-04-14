from __future__ import annotations

import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class TempImageManager:
    def __init__(self) -> None:
        self._base_dir = Path(tempfile.gettempdir()) / "abs_ofr"
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def temp_image(self, image_bytes: bytes, suffix: str = ".jpg") -> Iterator[Path]:
        temp_path = self._base_dir / f"img_{uuid.uuid4().hex}{suffix}"
        temp_path.write_bytes(image_bytes)
        try:
            yield temp_path
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                # Keep non-fatal; deletion is best-effort at this layer.
                pass
