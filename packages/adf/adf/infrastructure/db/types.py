"""Reusable SQLAlchemy type storing a ``StrEnum`` as text and loading it back."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import String
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class StrEnumType[E: StrEnum](TypeDecorator[E]):
    """Persist a :class:`StrEnum` value as a VARCHAR, reload it as the enum.

    Using this avoids the pitfall where a plain ``String`` column returns raw
    strings, breaking ``.value`` access and identity comparisons.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_cls: type[E], length: int = 40) -> None:
        self._enum_cls = enum_cls
        super().__init__(length=length)

    def process_bind_param(self, value: E | str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, StrEnum):
            return value.value
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> E | None:
        if value is None:
            return None
        return self._enum_cls(value)
