"""GitHub webhook signature verification and idempotency."""

from __future__ import annotations

import json

import pytest
from adf.adapters.github.webhooks import GitHubWebhookVerifier
from adf.application.services.webhook_service import WebhookService
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.usefixtures("schema")


def test_signature_valid_and_invalid() -> None:
    verifier = GitHubWebhookVerifier("s3cr3t")
    payload = b'{"hello":"world"}'
    signature = verifier.sign(payload)
    assert verifier.verify(payload, signature)
    assert not verifier.verify(payload, "sha256=deadbeef")
    assert not verifier.verify(payload, None)
    assert not verifier.verify(b"tampered", signature)


async def test_webhook_idempotency() -> None:
    service = WebhookService()
    payload = {"pull_request": {"number": 1, "state": "open", "merged": False}}
    async with SqlAlchemyUnitOfWork() as uow:
        first = await service.handle(
            uow, delivery_id="delivery-1", event_type="pull_request", payload=payload
        )
        await uow.commit()
    async with SqlAlchemyUnitOfWork() as uow:
        second = await service.handle(
            uow, delivery_id="delivery-1", event_type="pull_request", payload=payload
        )
        await uow.commit()

    assert first.processed and not first.duplicate
    assert second.duplicate and not second.processed


async def test_check_run_updates_ci_state() -> None:
    from adf.domain.enums import CIState
    from adf.infrastructure.db.models import PullRequest

    async with SqlAlchemyUnitOfWork() as uow:
        pr = await uow.pull_requests.add(
            PullRequest(
                repository="acme/demo-repo",
                number=42,
                title="feat",
                branch="feature/x",
            )
        )
        await uow.commit()
        pr_id = pr.id

    payload = json.loads(
        json.dumps(
            {
                "check_run": {
                    "conclusion": "failure",
                    "pull_requests": [{"number": 42}],
                }
            }
        )
    )
    service = WebhookService()
    async with SqlAlchemyUnitOfWork() as uow:
        await service.handle(
            uow, delivery_id="d-ci-1", event_type="check_run", payload=payload
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork() as uow:
        pr = await uow.pull_requests.get(pr_id)
        assert pr is not None
        assert pr.ci_state == CIState.FAILURE
