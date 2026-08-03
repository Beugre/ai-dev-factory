"""Feature request use-cases: create, analyse, clarify, approve, dispatch."""

from __future__ import annotations

from datetime import UTC, datetime

from adf.application.audit import record_audit
from adf.application.container import Container
from adf.application.rendering import render_gherkin, render_story_issue_body
from adf.agent_runtime.prompt_loader import load_prompt
from adf.domain.contracts import ProductOwnerAnalysis
from adf.domain.enums import (
    ActorType,
    AgentRunState,
    AgentType,
    ApprovalDecision,
    ApprovalType,
    EpicStatus,
    FeatureSource,
    FeatureState,
    Priority,
    QuestionState,
    StoryStatus,
)
from adf.domain.errors import (
    BlockingQuestionsUnanswered,
    EntityNotFound,
)
from adf.domain.state_machine import assert_feature_transition
from adf.infrastructure.db.models import (
    AgentRun,
    Approval,
    ClarificationQuestion,
    Epic,
    FeatureRequest,
    Story,
)
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger
from adf.ports.agent_runtime import AgentRequest
from adf.ports.notification_gateway import NotificationButton, NotificationMessage

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


class FeatureService:
    def __init__(self, container: Container) -> None:
        self._c = container

    # --- creation --------------------------------------------------------
    async def create_feature(
        self,
        uow: SqlAlchemyUnitOfWork,
        *,
        project_id: str,
        title: str,
        raw_request: str,
        source: FeatureSource = FeatureSource.API,
        requester_id: str | None = None,
        priority: Priority = Priority.MEDIUM,
    ) -> FeatureRequest:
        project = await uow.projects.get(project_id)
        if project is None:
            raise EntityNotFound("Project", project_id)
        feature = FeatureRequest(
            project_id=project_id,
            title=title,
            raw_request=raw_request,
            source=source,
            requester_id=requester_id,
            priority=priority,
            state=FeatureState.DRAFT,
        )
        await uow.feature_requests.add(feature)
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=requester_id or "anonymous",
            action="feature.created",
            entity_type="FeatureRequest",
            entity_id=feature.id,
            metadata={"title": title, "source": source.value},
        )
        return feature

    # --- analysis --------------------------------------------------------
    async def analyze(
        self, uow: SqlAlchemyUnitOfWork, feature_id: str
    ) -> FeatureRequest:
        feature = await self._get_feature(uow, feature_id)
        answered = await self._answered_map(uow, feature_id)
        feature.state = assert_feature_transition(feature.state, FeatureState.ANALYZING)

        run = AgentRun(
            project_id=feature.project_id,
            feature_request_id=feature.id,
            agent_type=AgentType.PRODUCT_OWNER,
            provider=self._c.agent_runtime.provider,
            state=AgentRunState.RUNNING,
            started_at=_now(),
            input_summary=feature.raw_request[:500],
        )
        await uow.agent_runs.add(run)

        request = AgentRequest(
            role=AgentType.PRODUCT_OWNER,
            instructions=load_prompt("product-owner-analysis"),
            context={
                "raw_request": feature.raw_request,
                "project": feature.project_id,
                "answers": answered,
                "answers_complete": bool(answered),
            },
            correlation_id=feature.id,
        )
        try:
            analysis, result = await self._c.agent_runtime.run(request, ProductOwnerAnalysis)
        except Exception as exc:
            run.state = AgentRunState.FAILED
            run.completed_at = _now()
            run.error = f"{type(exc).__name__}: {exc}"
            logger.error("po_analysis_failed", feature=feature.id, error=run.error)
            raise

        run.state = AgentRunState.SUCCEEDED
        run.completed_at = _now()
        run.output_summary = result.output_summary
        run.model = result.model
        run.tokens_input = result.tokens_input
        run.tokens_output = result.tokens_output
        run.correlation_id = feature.id

        feature.normalized_request = analysis.normalized_request
        await self._persist_analysis(uow, feature, analysis)

        if analysis.has_blocking_questions:
            feature.state = assert_feature_transition(
                feature.state, FeatureState.NEEDS_CLARIFICATION
            )
            await self._notify_questions(feature, analysis)
        else:
            feature.state = assert_feature_transition(
                feature.state, FeatureState.READY_FOR_SCOPE_APPROVAL
            )
            await self._create_scope_approval(uow, feature)
            await self._notify_scope(uow, feature, analysis)

        await record_audit(
            uow,
            actor_type=ActorType.AGENT,
            actor_id=AgentType.PRODUCT_OWNER.value,
            action="feature.analyzed",
            entity_type="FeatureRequest",
            entity_id=feature.id,
            metadata={"questions": len(analysis.questions), "stories": len(analysis.stories)},
        )
        return feature

    async def _persist_analysis(
        self,
        uow: SqlAlchemyUnitOfWork,
        feature: FeatureRequest,
        analysis: ProductOwnerAnalysis,
    ) -> None:
        # Persist questions (only new blocking ones when re-analysing).
        existing = await uow.questions.list(feature_request_id=feature.id, limit=200)
        existing_texts = {q.question for q in existing}
        for q in analysis.questions:
            if q.question in existing_texts:
                continue
            await uow.questions.add(
                ClarificationQuestion(
                    feature_request_id=feature.id,
                    question=q.question,
                    answer_type=q.answer_type,
                    options=list(q.options),
                    blocking=q.blocking,
                    state=QuestionState.PENDING,
                    asked_at=_now(),
                )
            )

        if not analysis.stories:
            return

        # Replace any previous draft epic/stories with the fresh scope.
        epic = Epic(
            feature_request_id=feature.id,
            title=analysis.epic.title,
            description=analysis.epic.description,
            business_value=analysis.epic.business_value,
            status=EpicStatus.DRAFT,
        )
        await uow.epics.add(epic)
        for story in analysis.stories:
            await uow.stories.add(
                Story(
                    epic_id=epic.id,
                    title=story.title,
                    description=story.description,
                    acceptance_criteria=list(story.acceptance_criteria),
                    gherkin=render_gherkin(story.gherkin),
                    priority=story.priority,
                    estimated_complexity=story.estimated_complexity,
                    dependencies=list(story.dependencies),
                    status=StoryStatus.DRAFT,
                )
            )

    # --- clarification ---------------------------------------------------
    async def answer_question(
        self,
        uow: SqlAlchemyUnitOfWork,
        question_id: str,
        answer: str,
        *,
        actor_id: str = "owner",
    ) -> FeatureRequest:
        question = await uow.questions.get(question_id)
        if question is None:
            raise EntityNotFound("ClarificationQuestion", question_id)
        question.answer = answer
        question.state = QuestionState.ANSWERED
        question.answered_at = _now()
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="question.answered",
            entity_type="ClarificationQuestion",
            entity_id=question.id,
            metadata={"answer": answer[:200]},
        )
        feature = await self._get_feature(uow, question.feature_request_id)
        pending = await self._pending_blocking(uow, feature.id)
        if not pending:
            # All blocking questions answered -> re-analyse (NEEDS_CLARIFICATION
            # -> ANALYZING handled inside analyze()).
            return await self.analyze(uow, feature.id)
        return feature

    # --- scope approval --------------------------------------------------
    async def approve_scope(
        self,
        uow: SqlAlchemyUnitOfWork,
        feature_id: str,
        *,
        actor_id: str = "owner",
    ) -> FeatureRequest:
        feature = await self._get_feature(uow, feature_id)
        pending = await self._pending_blocking(uow, feature_id)
        if pending:
            raise BlockingQuestionsUnanswered(
                f"{len(pending)} question(s) bloquante(s) en attente"
            )
        feature.state = assert_feature_transition(feature.state, FeatureState.SCOPE_APPROVED)
        await self._decide_scope_approval(uow, feature_id, ApprovalDecision.APPROVED, actor_id)
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="scope.approved",
            entity_type="FeatureRequest",
            entity_id=feature.id,
        )
        return await self._create_issues(uow, feature)

    async def request_changes(
        self,
        uow: SqlAlchemyUnitOfWork,
        feature_id: str,
        comment: str,
        *,
        actor_id: str = "owner",
    ) -> FeatureRequest:
        feature = await self._get_feature(uow, feature_id)
        feature.state = assert_feature_transition(
            feature.state, FeatureState.CHANGES_REQUESTED
        )
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="feature.changes_requested",
            entity_type="FeatureRequest",
            entity_id=feature.id,
            metadata={"comment": comment[:500]},
        )
        return feature

    async def cancel(
        self, uow: SqlAlchemyUnitOfWork, feature_id: str, *, actor_id: str = "owner"
    ) -> FeatureRequest:
        feature = await self._get_feature(uow, feature_id)
        feature.state = assert_feature_transition(feature.state, FeatureState.CANCELLED)
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="feature.cancelled",
            entity_type="FeatureRequest",
            entity_id=feature.id,
        )
        return feature

    # --- issue creation --------------------------------------------------
    async def _create_issues(
        self, uow: SqlAlchemyUnitOfWork, feature: FeatureRequest
    ) -> FeatureRequest:
        feature.state = assert_feature_transition(feature.state, FeatureState.CREATING_ISSUES)
        repo = self._c.settings.github_target_repo
        epics = await uow.epics.list(feature_request_id=feature.id, limit=10)
        if not epics:
            feature.state = assert_feature_transition(feature.state, FeatureState.BLOCKED)
            return feature
        epic = epics[0]
        epic_issue = await self._c.github.create_issue(
            repo,
            f"[EPIC] {epic.title}",
            f"{epic.description}\n\n**Valeur métier:** {epic.business_value}",
            labels=["type:epic", "status:ready"],
        )
        epic.github_issue_number = epic_issue.number
        epic.status = EpicStatus.APPROVED

        stories = await uow.stories.list(epic_id=epic.id, limit=50)
        for story in stories:
            body = render_story_issue_body(
                _story_contract(story), context=feature.normalized_request or feature.raw_request
            )
            issue = await self._c.github.create_issue(
                repo,
                f"[STORY] {story.title}",
                body,
                labels=["type:story", "status:ready", f"priority:{story.priority.value}"],
            )
            story.github_issue_number = issue.number
            story.github_issue_url = issue.url
            story.status = StoryStatus.READY

        feature.state = assert_feature_transition(
            feature.state, FeatureState.READY_FOR_DEVELOPMENT
        )
        await record_audit(
            uow,
            actor_type=ActorType.SYSTEM,
            actor_id="issue-factory",
            action="issues.created",
            entity_type="FeatureRequest",
            entity_id=feature.id,
            metadata={"epic_issue": epic_issue.number, "stories": len(stories)},
        )
        return feature

    # --- notifications ---------------------------------------------------
    async def _notify_questions(
        self, feature: FeatureRequest, analysis: ProductOwnerAnalysis
    ) -> None:
        body = "\n".join(f"• {q.question}" for q in analysis.questions if q.blocking)
        await self._c.notifications.send(
            NotificationMessage(
                channel=self._c.notifications.channel,
                recipient=feature.requester_id or "owner",
                type="clarification.needed",
                title=f"Questions sur: {feature.title}",
                body=body,
                buttons=[NotificationButton("Répondre", "answer", feature.id)],
                metadata={"feature_id": feature.id},
            )
        )

    async def _notify_scope(
        self,
        uow: SqlAlchemyUnitOfWork,
        feature: FeatureRequest,
        analysis: ProductOwnerAnalysis,
    ) -> None:
        story_lines = "\n".join(f"• {s.title}" for s in analysis.stories)
        body = (
            f"**Epic:** {analysis.epic.title}\n\n"
            f"**Stories:**\n{story_lines}\n\n"
            f"**Risques:** {', '.join(analysis.risks) or 'aucun'}"
        )
        await self._c.notifications.send(
            NotificationMessage(
                channel=self._c.notifications.channel,
                recipient=feature.requester_id or "owner",
                type="scope.review",
                title=f"Périmètre prêt: {feature.title}",
                body=body,
                buttons=[
                    NotificationButton("Approuver", "approve_scope", feature.id),
                    NotificationButton("Demander une modification", "request_changes", feature.id),
                    NotificationButton("Annuler", "cancel", feature.id, style="danger"),
                ],
                metadata={"feature_id": feature.id},
            )
        )

    # --- approvals -------------------------------------------------------
    async def _create_scope_approval(
        self, uow: SqlAlchemyUnitOfWork, feature: FeatureRequest
    ) -> None:
        await uow.approvals.add(
            Approval(
                project_id=feature.project_id,
                entity_type="FeatureRequest",
                entity_id=feature.id,
                approval_type=ApprovalType.SCOPE,
                decision=ApprovalDecision.PENDING,
                requested_at=_now(),
            )
        )

    async def _decide_scope_approval(
        self,
        uow: SqlAlchemyUnitOfWork,
        feature_id: str,
        decision: ApprovalDecision,
        actor_id: str,
    ) -> None:
        approvals = await uow.approvals.list(
            entity_id=feature_id, approval_type=ApprovalType.SCOPE, limit=5
        )
        for approval in approvals:
            if approval.decision == ApprovalDecision.PENDING:
                approval.decision = decision
                approval.decided_at = _now()
                approval.comment = f"decided by {actor_id}"

    # --- helpers ---------------------------------------------------------
    async def _get_feature(
        self, uow: SqlAlchemyUnitOfWork, feature_id: str
    ) -> FeatureRequest:
        feature = await uow.feature_requests.get(feature_id)
        if feature is None:
            raise EntityNotFound("FeatureRequest", feature_id)
        return feature

    async def _answered_map(
        self, uow: SqlAlchemyUnitOfWork, feature_id: str
    ) -> dict[str, str]:
        questions = await uow.questions.list(feature_request_id=feature_id, limit=200)
        return {
            q.question: q.answer
            for q in questions
            if q.state == QuestionState.ANSWERED and q.answer
        }

    async def _pending_blocking(
        self, uow: SqlAlchemyUnitOfWork, feature_id: str
    ) -> list[ClarificationQuestion]:
        questions = await uow.questions.list(feature_request_id=feature_id, limit=200)
        return [
            q for q in questions if q.blocking and q.state == QuestionState.PENDING
        ]


def _story_contract(story: Story):  # type: ignore[no-untyped-def]
    """Lightweight adapter from ORM Story to the rendering contract shape."""
    from adf.domain.contracts import StoryContract

    return StoryContract(
        title=story.title,
        description=story.description,
        acceptance_criteria=list(story.acceptance_criteria),
        gherkin=[],
        priority=story.priority,
        estimated_complexity=story.estimated_complexity,
        dependencies=list(story.dependencies),
    )
