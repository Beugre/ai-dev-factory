"""Explicit domain enumerations for entity states and classifications."""

from __future__ import annotations

from enum import StrEnum


class FeatureState(StrEnum):
    """Lifecycle of a :class:`FeatureRequest`.

    Transitions are enforced by :mod:`adf.domain.state_machine`.
    """

    DRAFT = "DRAFT"
    ANALYZING = "ANALYZING"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    READY_FOR_SCOPE_APPROVAL = "READY_FOR_SCOPE_APPROVAL"
    SCOPE_APPROVED = "SCOPE_APPROVED"
    CREATING_ISSUES = "CREATING_ISSUES"
    READY_FOR_DEVELOPMENT = "READY_FOR_DEVELOPMENT"
    IN_DEVELOPMENT = "IN_DEVELOPMENT"
    IN_REVIEW = "IN_REVIEW"
    READY_FOR_STAGING = "READY_FOR_STAGING"
    STAGING_DEPLOYED = "STAGING_DEPLOYED"
    READY_FOR_ACCEPTANCE = "READY_FOR_ACCEPTANCE"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    ACCEPTED = "ACCEPTED"
    READY_FOR_PRODUCTION = "READY_FOR_PRODUCTION"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class StoryStatus(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    DISPATCHED = "DISPATCHED"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    STAGING = "STAGING"
    ACCEPTED = "ACCEPTED"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"


class EpicStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeatureSource(StrEnum):
    DISCORD = "discord"
    WEB = "web"
    API = "api"


class QuestionAnswerType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    FREE_TEXT = "free_text"
    BOOLEAN = "boolean"


class QuestionState(StrEnum):
    PENDING = "pending"
    ANSWERED = "answered"
    SKIPPED = "skipped"


class AgentType(StrEnum):
    PRODUCT_OWNER = "product_owner"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    QA = "qa"
    DOCUMENTATION = "documentation"
    RELEASE_MANAGER = "release_manager"


class AgentRunState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ApprovalType(StrEnum):
    SCOPE = "scope"
    STAGING = "staging"
    PRODUCTION = "production"
    DESTRUCTIVE_MIGRATION = "destructive_migration"


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class PullRequestState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class CIState(StrEnum):
    UNKNOWN = "unknown"
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


class ReviewState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class DeploymentEnvironment(StrEnum):
    PREVIEW = "preview"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ActorType(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    GITHUB = "github"
    DISCORD = "discord"
