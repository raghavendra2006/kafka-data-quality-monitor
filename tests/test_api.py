"""Integration tests for the Data Access API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.auth import create_access_token


@pytest.fixture
def analyst_token():
    """Generate a valid analyst JWT token."""
    return create_access_token(data={"sub": "test_analyst", "role": "analyst"})


@pytest.fixture
def admin_token():
    """Generate a valid admin JWT token."""
    return create_access_token(data={"sub": "test_admin", "role": "admin"})


# ---------------------------------------------------------------
# Health check
# ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_check():
    """Health endpoint returns 200 with correct structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "data-api"
    assert data["version"] == "1.0.0"


# ---------------------------------------------------------------
# Authentication enforcement
# ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_sales_endpoint_without_token():
    """Sales endpoint returns 403 without a token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sales/daily")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reviews_endpoint_without_token():
    """Reviews endpoint returns 403 without a token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/reviews/raw")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_sales_endpoint_with_invalid_token():
    """Sales endpoint returns 401 with an invalid/malformed token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/sales/daily",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
    assert resp.status_code == 401


# ---------------------------------------------------------------
# RBAC enforcement
# ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_reviews_with_analyst_token_returns_403(analyst_token):
    """Analyst role cannot access the admin-only reviews endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/reviews/raw",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
    assert resp.status_code == 403
    assert "does not have access" in resp.json()["detail"]


# ---------------------------------------------------------------
# Token generation endpoint
# ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_token_endpoint():
    """Token generation endpoint returns a valid JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/token",
            json={"username": "testuser", "role": "analyst"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_generate_admin_token_and_verify():
    """Generated admin token can be used for authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate token
        token_resp = await client.post(
            "/auth/token",
            json={"username": "admin_test", "role": "admin"},
        )
        assert token_resp.status_code == 200
        token = token_resp.json()["access_token"]

        # Verify it works (will fail with DB error but should pass auth)
        sales_resp = await client.get(
            "/api/v1/sales/daily",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should pass auth (not 401/403) — may get 500 if no DB, which is fine
        assert sales_resp.status_code != 401
        assert sales_resp.status_code != 403
