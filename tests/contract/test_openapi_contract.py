"""Contract test: the OpenAPI spec exposes the documented endpoints."""

from __future__ import annotations

import pytest

EXPECTED_PATHS = [
    "/api/v1/projects",
    "/api/v1/feature-requests",
    "/api/v1/feature-requests/{feature_id}/analyze",
    "/api/v1/feature-requests/{feature_id}/approve-scope",
    "/api/v1/questions/{question_id}/answer",
    "/api/v1/stories/{story_id}/dispatch",
    "/api/v1/approvals",
    "/api/v1/pull-requests/{pr_id}/approve-staging",
    "/api/v1/agent-runs",
    "/api/v1/deployments",
    "/api/v1/audit-logs",
    "/api/v1/webhooks/github",
]


@pytest.mark.contract
def test_openapi_exposes_documented_endpoints() -> None:
    from adf.api.app import create_app

    spec = create_app().openapi()
    for path in EXPECTED_PATHS:
        assert path in spec["paths"], f"Missing OpenAPI path: {path}"


@pytest.mark.contract
def test_error_schema_is_structured() -> None:
    from adf.api.schemas import ErrorResponse

    fields = set(ErrorResponse.model_fields)
    assert {"code", "message", "correlation_id"} <= fields
