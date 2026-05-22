"""Async SQLAlchemy database engine, session factory, and Base class."""
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Build SSL context for asyncpg (required for Neon on Windows)
_ssl_context = ssl.create_default_context()

# Strip ssl/sslmode from URL — pass SSL via connect_args instead
_db_url = settings.DATABASE_URL.replace("?ssl=require", "").replace(
    "?sslmode=require", ""
).replace("&ssl=require", "").replace("&sslmode=require", "")

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    _db_url,
    echo=(settings.APP_ENV == "development"),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"ssl": _ssl_context},
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ── Declarative Base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
