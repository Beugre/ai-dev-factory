"""ORM models mapping the AI Dev Factory domain to relational tables.

Enums are stored as their string values. JSON columns hold list/dict payloads
and work on both SQLite (dev/tests) and PostgreSQL (prod).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adf.domain.enums import (
    AgentRunState,
    AgentType,
    ApprovalDecision,
    ApprovalType,
    CIState,
    DeploymentEnvironment,
    DeploymentStatus,
    EpicStatus,
    FeatureSource,
    FeatureState,
    NotificationStatus,
    Priority,
    ProjectStatus,
    PullRequestState,
    QuestionAnswerType,
    QuestionState,
    ReviewState,
    StoryStatus,
)
from adf.infrastructure.db import Base
from adf.infrastructure.db.types import StrEnumType


class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    github_owner: Mapped[str] = mapped_column(String(200))
    github_repo: Mapped[str] = mapped_column(String(200))
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    staging_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        StrEnumType(ProjectStatus), default=ProjectStatus.ACTIVE
    )

    feature_requests: Mapped[list[FeatureRequest]] = relationship(back_populates="project")


class FeatureRequest(Base):
    __tablename__ = "feature_requests"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    raw_request: Mapped[str] = mapped_column(Text)
    normalized_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[FeatureSource] = mapped_column(
        StrEnumType(FeatureSource), default=FeatureSource.API
    )
    requester_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[FeatureState] = mapped_column(
        StrEnumType(FeatureState), default=FeatureState.DRAFT, index=True
    )
    priority: Mapped[Priority] = mapped_column(
        StrEnumType(Priority), default=Priority.MEDIUM
    )

    project: Mapped[Project] = relationship(back_populates="feature_requests")
    questions: Mapped[list[ClarificationQuestion]] = relationship(
        back_populates="feature_request", cascade="all, delete-orphan"
    )
    epics: Mapped[list[Epic]] = relationship(
        back_populates="feature_request", cascade="all, delete-orphan"
    )


class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"

    feature_request_id: Mapped[str] = mapped_column(
        ForeignKey("feature_requests.id"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer_type: Mapped[QuestionAnswerType] = mapped_column(
        StrEnumType(QuestionAnswerType), default=QuestionAnswerType.FREE_TEXT
    )
    options: Mapped[list[str]] = mapped_column(JSON, default=list)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    state: Mapped[QuestionState] = mapped_column(
        StrEnumType(QuestionState), default=QuestionState.PENDING
    )
    asked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    feature_request: Mapped[FeatureRequest] = relationship(back_populates="questions")


class Epic(Base):
    __tablename__ = "epics"

    feature_request_id: Mapped[str] = mapped_column(
        ForeignKey("feature_requests.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    business_value: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[EpicStatus] = mapped_column(
        StrEnumType(EpicStatus), default=EpicStatus.DRAFT
    )
    github_issue_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    feature_request: Mapped[FeatureRequest] = relationship(back_populates="epics")
    stories: Mapped[list[Story]] = relationship(
        back_populates="epic", cascade="all, delete-orphan"
    )


class Story(Base):
    __tablename__ = "stories"

    epic_id: Mapped[str] = mapped_column(ForeignKey("epics.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    gherkin: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[Priority] = mapped_column(
        StrEnumType(Priority), default=Priority.MEDIUM
    )
    estimated_complexity: Mapped[int] = mapped_column(Integer, default=3)
    dependencies: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[StoryStatus] = mapped_column(
        StrEnumType(StoryStatus), default=StoryStatus.DRAFT, index=True
    )
    assigned_agent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    github_issue_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_issue_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pull_request_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pull_request_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    epic: Mapped[Epic] = relationship(back_populates="stories")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    feature_request_id: Mapped[str | None] = mapped_column(
        ForeignKey("feature_requests.id"), nullable=True, index=True
    )
    story_id: Mapped[str | None] = mapped_column(
        ForeignKey("stories.id"), nullable=True, index=True
    )
    agent_type: Mapped[AgentType] = mapped_column(StrEnumType(AgentType))
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[AgentRunState] = mapped_column(
        StrEnumType(AgentRunState), default=AgentRunState.PENDING
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)


class Approval(Base):
    __tablename__ = "approvals"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(64))
    approval_type: Mapped[ApprovalType] = mapped_column(StrEnumType(ApprovalType))
    requested_from: Mapped[str] = mapped_column(String(200), default="owner")
    decision: Mapped[ApprovalDecision] = mapped_column(
        StrEnumType(ApprovalDecision), default=ApprovalDecision.PENDING, index=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (UniqueConstraint("repository", "number", name="uq_pr_repo_number"),)

    story_id: Mapped[str | None] = mapped_column(
        ForeignKey("stories.id"), nullable=True, index=True
    )
    repository: Mapped[str] = mapped_column(String(200))
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    branch: Mapped[str] = mapped_column(String(200))
    state: Mapped[PullRequestState] = mapped_column(
        StrEnumType(PullRequestState), default=PullRequestState.OPEN
    )
    ci_state: Mapped[CIState] = mapped_column(
        StrEnumType(CIState), default=CIState.UNKNOWN
    )
    review_state: Mapped[ReviewState] = mapped_column(
        StrEnumType(ReviewState), default=ReviewState.PENDING
    )
    preview_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mergeable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Deployment(Base):
    __tablename__ = "deployments"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    pull_request_id: Mapped[str | None] = mapped_column(
        ForeignKey("pull_requests.id"), nullable=True
    )
    environment: Mapped[DeploymentEnvironment] = mapped_column(
        StrEnumType(DeploymentEnvironment)
    )
    version: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[DeploymentStatus] = mapped_column(
        StrEnumType(DeploymentStatus), default=DeploymentStatus.PENDING
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Notification(Base):
    __tablename__ = "notifications"

    channel: Mapped[str] = mapped_column(String(50))
    recipient: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[NotificationStatus] = mapped_column(
        StrEnumType(NotificationStatus), default=NotificationStatus.PENDING
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_entity", "entity_type", "entity_id"),)

    actor_type: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(64))
    event_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class WebhookEvent(Base):
    """Idempotency ledger for inbound GitHub webhooks (delivery id = PK)."""

    __tablename__ = "webhook_events"

    delivery_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
