"""Clarification question answering endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from adf.api.deps import UowDep, get_container
from adf.api.schemas import AnswerIn, FeatureRequestOut
from adf.application.container import Container
from adf.application.services.feature_service import FeatureService
from adf.infrastructure.db.models import FeatureRequest
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/questions", tags=["questions"])


def _service(container: Container = Depends(get_container)) -> FeatureService:
    return FeatureService(container)


@router.post("/{question_id}/answer", response_model=FeatureRequestOut)
async def answer_question(
    question_id: str,
    payload: AnswerIn,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: FeatureService = Depends(_service),
) -> FeatureRequest:
    feature = await service.answer_question(
        uow, question_id, payload.answer, actor_id=payload.actor_id
    )
    await uow.commit()
    return feature
