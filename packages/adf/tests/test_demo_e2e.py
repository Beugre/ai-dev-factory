"""End-to-end demo workflow (mock adapters, no external services)."""

from __future__ import annotations

import pytest
from adf.application.demo import run_demo
from adf.domain.enums import FeatureState

pytestmark = pytest.mark.e2e


async def test_full_demo_workflow() -> None:
    report = await run_demo()
    assert report.final_feature_state == FeatureState.DONE.value
    assert report.issues_created >= 3
    assert report.dispatch_confirmed is True
    assert report.deployment_url is not None
    assert report.notifications >= 1
    assert "DONE" in report.story_states
    # The workflow visited clarification, scope approval and change-request steps.
    joined = " ".join(report.steps)
    assert "question" in joined.lower()
    assert "approuv" in joined.lower()
    assert "modification" in joined.lower()
