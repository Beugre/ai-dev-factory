"""Feature request endpoints (thin controllers over FeatureService)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from adf.api.deps import UowDep, get_container
from adf.api.schemas import (
    ActorIn,
    FeatureRequestCreate,
    FeatureRequestOut,
    Page,
    QuestionOut,
    RequestChangesIn,
)
from adf.application.container import Container
from adf.application.services.feature_service import FeatureService
from adf.domain.errors import EntityNotFound
from adf.infrastructure.db.models import FeatureRequest
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/feature-requests", tags=["feature-requests"])


def _service(container: Container = Depends(get_container)) -> FeatureService:
    return FeatureService(container)


@router.post("", response_model=FeatureRequestOut, status_code=201)
async def create_feature(
    payload: FeatureRequestCreate,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: FeatureService = Depends(_service),
) -> FeatureRequest:
    feature = await service.create_feature(
        uow,
        project_id=payload.project_id,
        title=payload.title,
        raw_request=payload.raw_request,
        source=payload.source,
        requester_id=payload.requester_id,
        priority=payload.priority,
    )
    await uow.commit()
    return feature


@router.get("", response_model=Page[FeatureRequestOut])
async def list_features(
    uow: SqlAlchemyUnitOfWork = UowDep,
    project_id: str | None = Query(None),
    state: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[FeatureRequestOut]:
    items = await uow.feature_requests.list(
        project_id=project_id, state=state, limit=limit, offset=offset
    )
    return Page(
        items=[FeatureRequestOut.model_validate(f) for f in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{feature_id}", response_model=FeatureRequestOut)
async def get_feature(feature_id: str, uow: SqlAlchemyUnitOfWork = UowDep) -> FeatureRequest:
    feature = await uow.feature_requests.get(feature_id)
    if feature is None:
        raise EntityNotFound("FeatureRequest", feature_id)
    return feature


@router.post("/{feature_id}/analyze", response_model=FeatureRequestOut)
async def analyze(
    feature_id: str,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: FeatureService = Depends(_service),
) -> FeatureRequest:
    feature = await service.analyze(uow, feature_id)
    await uow.commit()
    return feature


@router.post("/{feature_id}/approve-scope", response_model=FeatureRequestOut)
async def approve_scope(
    feature_id: str,
    payload: ActorIn | None = None,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: FeatureService = Depends(_service),
) -> FeatureRequest:
    actor = (payload or ActorIn()).actor_id
    feature = await service.approve_scope(uow, feature_id, actor_id=actor)
    await uow.commit()
    return feature


@router.post("/{feature_id}/request-changes", response_model=FeatureRequestOut)
async def request_changes(
    feature_id: str,
    payload: RequestChangesIn,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: FeatureService = Depends(_service),
) -> FeatureRequest:
    feature = await service.request_changes(uow, feature_id, payload.comment)
    await uow.commit()
    return feature


@router.post("/{feature_id}/cancel", response_model=FeatureRequestOut)
async def cancel(
    feature_id: str,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: FeatureService = Depends(_service),
) -> FeatureRequest:
    feature = await service.cancel(uow, feature_id)
    await uow.commit()
    return feature


@router.get("/{feature_id}/questions", response_model=list[QuestionOut])
async def list_questions(
    feature_id: str, uow: SqlAlchemyUnitOfWork = UowDep
) -> list[QuestionOut]:
    questions = await uow.questions.list(feature_request_id=feature_id, limit=200)
    return [QuestionOut.model_validate(q) for q in questions]
