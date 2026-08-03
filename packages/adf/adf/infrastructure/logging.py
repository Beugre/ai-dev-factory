"""Structured JSON logging with correlation-id support.

Never log secrets. Adapters must scrub tokens before logging.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

import structlog
from structlog.typing import EventDict, WrappedLogger

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str | None) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def _add_correlation_id(
    _: WrappedLogger, __: str, event_dict: EventDict
) -> EventDict:
    cid = _correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(format="%(message)s", level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            _add_correlation_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_logger(name: str = "adf") -> structlog.stdlib.BoundLogger:
    configure_logging()
    return structlog.get_logger(name)
