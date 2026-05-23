"""Sales endpoints — accessible by analyst and admin roles."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..auth import require_role
from ..database import get_db
from ..models import DailySalesResponse, DailySalesItem

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


@router.get(
    "/daily",
    response_model=DailySalesResponse,
    summary="Get daily sales summary",
    description="Returns aggregated daily sales data from the fact_daily_sales table.",
)
async def get_daily_sales(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_role("analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Fetch daily sales data. Accessible by analyst and admin roles."""
    query = text(
        """
        SELECT
            date::text AS date,
            product_name,
            product_category,
            total_quantity_sold,
            total_revenue::float,
            avg_review_rating
        FROM fact_daily_sales
        ORDER BY date DESC, product_name
        LIMIT :limit OFFSET :offset
        """
    )
    result = await db.execute(query, {"limit": limit, "offset": offset})
    rows = result.fetchall()

    data = [
        DailySalesItem(
            date=row.date,
            product_name=row.product_name,
            product_category=row.product_category,
            total_quantity_sold=row.total_quantity_sold,
            total_revenue=row.total_revenue,
            avg_review_rating=row.avg_review_rating,
        )
        for row in rows
    ]

    return DailySalesResponse(data=data, count=len(data))
