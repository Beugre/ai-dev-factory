"""Agent runtime: deterministic output + Pydantic validation of AI output."""

from __future__ import annotations

import pytest
from adf.adapters.agent_runtime.mock import MockAgentRuntime
from adf.domain.contracts import ProductOwnerAnalysis, StoryContract
from adf.domain.enums import AgentType
from adf.ports.agent_runtime import AgentRequest
from pydantic import ValidationError


def _request(raw: str, answers: dict[str, str] | None = None) -> AgentRequest:
    return AgentRequest(
        role=AgentType.PRODUCT_OWNER,
        instructions="analyse",
        context={"raw_request": raw, "answers": answers or {}},
        correlation_id="corr-1",
    )


async def test_password_reset_produces_blocking_questions() -> None:
    runtime = MockAgentRuntime()
    analysis, result = await runtime.run(
        _request("Je veux réinitialiser mon mot de passe"), ProductOwnerAnalysis
    )
    assert analysis.has_blocking_questions
    assert len(analysis.questions) >= 3
    assert result.provider == "mock"


async def test_answers_yield_stories_with_gherkin() -> None:
    runtime = MockAgentRuntime()
    analysis, _ = await runtime.run(
        _request(
            "réinitialisation du mot de passe",
            answers={"canal": "Email", "durée": "1 heure"},
        ),
        ProductOwnerAnalysis,
    )
    assert not analysis.has_blocking_questions
    assert len(analysis.stories) >= 2
    assert all(s.acceptance_criteria for s in analysis.stories)
    assert any(s.gherkin for s in analysis.stories)


async def test_deterministic_output() -> None:
    runtime = MockAgentRuntime()
    a1, _ = await runtime.run(_request("réinitialiser mot de passe"), ProductOwnerAnalysis)
    a2, _ = await runtime.run(_request("réinitialiser mot de passe"), ProductOwnerAnalysis)
    assert a1.model_dump() == a2.model_dump()


def test_story_contract_rejects_oversized_input() -> None:
    with pytest.raises(ValidationError):
        StoryContract(title="x", description="d")  # title too short


def test_story_contract_bounds_complexity() -> None:
    with pytest.raises(ValidationError):
        StoryContract(title="Valid title", description="d", estimated_complexity=99)
