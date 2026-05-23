"""Reviews endpoints — accessible by admin role only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..auth import require_role
from ..database import get_db
from ..models import ReviewsResponse, ReviewItem

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get(
    "/raw",
    response_model=ReviewsResponse,
    summary="Get raw customer reviews",
    description="Returns raw review data including review text. Admin only.",
)
async def get_raw_reviews(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Fetch raw review data. Accessible by admin role only."""
    query = text(
        """
        SELECT
            review_id,
            product_id,
            rating,
            review_text
        FROM raw.reviews
        ORDER BY review_id
        LIMIT :limit OFFSET :offset
        """
    )
    result = await db.execute(query, {"limit": limit, "offset": offset})
    rows = result.fetchall()

    data = [
        ReviewItem(
            review_id=row.review_id,
            product_id=row.product_id,
            rating=row.rating,
            review_text=row.review_text,
        )
        for row in rows
    ]

    return ReviewsResponse(data=data, count=len(data))
