"""Pydantic response models for the API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class DailySalesItem(BaseModel):
    """Single daily sales record."""
    date: str
    product_name: str
    product_category: str
    total_quantity_sold: int
    total_revenue: float
    avg_review_rating: float = Field(default=0.0)


class DailySalesResponse(BaseModel):
    """Response wrapper for daily sales endpoint."""
    data: List[DailySalesItem]
    count: int


class ReviewItem(BaseModel):
    """Single raw review record."""
    review_id: int
    product_id: int
    rating: int
    review_text: Optional[str] = None


class ReviewsResponse(BaseModel):
    """Response wrapper for raw reviews endpoint."""
    data: List[ReviewItem]
    count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str


class TokenResponse(BaseModel):
    """Token generation response."""
    access_token: str
    token_type: str = "bearer"


class TokenRequest(BaseModel):
    """Token generation request."""
    username: str
    role: str = Field(pattern="^(analyst|admin)$")
