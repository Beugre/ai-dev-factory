"""Audit helper: every agentic/sensitive action is recorded."""

from __future__ import annotations

from adf.domain.enums import ActorType
from adf.infrastructure.db.models import AuditLog
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork


async def record_audit(
    uow: SqlAlchemyUnitOfWork,
    *,
    actor_type: ActorType,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, object] | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_type=actor_type.value,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=metadata or {},
    )
    return await uow.audit_logs.add(entry)
