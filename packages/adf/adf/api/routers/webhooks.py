"""GitHub webhook receiver: verifies signature and processes idempotently."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header, Request, Response

from adf.api.deps import UowDep, get_container
from adf.application.container import Container
from adf.application.services.webhook_service import WebhookService
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger("adf.webhooks")


@router.post("/github")
async def github_webhook(
    request: Request,
    response: Response,
    x_github_event: str = Header(default="unknown"),
    x_github_delivery: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
    container: Container = Depends(get_container),
    uow: SqlAlchemyUnitOfWork = UowDep,
) -> dict[str, object]:
    body = await request.body()

    # 1. Signature verification (rejects tampered/forged payloads).
    if not container.webhook_verifier.verify(body, x_hub_signature_256):
        response.status_code = 401
        return {"code": "invalid_signature", "message": "Signature invalide"}

    if not x_github_delivery:
        response.status_code = 400
        return {"code": "missing_delivery_id", "message": "X-GitHub-Delivery requis"}

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        response.status_code = 400
        return {"code": "invalid_json", "message": "Corps JSON invalide"}

    service = WebhookService()
    outcome = await service.handle(
        uow,
        delivery_id=x_github_delivery,
        event_type=x_github_event,
        payload=payload,
    )
    await uow.commit()

    # Idempotent: duplicate deliveries return 200 without reprocessing.
    return {
        "processed": outcome.processed,
        "duplicate": outcome.duplicate,
        "detail": outcome.detail,
    }
