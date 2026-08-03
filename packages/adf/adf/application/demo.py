"""End-to-end demo orchestrator.

Runs the full workflow with mock adapters and NO external account:

    request -> analysis -> questions -> answers -> scope -> approval ->
    issues (mock) -> dispatch (mock) -> PR (mock) -> CI -> review -> QA ->
    staging (mock) -> notification -> change request -> new iteration ->
    acceptance.

Used by ``python -m adf.cli demo`` and by the e2e test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from adf.adapters.github.mock import MockGitHubGateway
from adf.application.container import Container, build_mock_container
from adf.application.services.dispatch_service import StoryDispatchService
from adf.application.services.feature_service import FeatureService
from adf.application.services.pull_request_service import PullRequestService
from adf.domain.contracts import QAContract, ReviewContract
from adf.domain.enums import (
    AgentType,
    CIState,
    FeatureSource,
    FeatureState,
    Priority,
    PullRequestState,
    ReviewState,
    StoryStatus,
)
from adf.infrastructure.db import create_all
from adf.infrastructure.db.models import AgentRun, Project, PullRequest, Story
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.ports.agent_runtime import AgentRequest

DEMO_REQUEST = (
    "En tant qu'utilisateur, je veux pouvoir demander la réinitialisation de mon "
    "mot de passe afin de récupérer l'accès à mon compte."
)


@dataclass
class DemoReport:
    steps: list[str] = field(default_factory=list)
    feature_id: str = ""
    final_feature_state: str = ""
    story_states: list[str] = field(default_factory=list)
    issues_created: int = 0
    dispatch_confirmed: bool = False
    deployment_url: str | None = None
    notifications: int = 0

    def log(self, message: str) -> None:
        self.steps.append(message)


async def run_demo(*, ensure_schema: bool = True) -> DemoReport:
    if ensure_schema:
        await create_all()
    container = build_mock_container()
    github = container.github
    assert isinstance(github, MockGitHubGateway)
    feature_service = FeatureService(container)
    dispatch_service = StoryDispatchService(container)
    pr_service = PullRequestService(container)
    report = DemoReport()

    async with SqlAlchemyUnitOfWork() as uow:
        # 1. Demo project
        project = await uow.projects.add(
            Project(
                name="Demo App",
                slug="demo-app",
                github_owner=container.settings.github_owner,
                github_repo=container.settings.github_target_repo,
                default_branch="main",
                staging_url=container.settings.staging_base_url,
            )
        )
        report.log(f"Projet de démonstration créé: {project.slug}")

        # 2. Feature request
        feature = await feature_service.create_feature(
            uow,
            project_id=project.id,
            title="Réinitialisation du mot de passe",
            raw_request=DEMO_REQUEST,
            source=FeatureSource.WEB,
            requester_id="owner",
            priority=Priority.HIGH,
        )
        report.feature_id = feature.id
        report.log("Demande utilisateur enregistrée.")

        # 3. Product Owner analysis -> blocking questions
        await feature_service.analyze(uow, feature.id)
        questions = await uow.questions.list(feature_request_id=feature.id, limit=50)
        report.log(f"Analyse Product Owner: {len(questions)} question(s) bloquante(s).")
        assert feature.state == FeatureState.NEEDS_CLARIFICATION

        # 4. Answer every question
        answers = {
            "canal": "Email",
            "durée": "1 heure",
            "inconnue": "Répondre de façon neutre (anti-énumération)",
        }
        answer_values = list(answers.values())
        for i, question in enumerate(questions):
            await feature_service.answer_question(
                uow, question.id, answer_values[i % len(answer_values)]
            )
        report.log("Réponses fournies -> nouvelle analyse.")

        await uow.session.refresh(feature)
        assert feature.state == FeatureState.READY_FOR_SCOPE_APPROVAL, feature.state
        report.log("Périmètre prêt pour validation.")

        # 5. Human scope approval -> issues created
        await feature_service.approve_scope(uow, feature.id, actor_id="owner")
        await uow.session.refresh(feature)
        stories = await _all_stories(uow, feature.id)
        report.issues_created = len(github.issues)
        report.log(
            f"Périmètre approuvé -> {len(github.issues)} issue(s) GitHub (mock) créée(s)."
        )
        assert feature.state == FeatureState.READY_FOR_DEVELOPMENT

        # 6. Dispatch first story to Copilot (mock, confirmed)
        first_story = stories[0]
        dispatch = await dispatch_service.dispatch(uow, first_story.id, actor_id="owner")
        report.dispatch_confirmed = dispatch.confirmed
        report.log(
            f"Story affectée à Copilot (mode={dispatch.mode}, "
            f"confirmé={dispatch.confirmed})."
        )

        feature.state = _advance(feature.state, FeatureState.IN_DEVELOPMENT)

        # 7. Simulate a pull request opened by the coding agent
        pr_info = github.open_pull_request(
            title=f"feat: {first_story.title}",
            branch=f"story/{first_story.id[:8]}",
            story_number=first_story.github_issue_number or 0,
            ci_state="success",
            preview_url=f"{container.settings.staging_base_url}/pr/1",
        )
        pr = await uow.pull_requests.add(
            PullRequest(
                story_id=first_story.id,
                repository=container.settings.github_target_repo,
                number=pr_info.number,
                title=pr_info.title,
                branch=pr_info.branch,
                state=PullRequestState.OPEN,
                ci_state=CIState.SUCCESS,
                review_state=ReviewState.PENDING,
                preview_url=pr_info.preview_url,
                mergeable=True,
            )
        )
        first_story.status = _advance_story(first_story.status, StoryStatus.IN_PROGRESS)
        first_story.pull_request_number = pr.number
        first_story.pull_request_url = pr_info.url
        report.log(f"Pull request #{pr.number} ouverte, CI verte.")

        # 8. Review + QA agents
        review = await _run_review(container, uow, project.id, first_story.id, "success")
        qa = await _run_qa(container, uow, project.id, first_story.id, "success")
        pr.review_state = (
            ReviewState.APPROVED if review.verdict == "approved" else ReviewState.CHANGES_REQUESTED
        )
        first_story.status = _advance_story(first_story.status, StoryStatus.IN_REVIEW)
        feature.state = _advance(feature.state, FeatureState.IN_REVIEW)
        report.log(f"Revue: {review.verdict} | QA: {qa.verdict}.")

        # 9. Approve staging (gated on CI) -> deploy mock -> notify
        feature.state = _advance(feature.state, FeatureState.READY_FOR_STAGING)
        deployment = await pr_service.approve_staging(uow, pr.id, actor_id="owner")
        report.deployment_url = deployment.url
        feature.state = _advance(feature.state, FeatureState.STAGING_DEPLOYED)
        feature.state = _advance(feature.state, FeatureState.READY_FOR_ACCEPTANCE)
        report.log(f"Staging déployé (mock): {deployment.url}")

        # 10. Owner requests a change -> comment on PR -> new iteration
        await pr_service.request_changes(
            uow, pr.id, "Merci d'ajouter un message de confirmation.", actor_id="owner"
        )
        feature.state = _advance(feature.state, FeatureState.CHANGES_REQUESTED)
        feature.state = _advance(feature.state, FeatureState.IN_DEVELOPMENT)
        await uow.session.refresh(first_story)
        first_story.status = _advance_story(first_story.status, StoryStatus.IN_PROGRESS)
        report.log("Demande de modification -> commentaire posté sur la PR.")

        # 11. New version -> review passes -> acceptance
        first_story.status = _advance_story(first_story.status, StoryStatus.IN_REVIEW)
        feature.state = _advance(feature.state, FeatureState.IN_REVIEW)
        feature.state = _advance(feature.state, FeatureState.READY_FOR_STAGING)
        feature.state = _advance(feature.state, FeatureState.STAGING_DEPLOYED)
        feature.state = _advance(feature.state, FeatureState.READY_FOR_ACCEPTANCE)
        first_story.status = _advance_story(first_story.status, StoryStatus.STAGING)
        first_story.status = _advance_story(first_story.status, StoryStatus.ACCEPTED)
        first_story.status = _advance_story(first_story.status, StoryStatus.DONE)
        feature.state = _advance(feature.state, FeatureState.ACCEPTED)
        feature.state = _advance(feature.state, FeatureState.DONE)
        report.log("Validation finale: feature acceptée et terminée.")

        report.final_feature_state = feature.state.value
        all_stories = await _all_stories(uow, feature.id)
        report.story_states = [s.status.value for s in all_stories]
        notifications = getattr(container.notifications, "sent", [])
        report.notifications = len(notifications)

        await uow.commit()

    return report


def _advance(current: FeatureState, target: FeatureState) -> FeatureState:
    from adf.domain.state_machine import assert_feature_transition

    return assert_feature_transition(current, target)


def _advance_story(current: StoryStatus, target: StoryStatus) -> StoryStatus:
    from adf.domain.state_machine import assert_story_transition

    return assert_story_transition(current, target)


async def _all_stories(uow: SqlAlchemyUnitOfWork, feature_id: str) -> list[Story]:
    epics = await uow.epics.list(feature_request_id=feature_id, limit=10)
    stories: list[Story] = []
    for epic in epics:
        stories.extend(await uow.stories.list(epic_id=epic.id, limit=50))
    return stories


async def _run_review(
    container: Container,
    uow: SqlAlchemyUnitOfWork,
    project_id: str,
    story_id: str,
    ci: str,
) -> ReviewContract:
    run = AgentRun(
        project_id=project_id,
        story_id=story_id,
        agent_type=AgentType.REVIEWER,
        provider=container.agent_runtime.provider,
        started_at=datetime.now(UTC),
    )
    review, result = await container.agent_runtime.run(
        AgentRequest(
            role=AgentType.REVIEWER,
            instructions="Review the pull request.",
            context={"ci_state": ci, "story_id": story_id},
            correlation_id=story_id,
        ),
        ReviewContract,
    )
    run.output_summary = result.output_summary
    run.completed_at = datetime.now(UTC)
    await uow.agent_runs.add(run)
    return review


async def _run_qa(
    container: Container,
    uow: SqlAlchemyUnitOfWork,
    project_id: str,
    story_id: str,
    ci: str,
) -> QAContract:
    run = AgentRun(
        project_id=project_id,
        story_id=story_id,
        agent_type=AgentType.QA,
        provider=container.agent_runtime.provider,
        started_at=datetime.now(UTC),
    )
    qa, result = await container.agent_runtime.run(
        AgentRequest(
            role=AgentType.QA,
            instructions="Run QA on the pull request.",
            context={"ci_state": ci, "story_id": story_id},
            correlation_id=story_id,
        ),
        QAContract,
    )
    run.output_summary = result.output_summary
    run.completed_at = datetime.now(UTC)
    await uow.agent_runs.add(run)
    return qa
