"""Story dispatch use-cases: dispatch to Copilot, pause, resume."""

from __future__ import annotations

from adf.application.audit import record_audit
from adf.application.container import Container
from adf.domain.enums import ActorType, StoryStatus
from adf.domain.errors import EntityNotFound
from adf.domain.state_machine import assert_story_transition
from adf.infrastructure.db.models import Story
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger
from adf.ports.github_gateway import DispatchResult, IssueRef

logger = get_logger(__name__)


class StoryDispatchService:
    def __init__(self, container: Container) -> None:
        self._c = container

    async def dispatch(
        self, uow: SqlAlchemyUnitOfWork, story_id: str, *, actor_id: str = "owner"
    ) -> DispatchResult:
        story = await self._get_story(uow, story_id)
        if story.github_issue_number is None:
            raise EntityNotFound("Story.github_issue", story_id)

        story.status = assert_story_transition(story.status, StoryStatus.DISPATCHED)
        story.assigned_agent = self._c.settings.copilot_custom_agent

        result = await self._c.dispatcher.dispatch(
            self._c.settings.github_target_repo,
            IssueRef(number=story.github_issue_number, url=story.github_issue_url or ""),
            base_branch=self._c.settings.github_default_branch,
            instructions=f"Implement story: {story.title}",
            custom_agent=self._c.settings.copilot_custom_agent,
            model=self._c.settings.copilot_model,
        )

        # Never claim success unless the dispatcher confirmed it.
        if not result.confirmed:
            logger.info(
                "dispatch_not_confirmed", story=story.id, mode=result.mode, detail=result.detail
            )

        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="story.dispatched",
            entity_type="Story",
            entity_id=story.id,
            metadata={"mode": result.mode, "confirmed": result.confirmed},
        )
        return result

    async def pause(
        self, uow: SqlAlchemyUnitOfWork, story_id: str, *, actor_id: str = "owner"
    ) -> Story:
        story = await self._get_story(uow, story_id)
        story.status = assert_story_transition(story.status, StoryStatus.PAUSED)
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="story.paused",
            entity_type="Story",
            entity_id=story.id,
        )
        return story

    async def resume(
        self, uow: SqlAlchemyUnitOfWork, story_id: str, *, actor_id: str = "owner"
    ) -> Story:
        story = await self._get_story(uow, story_id)
        story.status = assert_story_transition(story.status, StoryStatus.DISPATCHED)
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="story.resumed",
            entity_type="Story",
            entity_id=story.id,
        )
        return story

    async def _get_story(self, uow: SqlAlchemyUnitOfWork, story_id: str) -> Story:
        story = await uow.stories.get(story_id)
        if story is None:
            raise EntityNotFound("Story", story_id)
        return story
