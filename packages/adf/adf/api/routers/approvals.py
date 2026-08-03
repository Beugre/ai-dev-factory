"""Approval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from adf.api.deps import UowDep
from adf.api.schemas import ApprovalOut, DecisionIn, Page
from adf.application.services.approval_service import ApprovalService
from adf.infrastructure.db.models import Approval
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _service() -> ApprovalService:
    return ApprovalService()


@router.get("", response_model=Page[ApprovalOut])
async def list_approvals(
    uow: SqlAlchemyUnitOfWork = UowDep,
    decision: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[ApprovalOut]:
    items = await uow.approvals.list(decision=decision, limit=limit, offset=offset)
    return Page(
        items=[ApprovalOut.model_validate(a) for a in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(
    approval_id: str,
    payload: DecisionIn | None = None,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: ApprovalService = Depends(_service),
) -> Approval:
    body = payload or DecisionIn()
    approval = await service.approve(
        uow, approval_id, actor_id=body.actor_id, comment=body.comment
    )
    await uow.commit()
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(
    approval_id: str,
    payload: DecisionIn | None = None,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: ApprovalService = Depends(_service),
) -> Approval:
    body = payload or DecisionIn()
    approval = await service.reject(
        uow, approval_id, actor_id=body.actor_id, comment=body.comment
    )
    await uow.commit()
    return approval
