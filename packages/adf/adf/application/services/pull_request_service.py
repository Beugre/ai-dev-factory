"""Pull request use-cases: request changes, approve staging (gated)."""

from __future__ import annotations

from datetime import UTC, datetime

from adf.application.audit import record_audit
from adf.application.container import Container
from adf.domain.enums import (
    ActorType,
    CIState,
    DeploymentEnvironment,
    DeploymentStatus,
    StoryStatus,
)
from adf.domain.errors import CIFailure, EntityNotFound
from adf.domain.state_machine import assert_story_transition
from adf.infrastructure.db.models import Deployment, PullRequest, Story
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger
from adf.ports.deployment_gateway import DeploymentRequest

logger = get_logger(__name__)


class PullRequestService:
    def __init__(self, container: Container) -> None:
        self._c = container

    async def request_changes(
        self,
        uow: SqlAlchemyUnitOfWork,
        pr_id: str,
        comment: str,
        *,
        actor_id: str = "owner",
    ) -> PullRequest:
        pr = await self._get_pr(uow, pr_id)
        # Untrusted user comment is posted verbatim as data, never executed.
        await self._c.github.comment_on_pull_request(
            pr.repository, pr.number, f"Demande de modification:\n\n{comment}"
        )
        if pr.story_id:
            story = await uow.stories.get(pr.story_id)
            if story is not None:
                story.status = assert_story_transition(
                    story.status, StoryStatus.CHANGES_REQUESTED
                )
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="pr.changes_requested",
            entity_type="PullRequest",
            entity_id=pr.id,
            metadata={"comment": comment[:500]},
        )
        return pr

    async def approve_staging(
        self, uow: SqlAlchemyUnitOfWork, pr_id: str, *, actor_id: str = "owner"
    ) -> Deployment:
        pr = await self._get_pr(uow, pr_id)
        # Gate: a failing CI can never be bypassed.
        if pr.ci_state == CIState.FAILURE:
            raise CIFailure(f"CI en échec sur la PR #{pr.number}, staging bloqué")

        story: Story | None = None
        if pr.story_id:
            story = await uow.stories.get(pr.story_id)
            if story is not None:
                story.status = assert_story_transition(story.status, StoryStatus.STAGING)

        project_slug = await self._project_slug(uow, pr)
        result = await self._c.deployment.deploy(
            DeploymentRequest(
                environment=DeploymentEnvironment.STAGING,
                version=pr.branch,
                ref=pr.branch,
                project_slug=project_slug,
            )
        )
        deployment = Deployment(
            project_id=await self._project_id(uow, pr),
            pull_request_id=pr.id,
            environment=DeploymentEnvironment.STAGING,
            version=pr.branch,
            status=(
                DeploymentStatus.SUCCEEDED
                if result.status == "succeeded"
                else DeploymentStatus.IN_PROGRESS
            ),
            url=result.url,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) if result.status == "succeeded" else None,
        )
        await uow.deployments.add(deployment)
        pr.preview_url = result.url
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="staging.approved",
            entity_type="PullRequest",
            entity_id=pr.id,
            metadata={"url": result.url or ""},
        )
        return deployment

    async def _get_pr(self, uow: SqlAlchemyUnitOfWork, pr_id: str) -> PullRequest:
        pr = await uow.pull_requests.get(pr_id)
        if pr is None:
            raise EntityNotFound("PullRequest", pr_id)
        return pr

    async def _project_id(self, uow: SqlAlchemyUnitOfWork, pr: PullRequest) -> str:
        if pr.story_id:
            story = await uow.stories.get(pr.story_id)
            if story is not None:
                epic = await uow.epics.get(story.epic_id)
                if epic is not None:
                    feature = await uow.feature_requests.get(epic.feature_request_id)
                    if feature is not None:
                        return feature.project_id
        projects = await uow.projects.list(limit=1)
        return projects[0].id if projects else ""

    async def _project_slug(self, uow: SqlAlchemyUnitOfWork, pr: PullRequest) -> str:
        project_id = await self._project_id(uow, pr)
        project = await uow.projects.get(project_id) if project_id else None
        return project.slug if project else "demo"
