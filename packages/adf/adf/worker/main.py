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
    # socket_timeout doit être > blpop timeout pour éviter le TimeoutError socket.
    client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=15,
        socket_connect_timeout=10,
    )
    logger.info("worker_started", queue=QUEUE_KEY)
    try:
        while True:
            try:
                item = await client.blpop([QUEUE_KEY], timeout=5)
            except Exception as exc:  # noqa: BLE001
                logger.warning("worker_redis_error", error=f"{type(exc).__name__}: {exc}")
                await asyncio.sleep(2)
                continue
            if item is None:
                continue
            _, raw = item
            try:
                result = await process_job(raw)
                logger.info("worker_job_done", result=result)
            except Exception as exc:  # noqa: BLE001
                logger.error("worker_job_failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        await client.aclose()  # type: ignore[attr-defined]


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run())


if __name__ == "__main__":
    main()
