from __future__ import annotations

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database import engine
from app.core.config import settings


async def check_database() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "database reachable"
    except SQLAlchemyError as exc:
        return False, f"database unreachable: {exc.__class__.__name__}"


async def check_lm_studio() -> tuple[bool, str]:
    url = f"{settings.lm_studio_base_url}/v1/models"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        return True, "lm studio reachable"
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        return False, f"lm studio unreachable: {exc.__class__.__name__}"
