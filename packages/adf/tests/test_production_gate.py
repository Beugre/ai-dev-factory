"""Production deployments are never automatic — a human approval is required."""

from __future__ import annotations

import pytest
from adf.application.services.approval_service import ApprovalService
from adf.domain.enums import ApprovalDecision, DeploymentEnvironment
from adf.domain.errors import HumanApprovalRequired
from adf.infrastructure.db.models import Project
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.usefixtures("schema")


async def _project() -> str:
    async with SqlAlchemyUnitOfWork() as uow:
        project = await uow.projects.add(
            Project(name="D", slug="demo-app", github_owner="acme", github_repo="demo-repo")
        )
        await uow.commit()
        return project.id


async def test_production_requires_explicit_approval() -> None:
    project_id = await _project()
    service = ApprovalService()
    async with SqlAlchemyUnitOfWork() as uow:
        with pytest.raises(HumanApprovalRequired):
            await service.ensure_production_approved(
                uow, project_id=project_id, entity_id="feature-1"
            )


async def test_production_allowed_after_approval() -> None:
    project_id = await _project()
    service = ApprovalService()
    async with SqlAlchemyUnitOfWork() as uow:
        approval = await service.request_production_approval(
            uow, project_id=project_id, entity_type="FeatureRequest", entity_id="feature-1"
        )
        await service.approve(uow, approval.id, actor_id="owner")
        await uow.commit()

    async with SqlAlchemyUnitOfWork() as uow:
        # Should not raise now.
        await service.ensure_production_approved(
            uow, project_id=project_id, entity_id="feature-1"
        )
        approvals = await uow.approvals.list(entity_id="feature-1", limit=5)
        assert any(a.decision == ApprovalDecision.APPROVED for a in approvals)


def test_production_is_the_only_human_gated_environment() -> None:
    from adf.application.services.approval_service import HUMAN_GATED_ENVIRONMENTS

    assert DeploymentEnvironment.PRODUCTION in HUMAN_GATED_ENVIRONMENTS
    assert DeploymentEnvironment.STAGING not in HUMAN_GATED_ENVIRONMENTS
