"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine

# ── Routers (imported in Phase 2 when implementations are ready) ──────────────
from app.routers import income, expense, salary, transactions, members, categories, dashboard

logging.basicConfig(
    level=logging.INFO if settings.APP_ENV == "production" else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("🚀 TeamLedgerBot API starting up (env=%s)", settings.APP_ENV)
    yield
    logger.info("🛑 TeamLedgerBot API shutting down")
    await engine.dispose()


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="TeamLedgerBot API",
    description="Team Operations Data Platform — Income, Expense, Salary & Analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(income.router, prefix="/api", tags=["Income"])
app.include_router(expense.router, prefix="/api", tags=["Expense"])
app.include_router(salary.router, prefix="/api", tags=["Salary"])
app.include_router(transactions.router, prefix="/api", tags=["Transactions"])
app.include_router(members.router, prefix="/api", tags=["Members"])
app.include_router(categories.router, prefix="/api", tags=["Categories"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
