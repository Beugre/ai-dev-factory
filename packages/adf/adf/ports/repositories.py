"""Repository and Unit-of-Work ports.

The application layer depends on these abstractions, not on SQLAlchemy. The
concrete implementation lives in :mod:`adf.infrastructure.db`.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    async def add(self, entity: T) -> T: ...
    async def get(self, entity_id: str) -> T | None: ...
    async def list(self, **filters: object) -> list[T]: ...


class UnitOfWork(Protocol):
    """Transactional boundary exposing typed repositories.

    Attribute types are declared in the concrete implementation to avoid a
    domain -> infrastructure import cycle; here we only require the async
    context-manager + commit/rollback surface.
    """

    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(self, *exc: object) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
