"""Root-level test configuration for integration/contract/e2e suites.

These exercise the installed ``adf`` package against a temporary SQLite database
with mock adapters (no external services). Run with: ``pytest tests`` from the
repository root (requires ``pip install -e ./packages/adf[dev]``).
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

os.environ.setdefault("AGENT_RUNTIME", "mock")
os.environ.setdefault("NOTIFICATION_GATEWAY", "mock")
os.environ.setdefault("DEPLOYMENT_MODE", "mock")
os.environ.setdefault("COPILOT_DISPATCH_MODE", "issue_assignment")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-webhook-secret")


@pytest.fixture(autouse=True)
def _isolated_db() -> Iterator[None]:
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
