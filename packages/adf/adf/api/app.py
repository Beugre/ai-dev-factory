"""FastAPI application factory."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from adf.api.errors import install_error_handlers
from adf.api.routers import (
    approvals,
    epics,
    feature_requests,
    health,
    observability,
    projects,
    pull_requests,
    questions,
    stories,
    webhooks,
)
from adf.config import get_settings
from adf.infrastructure.db import create_all
from adf.infrastructure.logging import configure_logging, set_correlation_id
from adf.infrastructure.metrics import http_requests_total, request_latency_seconds

API_PREFIX = "/api/v1"

OPENAPI_TAGS = [
    {"name": "projects", "description": "Projets cibles."},
    {"name": "feature-requests", "description": "Demandes fonctionnelles."},
    {"name": "questions", "description": "Questions de clarification."},
    {"name": "epics", "description": "Epics générés."},
    {"name": "stories", "description": "Stories et dispatch Copilot."},
    {"name": "approvals", "description": "Validations humaines."},
    {"name": "pull-requests", "description": "Pull requests et staging."},
    {"name": "observability", "description": "Agent runs, déploiements, audit."},
    {"name": "webhooks", "description": "Webhooks GitHub."},
    {"name": "health", "description": "Sondes santé/readiness."},
]


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        set_correlation_id(correlation_id)
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path
        request_latency_seconds.labels(path=path).observe(elapsed)
        http_requests_total.labels(
            method=request.method, path=path, status=str(response.status_code)
        ).inc()
        response.headers["X-Correlation-ID"] = correlation_id
        return response


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="AI Dev Factory API",
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
        description="Pilotez la construction d'une application depuis votre téléphone.",
    )
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_base_url, "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_error_handlers(app)

    @app.on_event("startup")
    async def _startup() -> None:
        # SQLite dev/test convenience: ensure tables exist. Prod uses Alembic.
        if settings.is_sqlite:
            await create_all()

    for module in (
        health,
        projects,
        feature_requests,
        questions,
        epics,
        stories,
        approvals,
        pull_requests,
        observability,
        webhooks,
    ):
        app.include_router(module.router, prefix=API_PREFIX)

    # Also expose health/readiness at the root for infra probes.
    app.include_router(health.router)

    @app.get("/metrics", include_in_schema=False)
    async def metrics(x_metrics_token: str | None = Header(default=None)) -> Response:
        if settings.metrics_token and x_metrics_token != settings.metrics_token:
            return Response(status_code=401)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
