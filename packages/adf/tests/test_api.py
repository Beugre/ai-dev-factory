"""API smoke tests over the FastAPI app using the TestClient."""

from __future__ import annotations

import pytest
from adf.api.deps import get_container
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    # Rebuild the cached container so it uses the isolated test DB-independent
    # mock adapters.
    get_container.cache_clear()
    import asyncio

    from adf.infrastructure.db import create_all

    asyncio.run(create_all())
    from adf.api.app import create_app

    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_openapi_available(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "AI Dev Factory API"
    assert "/api/v1/feature-requests" in spec["paths"]


def test_feature_flow_over_http(client: TestClient) -> None:
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "Demo",
            "slug": "demo-app",
            "github_owner": "acme",
            "github_repo": "demo-repo",
        },
    ).json()

    feature = client.post(
        "/api/v1/feature-requests",
        json={
            "project_id": project["id"],
            "title": "Reset password",
            "raw_request": "Je veux réinitialiser mon mot de passe",
        },
    ).json()
    assert feature["state"] == "DRAFT"

    analyzed = client.post(f"/api/v1/feature-requests/{feature['id']}/analyze").json()
    assert analyzed["state"] == "NEEDS_CLARIFICATION"

    questions = client.get(
        f"/api/v1/feature-requests/{feature['id']}/questions"
    ).json()
    assert len(questions) >= 3

    for question in questions:
        client.post(
            f"/api/v1/questions/{question['id']}/answer",
            json={"answer": "Email"},
        )

    refreshed = client.get(f"/api/v1/feature-requests/{feature['id']}").json()
    assert refreshed["state"] == "READY_FOR_SCOPE_APPROVAL"

    approved = client.post(
        f"/api/v1/feature-requests/{feature['id']}/approve-scope", json={}
    ).json()
    assert approved["state"] == "READY_FOR_DEVELOPMENT"


def test_invalid_transition_returns_structured_error(client: TestClient) -> None:
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "Demo",
            "slug": "demo-app",
            "github_owner": "acme",
            "github_repo": "demo-repo",
        },
    ).json()
    feature = client.post(
        "/api/v1/feature-requests",
        json={
            "project_id": project["id"],
            "title": "Feature X",
            "raw_request": "quelque chose",
        },
    ).json()
    # Approving scope from DRAFT is invalid.
    resp = client.post(f"/api/v1/feature-requests/{feature['id']}/approve-scope", json={})
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "invalid_state_transition"
    assert "correlation_id" in body
