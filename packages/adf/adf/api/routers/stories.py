"""Story endpoints (list/get/dispatch/pause/resume)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from adf.api.deps import UowDep, get_container
from adf.api.schemas import DispatchOut, Page, StoryOut
from adf.application.container import Container
from adf.application.services.dispatch_service import StoryDispatchService
from adf.domain.errors import EntityNotFound
from adf.infrastructure.db.models import Story
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/stories", tags=["stories"])


def _service(container: Container = Depends(get_container)) -> StoryDispatchService:
    return StoryDispatchService(container)


@router.get("", response_model=Page[StoryOut])
async def list_stories(
    uow: SqlAlchemyUnitOfWork = UowDep,
    epic_id: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assigned_agent: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[StoryOut]:
    items = await uow.stories.list(
        epic_id=epic_id,
        status=status,
        priority=priority,
        assigned_agent=assigned_agent,
        limit=limit,
        offset=offset,
    )
    return Page(
        items=[StoryOut.model_validate(s) for s in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{story_id}", response_model=StoryOut)
async def get_story(story_id: str, uow: SqlAlchemyUnitOfWork = UowDep) -> Story:
    story = await uow.stories.get(story_id)
    if story is None:
        raise EntityNotFound("Story", story_id)
    return story


@router.post("/{story_id}/dispatch", response_model=DispatchOut)
async def dispatch_story(
    story_id: str,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: StoryDispatchService = Depends(_service),
) -> DispatchOut:
    result = await service.dispatch(uow, story_id)
    await uow.commit()
    return DispatchOut(mode=result.mode, confirmed=result.confirmed, detail=result.detail)


@router.post("/{story_id}/pause", response_model=StoryOut)
async def pause_story(
    story_id: str,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: StoryDispatchService = Depends(_service),
) -> Story:
    story = await service.pause(uow, story_id)
    await uow.commit()
    return story


@router.post("/{story_id}/resume", response_model=StoryOut)
async def resume_story(
    story_id: str,
    uow: SqlAlchemyUnitOfWork = UowDep,
    service: StoryDispatchService = Depends(_service),
) -> Story:
    story = await service.resume(uow, story_id)
    await uow.commit()
    return story
