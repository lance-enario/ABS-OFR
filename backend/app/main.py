from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.infrastructure.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
    )

    @app.on_event("startup")
    def startup() -> None:
        init_db()

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": settings.app_name, "status": "ok"}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
