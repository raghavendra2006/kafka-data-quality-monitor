"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Yield a database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
