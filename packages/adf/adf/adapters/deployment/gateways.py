"""Deployment gateways: mock, local (compose) and webhook.

Production deployments are NEVER performed automatically here — the domain
requires an explicit human approval before a production deployment can be
requested (see :mod:`adf.application.services.deployment_service`).
"""

from __future__ import annotations

import httpx

from adf.config import get_settings
from adf.domain.enums import DeploymentEnvironment
from adf.infrastructure.logging import get_logger
from adf.ports.deployment_gateway import DeploymentRequest, DeploymentResult

logger = get_logger(__name__)


class MockDeploymentGateway:
    mode = "mock"

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        self._base_url = base_url.rstrip("/")

    async def deploy(self, request: DeploymentRequest) -> DeploymentResult:
        url = f"{self._base_url}/{request.project_slug}/{request.environment.value}"
        return DeploymentResult(
            status="succeeded",
            url=url,
            detail=f"Déploiement simulé ({request.environment.value}).",
        )


class LocalDeploymentGateway:
    """Simulates a local preview served by the running Docker Compose stack."""

    mode = "local"

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        self._base_url = base_url.rstrip("/")

    async def deploy(self, request: DeploymentRequest) -> DeploymentResult:
        url = f"{self._base_url}/{request.project_slug}/{request.environment.value}"
        logger.info(
            "local_deploy", env=request.environment.value, version=request.version
        )
        return DeploymentResult(
            status="succeeded", url=url, detail="Preview locale disponible."
        )


class WebhookDeploymentGateway:
    """Triggers an external deployment by calling a configurable webhook."""

    mode = "webhook"

    def __init__(self, webhook_url: str, secret: str | None = None) -> None:
        self._webhook_url = webhook_url
        self._secret = secret

    async def deploy(self, request: DeploymentRequest) -> DeploymentResult:
        headers = {"X-ADF-Secret": self._secret} if self._secret else {}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self._webhook_url,
                    headers=headers,
                    json={
                        "environment": request.environment.value,
                        "version": request.version,
                        "ref": request.ref,
                        "project": request.project_slug,
                    },
                )
                resp.raise_for_status()
                body = resp.json() if resp.content else {}
            return DeploymentResult(
                status="in_progress",
                url=body.get("url"),
                detail="Webhook de déploiement déclenché.",
            )
        except httpx.HTTPError as exc:
            return DeploymentResult(
                status="failed", url=None, detail=f"Echec webhook: {type(exc).__name__}"
            )


def build_deployment_gateway() -> (
    MockDeploymentGateway | LocalDeploymentGateway | WebhookDeploymentGateway
):
    settings = get_settings()
    if settings.deployment_mode == "local":
        return LocalDeploymentGateway(settings.staging_base_url)
    if settings.deployment_mode == "webhook" and settings.staging_deploy_webhook_url:
        return WebhookDeploymentGateway(
            settings.staging_deploy_webhook_url, settings.n8n_webhook_secret
        )
    return MockDeploymentGateway(settings.staging_base_url)


__all__ = [
    "DeploymentEnvironment",
    "LocalDeploymentGateway",
    "MockDeploymentGateway",
    "WebhookDeploymentGateway",
    "build_deployment_gateway",
]
