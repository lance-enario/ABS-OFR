from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.schemas import HealthResponse, HealthSection
from app.services.health_service import check_database, check_lm_studio

router = APIRouter(prefix="/health")


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_connected, db_detail = await check_database()
    lm_connected, lm_detail = await check_lm_studio()

    status = "healthy" if db_connected and lm_connected else "degraded"
    return HealthResponse(
        status=status,
        backend=HealthSection(connected=True, detail="backend online"),
        database=HealthSection(connected=db_connected, detail=db_detail),
        lm_studio=HealthSection(connected=lm_connected, detail=lm_detail),
        timestamp=datetime.now(timezone.utc),
    )
