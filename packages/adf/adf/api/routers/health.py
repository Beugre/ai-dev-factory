"""Health and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from adf.infrastructure.db import get_sessionmaker

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness probe: verifies the database is reachable."""
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not-ready"}
