"""Worker entrypoint: blocking-pop loop over the Redis job queue."""

from __future__ import annotations

import asyncio
import contextlib

import redis.asyncio as redis

from adf.config import get_settings
from adf.infrastructure.logging import get_logger
from adf.worker.jobs import QUEUE_KEY, process_job

logger = get_logger("adf.worker")


async def run() -> None:
    settings = get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)
    logger.info("worker_started", queue=QUEUE_KEY)
    try:
        while True:
            item = await client.blpop([QUEUE_KEY], timeout=5)
            if item is None:
                continue
            _, raw = item
            try:
                result = await process_job(raw)
                logger.info("worker_job_done", result=result)
            except Exception as exc:
                logger.error("worker_job_failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        await client.aclose()  # type: ignore[attr-defined]


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run())


if __name__ == "__main__":
    main()
