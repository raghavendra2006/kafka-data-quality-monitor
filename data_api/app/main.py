"""
Data Access API — FastAPI Application
======================================
Provides REST endpoints for querying the data warehouse.
Secured with JWT-based RBAC (analyst / admin roles).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import HealthResponse, TokenRequest, TokenResponse
from .auth import create_access_token
from .routes import sales, reviews

app = FastAPI(
    title="Data Platform API",
    description="Secure REST API for the Data Quality Monitoring Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"], # Replace with frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sales.router)
app.include_router(reviews.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint for Docker health checks."""
    return HealthResponse(
        status="healthy",
        service="data-api",
        version="1.0.0",
    )


@app.post(
    "/auth/token",
    response_model=TokenResponse,
    tags=["auth"],
    summary="Generate a JWT token for testing",
    description="Generate a JWT token with the specified username and role. "
    "This is a convenience endpoint for development and testing.",
)
async def generate_token(request: TokenRequest):
    """Generate a JWT for testing. In production, use a proper auth provider."""
    token = create_access_token(
        data={"sub": request.username, "role": request.role}
    )
    return TokenResponse(access_token=token)
