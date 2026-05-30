"""FastAPI application entry point."""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine

from app.routers import auth, categories, dashboard, expenses, flows, members, salary, venues

logging.basicConfig(
    level=logging.INFO if settings.APP_ENV == "production" else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("🚀 TeamLedgerBot API starting up (env=%s)", settings.APP_ENV)
    
    # Run Alembic migrations in a background subprocess to avoid healthcheck blocking
    try:
        import subprocess
        logger.info("🔄 Running database migrations via Alembic...")
        process = subprocess.Popen(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("⚡ Alembic migrations started in background (PID: %d)", process.pid)
    except Exception as e:
        logger.error("❌ Failed to start Alembic migrations: %s", e)

    yield
    logger.info("🛑 TeamLedgerBot API shutting down")
    await engine.dispose()


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="TeamLedgerBot API",
    description="Team Operations Data Platform — Daily Flows, Expenses, Salary & Analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(flows.router, prefix="/api", tags=["Flows"])
app.include_router(expenses.router, prefix="/api", tags=["Expenses"])
app.include_router(salary.router, prefix="/api", tags=["Salary"])
app.include_router(members.router, prefix="/api", tags=["Members"])
app.include_router(categories.router, prefix="/api", tags=["Categories"])
app.include_router(venues.router, prefix="/api", tags=["Venues"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
