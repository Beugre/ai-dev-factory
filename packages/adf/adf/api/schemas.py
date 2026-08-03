"""API schemas: requests, responses, pagination and structured errors."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from adf.domain.enums import FeatureSource, Priority


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: str | None = None


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


# --- Projects ------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern="^[a-z0-9-]+$")
    github_owner: str
    github_repo: str
    default_branch: str = "main"
    staging_url: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    github_owner: str
    github_repo: str
    default_branch: str
    staging_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime


# --- Feature requests ----------------------------------------------------
class FeatureRequestCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=3, max_length=300)
    raw_request: str = Field(min_length=3, max_length=8000)
    source: FeatureSource = FeatureSource.API
    requester_id: str | None = None
    priority: Priority = Priority.MEDIUM


class FeatureRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    title: str
    raw_request: str
    normalized_request: str | None
    source: str
    requester_id: str | None
    state: str
    priority: str
    created_at: datetime
    updated_at: datetime


class RequestChangesIn(BaseModel):
    comment: str = Field(min_length=1, max_length=4000)


class ActorIn(BaseModel):
    actor_id: str = "owner"


# --- Questions -----------------------------------------------------------
class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    feature_request_id: str
    question: str
    answer_type: str
    options: list[str]
    answer: str | None
    blocking: bool
    state: str


class AnswerIn(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)
    actor_id: str = "owner"


# --- Epics / Stories -----------------------------------------------------
class EpicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    feature_request_id: str
    title: str
    description: str
    business_value: str
    status: str
    github_issue_number: int | None


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    epic_id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    gherkin: str
    priority: str
    estimated_complexity: int
    dependencies: list[str]
    status: str
    assigned_agent: str | None
    github_issue_number: int | None
    github_issue_url: str | None
    pull_request_number: int | None
    pull_request_url: str | None


class DispatchOut(BaseModel):
    mode: str
    confirmed: bool
    detail: str


# --- Approvals -----------------------------------------------------------
class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    entity_type: str
    entity_id: str
    approval_type: str
    decision: str
    comment: str | None


class DecisionIn(BaseModel):
    comment: str | None = None
    actor_id: str = "owner"


# --- Pull requests / deployments ----------------------------------------
class PullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    story_id: str | None
    repository: str
    number: int
    title: str
    branch: str
    state: str
    ci_state: str
    review_state: str
    preview_url: str | None
    mergeable: bool | None


class DeploymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    pull_request_id: str | None
    environment: str
    version: str
    status: str
    url: str | None


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    feature_request_id: str | None
    story_id: str | None
    agent_type: str
    provider: str
    model: str | None
    input_summary: str
    output_summary: str
    state: str
    error: str | None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    actor_type: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime
