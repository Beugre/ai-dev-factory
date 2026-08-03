"""Map domain errors to structured HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adf.domain.errors import (
    BlockingQuestionsUnanswered,
    CIFailure,
    DomainError,
    EntityNotFound,
    HumanApprovalRequired,
    InvalidStateTransition,
    ScopeNotApproved,
)
from adf.infrastructure.logging import get_correlation_id, get_logger

logger = get_logger("adf.api")

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    EntityNotFound: 404,
    InvalidStateTransition: 409,
    BlockingQuestionsUnanswered: 409,
    ScopeNotApproved: 409,
    HumanApprovalRequired: 403,
    CIFailure: 409,
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        status = _STATUS_BY_ERROR.get(type(exc), 400)
        logger.info("domain_error", code=exc.code, status=status, detail=str(exc))
        return JSONResponse(
            status_code=status,
            content={
                "code": exc.code,
                "message": str(exc),
                "correlation_id": get_correlation_id(),
            },
        )
