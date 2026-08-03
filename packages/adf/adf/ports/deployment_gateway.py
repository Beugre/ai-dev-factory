"""Port for deployments (preview / staging / production)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from adf.domain.enums import DeploymentEnvironment


@dataclass(slots=True)
class DeploymentRequest:
    environment: DeploymentEnvironment
    version: str
    ref: str
    project_slug: str


@dataclass(slots=True)
class DeploymentResult:
    status: str
    url: str | None
    detail: str


class DeploymentGateway(Protocol):
    mode: str

    async def deploy(self, request: DeploymentRequest) -> DeploymentResult: ...
