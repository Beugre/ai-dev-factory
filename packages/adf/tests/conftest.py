"""Shared test fixtures.

Every test runs against an isolated temporary SQLite database so the suite
needs no external services (matching the mock-first design).
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator, Iterator

import pytest

# Force a mock, service-free configuration BEFORE importing app modules.
os.environ.setdefault("AGENT_RUNTIME", "mock")
os.environ.setdefault("NOTIFICATION_GATEWAY", "mock")
os.environ.setdefault("DEPLOYMENT_MODE", "mock")
os.environ.setdefault("COPILOT_DISPATCH_MODE", "issue_assignment")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-webhook-secret")


@pytest.fixture(autouse=True)
def _isolated_db() -> Iterator[None]:
    """Point the app at a fresh temp SQLite file for each test."""
    from adf.config import get_settings
    from adf.infrastructure.db import reset_engine

    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{path}"
    get_settings.cache_clear()
    reset_engine()
    try:
        yield
    finally:
        get_settings.cache_clear()
        reset_engine()
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture
async def schema() -> AsyncIterator[None]:
    from adf.infrastructure.db import create_all

    await create_all()
    yield


@pytest.fixture
def container():  # type: ignore[no-untyped-def]
    from adf.application.container import build_mock_container

    return build_mock_container()
