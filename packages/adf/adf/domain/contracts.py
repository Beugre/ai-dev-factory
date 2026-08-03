"""Structured contracts (value objects) exchanged with agents.

These Pydantic models validate the *structured output* produced by any
:class:`AgentRuntime`. Because agent output may be influenced by untrusted
content, validation here is a security boundary — malformed or oversized
payloads are rejected before they touch the persistence layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from adf.domain.enums import Priority, QuestionAnswerType

MAX_TEXT = 8_000


class ClarificationQuestionContract(BaseModel):
    question: str = Field(min_length=3, max_length=1_000)
    answer_type: QuestionAnswerType
    options: list[str] = Field(default_factory=list, max_length=10)
    blocking: bool = True

    @field_validator("options")
    @classmethod
    def _trim_options(cls, value: list[str]) -> list[str]:
        return [o.strip()[:200] for o in value if o.strip()]


class GherkinScenario(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    steps: list[str] = Field(min_length=1, max_length=30)


class StoryContract(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(max_length=MAX_TEXT)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=30)
    gherkin: list[GherkinScenario] = Field(default_factory=list, max_length=20)
    priority: Priority = Priority.MEDIUM
    estimated_complexity: int = Field(ge=1, le=13, default=3)
    dependencies: list[str] = Field(default_factory=list, max_length=20)


class EpicContract(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(max_length=MAX_TEXT)
    business_value: str = Field(max_length=2_000)


class ProductOwnerAnalysis(BaseModel):
    """The full structured result of the Product Owner agent."""

    normalized_request: str = Field(max_length=MAX_TEXT)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    risks: list[str] = Field(default_factory=list, max_length=20)
    business_rules: list[str] = Field(default_factory=list, max_length=30)
    questions: list[ClarificationQuestionContract] = Field(
        default_factory=list, max_length=15
    )
    epic: EpicContract
    stories: list[StoryContract] = Field(default_factory=list, max_length=30)

    @property
    def has_blocking_questions(self) -> bool:
        return any(q.blocking for q in self.questions)


class ReviewFinding(BaseModel):
    severity: str = Field(pattern="^(blocking|important|suggestion)$")
    message: str = Field(max_length=2_000)


class ReviewContract(BaseModel):
    summary: str = Field(max_length=4_000)
    findings: list[ReviewFinding] = Field(default_factory=list, max_length=50)
    verdict: str = Field(pattern="^(approved|changes_requested)$")


class QAContract(BaseModel):
    summary: str = Field(max_length=4_000)
    scenarios_checked: list[str] = Field(default_factory=list, max_length=50)
    missing_tests: list[str] = Field(default_factory=list, max_length=50)
    verdict: str = Field(pattern="^(pass|fail)$")
