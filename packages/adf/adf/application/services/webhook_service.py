"""GitHub webhook processing: idempotent, signature-verified upstream."""

from __future__ import annotations

from dataclasses import dataclass

from adf.application.audit import record_audit
from adf.domain.enums import ActorType, CIState, PullRequestState, ReviewState
from adf.infrastructure.db.models import PullRequest, WebhookEvent
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger
from adf.infrastructure.metrics import webhook_events_total

logger = get_logger(__name__)


@dataclass(slots=True)
class WebhookOutcome:
    processed: bool
    duplicate: bool
    detail: str


SUPPORTED_EVENTS = frozenset(
    {
        "issues",
        "issue_comment",
        "pull_request",
        "pull_request_review",
        "pull_request_review_comment",
        "check_run",
        "check_suite",
        "workflow_run",
        "deployment",
        "deployment_status",
    }
)


class WebhookService:
    async def handle(
        self,
        uow: SqlAlchemyUnitOfWork,
        *,
        delivery_id: str,
        event_type: str,
        payload: dict[str, object],
    ) -> WebhookOutcome:
        # Idempotency: the delivery id is the key. Duplicate deliveries no-op.
        existing = await uow.webhook_events.list(delivery_id=delivery_id, limit=1)
        if existing:
            webhook_events_total.labels(event_type=event_type, result="duplicate").inc()
            return WebhookOutcome(processed=False, duplicate=True, detail="duplicate delivery")

        await uow.webhook_events.add(
            WebhookEvent(
                delivery_id=delivery_id,
                event_type=event_type,
                processed=False,
                payload=payload,
            )
        )

        if event_type not in SUPPORTED_EVENTS:
            webhook_events_total.labels(event_type=event_type, result="ignored").inc()
            return WebhookOutcome(processed=False, duplicate=False, detail="unsupported event")

        detail = await self._apply(uow, event_type, payload)

        record = (await uow.webhook_events.list(delivery_id=delivery_id, limit=1))[0]
        record.processed = True
        webhook_events_total.labels(event_type=event_type, result="processed").inc()
        await record_audit(
            uow,
            actor_type=ActorType.GITHUB,
            actor_id=delivery_id,
            action=f"webhook.{event_type}",
            entity_type="WebhookEvent",
            entity_id=record.id,
            metadata={"detail": detail},
        )
        return WebhookOutcome(processed=True, duplicate=False, detail=detail)

    async def _apply(
        self, uow: SqlAlchemyUnitOfWork, event_type: str, payload: dict[str, object]
    ) -> str:
        if event_type in {"check_run", "check_suite", "workflow_run"}:
            return await self._update_ci(uow, payload)
        if event_type == "pull_request":
            return await self._update_pr(uow, payload)
        if event_type == "pull_request_review":
            return await self._update_review(uow, payload)
        return "recorded"

    async def _find_pr(
        self, uow: SqlAlchemyUnitOfWork, number: int | None
    ) -> PullRequest | None:
        if number is None:
            return None
        prs = await uow.pull_requests.list(number=number, limit=1)
        return prs[0] if prs else None

    async def _update_ci(
        self, uow: SqlAlchemyUnitOfWork, payload: dict[str, object]
    ) -> str:
        conclusion = _dig(payload, "check_run", "conclusion") or _dig(
            payload, "workflow_run", "conclusion"
        )
        pr_number = _first_pr_number(payload)
        pr = await self._find_pr(uow, pr_number)
        if pr is None:
            return "ci event without known PR"
        pr.ci_state = _ci_from_conclusion(str(conclusion) if conclusion else "")
        return f"ci -> {pr.ci_state.value}"

    async def _update_pr(
        self, uow: SqlAlchemyUnitOfWork, payload: dict[str, object]
    ) -> str:
        number = _dig(payload, "pull_request", "number")
        pr = await self._find_pr(uow, _as_int(number))
        if pr is None:
            return "pull_request event without known PR"
        state = _dig(payload, "pull_request", "state")
        merged = _dig(payload, "pull_request", "merged")
        if merged:
            pr.state = PullRequestState.MERGED
        elif state == "closed":
            pr.state = PullRequestState.CLOSED
        else:
            pr.state = PullRequestState.OPEN
        return f"pr -> {pr.state.value}"

    async def _update_review(
        self, uow: SqlAlchemyUnitOfWork, payload: dict[str, object]
    ) -> str:
        number = _dig(payload, "pull_request", "number")
        pr = await self._find_pr(uow, _as_int(number))
        if pr is None:
            return "review event without known PR"
        state = str(_dig(payload, "review", "state") or "").lower()
        if state == "approved":
            pr.review_state = ReviewState.APPROVED
        elif state == "changes_requested":
            pr.review_state = ReviewState.CHANGES_REQUESTED
        return f"review -> {pr.review_state.value}"


def _dig(payload: dict[str, object], *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _as_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _first_pr_number(payload: dict[str, object]) -> int | None:
    for container_key in ("check_run", "check_suite", "workflow_run"):
        prs = _dig(payload, container_key, "pull_requests")
        if isinstance(prs, list) and prs:
            first = prs[0]
            if isinstance(first, dict) and "number" in first:
                return _as_int(first["number"])
    return None


def _ci_from_conclusion(conclusion: str) -> CIState:
    if conclusion == "success":
        return CIState.SUCCESS
    if conclusion in {"failure", "cancelled", "timed_out"}:
        return CIState.FAILURE
    if conclusion == "":
        return CIState.RUNNING
    return CIState.UNKNOWN
