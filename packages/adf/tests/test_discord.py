"""Discord security and interaction routing."""

from __future__ import annotations

import pytest
from adf.application.container import build_mock_container
from adf.application.services.feature_service import FeatureService
from adf.discord_bot.interactions import InboundInteraction, InteractionRouter
from adf.discord_bot.security import DiscordSecurityPolicy, RateLimiter
from adf.infrastructure.db.models import Project
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.usefixtures("schema")

ALLOWED_USER = "1111"


def _policy() -> DiscordSecurityPolicy:
    return DiscordSecurityPolicy(allowed_user_ids=frozenset({ALLOWED_USER}))


async def _seed_feature_with_questions() -> tuple[str, list[str]]:
    container = build_mock_container()
    service = FeatureService(container)
    async with SqlAlchemyUnitOfWork() as uow:
        project = await uow.projects.add(
            Project(
                name="Demo",
                slug="demo-app",
                github_owner="acme",
                github_repo="demo-repo",
            )
        )
        feature = await service.create_feature(
            uow,
            project_id=project.id,
            title="Reset",
            raw_request="Je veux réinitialiser mon mot de passe",
        )
        await service.analyze(uow, feature.id)
        await uow.commit()
        questions = await uow.questions.list(feature_request_id=feature.id, limit=10)
        return feature.id, [q.id for q in questions]


async def test_unauthorized_user_is_refused() -> None:
    router = InteractionRouter(build_mock_container(), _policy(), RateLimiter())
    result = await router.handle(
        InboundInteraction(user_id="9999", action="approve_scope", target_id="x")
    )
    assert result.ok is False
    assert "autorisé" in result.message


async def test_answer_bound_to_correct_question() -> None:
    _, question_ids = await _seed_feature_with_questions()
    router = InteractionRouter(build_mock_container(), _policy(), RateLimiter())

    result = await router.handle(
        InboundInteraction(
            user_id=ALLOWED_USER,
            action="answer",
            target_id=question_ids[0],
            value="Email",
        )
    )
    assert result.ok is True

    async with SqlAlchemyUnitOfWork() as uow:
        answered = await uow.questions.get(question_ids[0])
        assert answered is not None
        assert answered.answer == "Email"
        assert answered.state.value == "answered"


async def test_malicious_answer_is_stored_as_data() -> None:
    _, question_ids = await _seed_feature_with_questions()
    router = InteractionRouter(build_mock_container(), _policy(), RateLimiter())
    payload = "; rm -rf / && echo pwned"
    result = await router.handle(
        InboundInteraction(
            user_id=ALLOWED_USER,
            action="answer",
            target_id=question_ids[0],
            value=payload,
        )
    )
    assert result.ok is True
    async with SqlAlchemyUnitOfWork() as uow:
        answered = await uow.questions.get(question_ids[0])
        assert answered is not None
        # Stored verbatim as data — never interpreted as a command.
        assert answered.answer == payload


def test_rate_limiter_blocks_after_threshold() -> None:
    limiter = RateLimiter(max_calls=2, window_seconds=100)
    assert limiter.allow("u", now=0)
    assert limiter.allow("u", now=1)
    assert not limiter.allow("u", now=2)


def test_empty_allowlist_denies_everyone() -> None:
    policy = DiscordSecurityPolicy(allowed_user_ids=frozenset())
    assert policy.is_user_allowed("anyone") is False
