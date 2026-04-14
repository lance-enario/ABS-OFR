from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.schemas import OrderCommitRequest, OrderListItem, OrderListQuery, OrderListResponse
from app.models.db import Measurement, Order


def create_order(db: Session, payload: OrderCommitRequest) -> Order:
    now = datetime.now(timezone.utc)
    order = Order(
        student_name=payload.verified_data.student_name,
        classification=payload.verified_data.classification,
        school_name=payload.verified_data.school_name,
        preview_id=payload.preview_id,
        created_year=now.year,
        created_month=now.month,
    )
    db.add(order)
    db.flush()

    for field_name, value in payload.verified_data.measurements.model_dump().items():
        if value is None:
            continue
        db.add(Measurement(order_id=order.id, field_name=field_name, value_in=float(value)))

    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, query: OrderListQuery) -> OrderListResponse:
    filters = []
    if query.year is not None:
        filters.append(Order.created_year == query.year)
    if query.month is not None:
        filters.append(Order.created_month == query.month)
    if query.classification:
        filters.append(Order.classification == query.classification)
    if query.search:
        pattern = f"%{query.search.strip()}%"
        filters.append(
            or_(
                Order.student_name.ilike(pattern),
                Order.school_name.ilike(pattern),
            )
        )

    total_stmt = select(func.count()).select_from(Order)
    if filters:
        total_stmt = total_stmt.where(*filters)
    total_count = db.scalar(total_stmt) or 0

    stmt = (
        select(Order)
        .where(*filters) if filters else select(Order)
    )
    stmt = stmt.order_by(Order.created_at.desc()).offset(query.offset).limit(query.limit)

    rows = db.scalars(stmt).all()
    items = [
        OrderListItem(
            id=row.id,
            student_name=row.student_name,
            classification=row.classification,
            school_name=row.school_name,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return OrderListResponse(
        total_count=total_count,
        limit=query.limit,
        offset=query.offset,
        items=items,
    )
