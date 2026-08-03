"""Job definitions and a Redis-list queue.

Jobs are JSON documents ``{"type": ..., "payload": {...}}``. Processing is
idempotent where it matters (feature analysis is safe to retry).
"""

from __future__ import annotations

import json
from typing import Any

from adf.application.container import build_container
from adf.application.services.feature_service import FeatureService
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger

logger = get_logger("adf.worker")

QUEUE_KEY = "adf:jobs"

JOB_ANALYZE_FEATURE = "analyze_feature"


def encode_job(job_type: str, payload: dict[str, Any]) -> str:
    return json.dumps({"type": job_type, "payload": payload})


async def process_job(raw: str) -> str:
    try:
        job = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("worker_bad_job", raw=raw[:120])
        return "invalid"

    job_type = job.get("type")
    payload = job.get("payload", {})
    if job_type == JOB_ANALYZE_FEATURE:
        return await _analyze_feature(payload.get("feature_id", ""))
    logger.warning("worker_unknown_job", type=job_type)
    return "unknown"


async def _analyze_feature(feature_id: str) -> str:
    if not feature_id:
        return "missing feature_id"
    container = build_container()
    service = FeatureService(container)
    async with SqlAlchemyUnitOfWork() as uow:
        await service.analyze(uow, feature_id)
        await uow.commit()
    logger.info("worker_feature_analyzed", feature_id=feature_id)
    return "analyzed"
