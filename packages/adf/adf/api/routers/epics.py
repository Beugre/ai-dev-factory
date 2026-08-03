"""Epic endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from adf.api.deps import UowDep
from adf.api.schemas import EpicOut, StoryOut
from adf.domain.errors import EntityNotFound
from adf.infrastructure.db.models import Epic
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/epics", tags=["epics"])


@router.get("/{epic_id}", response_model=EpicOut)
async def get_epic(epic_id: str, uow: SqlAlchemyUnitOfWork = UowDep) -> Epic:
    epic = await uow.epics.get(epic_id)
    if epic is None:
        raise EntityNotFound("Epic", epic_id)
    return epic


@router.get("/{epic_id}/stories", response_model=list[StoryOut])
async def list_epic_stories(
    epic_id: str, uow: SqlAlchemyUnitOfWork = UowDep
) -> list[StoryOut]:
    stories = await uow.stories.list(epic_id=epic_id, limit=200)
    return [StoryOut.model_validate(s) for s in stories]
