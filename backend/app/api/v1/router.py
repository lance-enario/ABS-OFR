from fastapi import APIRouter

from app.api.v1.routes.contracts import router as contracts_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.ocr import router as ocr_router
from app.api.v1.routes.orders import router as orders_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(contracts_router, tags=["contracts"])
api_router.include_router(ocr_router, tags=["ocr"])
api_router.include_router(orders_router, tags=["orders"])

