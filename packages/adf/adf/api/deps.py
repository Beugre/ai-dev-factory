"""API dependencies: settings, container, unit-of-work, correlation id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends, Header

from adf.application.container import Container, build_container
from adf.config import Settings, get_settings
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import set_correlation_id


@lru_cache
def get_container() -> Container:
    return build_container()


def settings_dep() -> Settings:
    return get_settings()


async def get_uow() -> AsyncIterator[SqlAlchemyUnitOfWork]:
    """Provide a per-request Unit of Work.

    Controllers call ``await uow.commit()`` explicitly for write operations.
    """
    async with SqlAlchemyUnitOfWork() as uow:
        yield uow


async def correlation_id_dep(
    x_correlation_id: str | None = Header(default=None),
) -> str | None:
    set_correlation_id(x_correlation_id)
    return x_correlation_id


ContainerDep = Depends(get_container)
UowDep = Depends(get_uow)
