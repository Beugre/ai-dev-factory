"""Pull request use-cases: change requests, CI gate, staging deploy."""

from __future__ import annotations

import pytest
from adf.adapters.github.mock import MockGitHubGateway
from adf.application.container import build_mock_container
from adf.application.services.pull_request_service import PullRequestService
from adf.domain.enums import (
    CIState,
    EpicStatus,
    PullRequestState,
    ReviewState,
    StoryStatus,
)
from adf.domain.errors import CIFailure
from adf.infrastructure.db.models import Epic, FeatureRequest, Project, PullRequest, Story
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.usefixtures("schema")


async def _seed_pr(ci_state: CIState) -> tuple[str, str]:
    async with SqlAlchemyUnitOfWork() as uow:
        project = await uow.projects.add(
            Project(name="D", slug="demo-app", github_owner="acme", github_repo="demo-repo")
        )
        feature = await uow.feature_requests.add(
            FeatureRequest(project_id=project.id, title="F", raw_request="r")
        )
        epic = await uow.epics.add(
            Epic(feature_request_id=feature.id, title="E", status=EpicStatus.APPROVED)
        )
        story = await uow.stories.add(
            Story(epic_id=epic.id, title="S", status=StoryStatus.IN_REVIEW)
        )
        pr = await uow.pull_requests.add(
            PullRequest(
                story_id=story.id,
                repository="demo-repo",
                number=1,
                title="feat",
                branch="feature/x",
                state=PullRequestState.OPEN,
                ci_state=ci_state,
                review_state=ReviewState.APPROVED,
            )
        )
        await uow.commit()
        return pr.id, story.id


async def test_request_changes_posts_comment_and_updates_story() -> None:
    pr_id, story_id = await _seed_pr(CIState.SUCCESS)
    container = build_mock_container()
    service = PullRequestService(container)
    async with SqlAlchemyUnitOfWork() as uow:
        await service.request_changes(uow, pr_id, "Ajouter un message de confirmation.")
        await uow.commit()

    gateway = container.github
    assert isinstance(gateway, MockGitHubGateway)
    assert gateway.comments[1]  # a comment was posted on PR #1
    async with SqlAlchemyUnitOfWork() as uow:
        story = await uow.stories.get(story_id)
        assert story is not None
        assert story.status == StoryStatus.CHANGES_REQUESTED


async def test_ci_failure_blocks_staging() -> None:
    pr_id, _ = await _seed_pr(CIState.FAILURE)
    service = PullRequestService(build_mock_container())
    async with SqlAlchemyUnitOfWork() as uow:
        with pytest.raises(CIFailure):
            await service.approve_staging(uow, pr_id)


async def test_staging_deploy_succeeds_when_ci_green() -> None:
    pr_id, _ = await _seed_pr(CIState.SUCCESS)
    service = PullRequestService(build_mock_container())
    async with SqlAlchemyUnitOfWork() as uow:
        deployment = await service.approve_staging(uow, pr_id)
        await uow.commit()
    assert deployment.url is not None
