"""Integration test: the full mock workflow end to end."""

from __future__ import annotations

import pytest

from adf.application.demo import run_demo
from adf.domain.enums import FeatureState


@pytest.mark.integration
async def test_demo_workflow_reaches_done() -> None:
    report = await run_demo()
    assert report.final_feature_state == FeatureState.DONE.value
    assert report.issues_created >= 3
    assert report.dispatch_confirmed is True
    assert report.deployment_url is not None
