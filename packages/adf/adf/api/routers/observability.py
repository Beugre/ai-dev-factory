"""Read-only endpoints for agent runs, deployments and audit logs."""

from __future__ import annotations

from fastapi import APIRouter, Query

from adf.api.deps import UowDep
from adf.api.schemas import AgentRunOut, AuditLogOut, DeploymentOut, Page
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(tags=["observability"])


@router.get("/agent-runs", response_model=Page[AgentRunOut])
async def list_agent_runs(
    uow: SqlAlchemyUnitOfWork = UowDep,
    story_id: str | None = Query(None),
    feature_request_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[AgentRunOut]:
    items = await uow.agent_runs.list(
        story_id=story_id,
        feature_request_id=feature_request_id,
        limit=limit,
        offset=offset,
    )
    return Page(
        items=[AgentRunOut.model_validate(a) for a in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/deployments", response_model=Page[DeploymentOut])
async def list_deployments(
    uow: SqlAlchemyUnitOfWork = UowDep,
    environment: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[DeploymentOut]:
    items = await uow.deployments.list(environment=environment, limit=limit, offset=offset)
    return Page(
        items=[DeploymentOut.model_validate(d) for d in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/audit-logs", response_model=Page[AuditLogOut])
async def list_audit_logs(
    uow: SqlAlchemyUnitOfWork = UowDep,
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[AuditLogOut]:
    items = await uow.audit_logs.list(
        entity_type=entity_type, entity_id=entity_id, limit=limit, offset=offset
    )
    return Page(
        items=[AuditLogOut.model_validate(a) for a in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )
