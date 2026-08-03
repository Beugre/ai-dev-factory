"""Pull request endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from adf.api.deps import UowDep, get_container
from adf.api.schemas import DeploymentOut, Page, PullRequestOut, RequestChangesIn
from adf.application.container import Container
from adf.application.services.pull_request_service import PullRequestService
from adf.domain.errors import EntityNotFound
from adf.infrastructure.db.models import PullRequest
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


def _service(container: Container = Depends(get_container)) -> PullRequestService:
    return PullRequestService(container)


@router.get("", response_model=Page[PullRequestOut])
async def list_pull_requests(
    uow: SqlAlchemyUnitOfWork = UowDep,
    state: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[PullRequestOut]:
    items = await uow.pull_requests.list(state=state, limit=limit, offset=offset)
    return Page(
        items=[PullRequestOut.model_validate(p) for p in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{pr_id}", response_model=PullRequestOut)
async def get_pull_request(pr_id: str, uow: SqlAlchemyUnitOfWork = UowDep) -> PullRequest:
    pr = await uow.pull_requests.get(pr_id)
    if pr is None:
        raise EntityNotFound("PullRequest", pr_id)
    return pr


@router.post("/{pr_id}/request-changes", response_model=PullRequestOut)
async def request_changes(
    pr_id: str,
    payload: RequestChangesIn,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: PullRequestService = Depends(_service),
) -> PullRequest:
    pr = await service.request_changes(uow, pr_id, payload.comment)
    await uow.commit()
    return pr


@router.post("/{pr_id}/approve-staging", response_model=DeploymentOut)
async def approve_staging(
    pr_id: str,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: PullRequestService = Depends(_service),
) -> DeploymentOut:
    deployment = await service.approve_staging(uow, pr_id)
    await uow.commit()
    return DeploymentOut.model_validate(deployment)
