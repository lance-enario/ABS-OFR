from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.schemas import (
    OrderCommitRequest,
    OrderCommitResponse,
    OrderListQuery,
    OrderListResponse,
)
from app.infrastructure.database import get_db
from app.services.order_service import create_order, list_orders
from app.services.preview_store import preview_store

router = APIRouter(prefix="/orders")


@router.post("", response_model=OrderCommitResponse, status_code=status.HTTP_201_CREATED)
async def commit_order(
    payload: OrderCommitRequest,
    db: Annotated[Session, Depends(get_db)],
) -> OrderCommitResponse:
    if not preview_store.exists(payload.preview_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="preview_id not found or expired",
        )

    try:
        order = create_order(db, payload)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unavailable: {exc.__class__.__name__}",
        ) from exc

    return OrderCommitResponse(
        status="committed",
        order_id=order.id,
        created_at=order.created_at,
        message="Order committed successfully.",
    )


@router.get("/list", response_model=OrderListResponse)
async def get_orders(
    db: Annotated[Session, Depends(get_db)],
    year: int | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    classification: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> OrderListResponse:
    query = OrderListQuery(
        year=year,
        month=month,
        classification=classification,
        search=search,
        limit=limit,
        offset=offset,
    )
    try:
        return list_orders(db, query)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unavailable: {exc.__class__.__name__}",
        ) from exc
