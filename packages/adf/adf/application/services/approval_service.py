"""Approval use-cases and the production human-approval gate."""

from __future__ import annotations

from datetime import UTC, datetime

from adf.application.audit import record_audit
from adf.domain.enums import (
    ActorType,
    ApprovalDecision,
    ApprovalType,
    DeploymentEnvironment,
)
from adf.domain.errors import EntityNotFound, HumanApprovalRequired
from adf.infrastructure.db.models import Approval
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork


class ApprovalService:
    async def approve(
        self,
        uow: SqlAlchemyUnitOfWork,
        approval_id: str,
        *,
        actor_id: str = "owner",
        comment: str | None = None,
    ) -> Approval:
        return await self._decide(uow, approval_id, ApprovalDecision.APPROVED, actor_id, comment)

    async def reject(
        self,
        uow: SqlAlchemyUnitOfWork,
        approval_id: str,
        *,
        actor_id: str = "owner",
        comment: str | None = None,
    ) -> Approval:
        return await self._decide(uow, approval_id, ApprovalDecision.REJECTED, actor_id, comment)

    async def _decide(
        self,
        uow: SqlAlchemyUnitOfWork,
        approval_id: str,
        decision: ApprovalDecision,
        actor_id: str,
        comment: str | None,
    ) -> Approval:
        approval = await uow.approvals.get(approval_id)
        if approval is None:
            raise EntityNotFound("Approval", approval_id)
        approval.decision = decision
        approval.decided_at = datetime.now(UTC)
        approval.comment = comment
        await record_audit(
            uow,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action=f"approval.{decision.value}",
            entity_type="Approval",
            entity_id=approval.id,
            metadata={"approval_type": approval.approval_type.value},
        )
        return approval

    async def ensure_production_approved(
        self, uow: SqlAlchemyUnitOfWork, *, project_id: str, entity_id: str
    ) -> None:
        """Guard: raise unless an explicit PRODUCTION approval exists and is approved.

        Production deployments are NEVER automatic. This is enforced in the
        domain/application, not just the UI.
        """
        approvals = await uow.approvals.list(
            project_id=project_id,
            entity_id=entity_id,
            approval_type=ApprovalType.PRODUCTION,
            limit=10,
        )
        if not any(a.decision == ApprovalDecision.APPROVED for a in approvals):
            raise HumanApprovalRequired(
                "Un déploiement en production nécessite une approbation humaine explicite."
            )

    async def request_production_approval(
        self, uow: SqlAlchemyUnitOfWork, *, project_id: str, entity_type: str, entity_id: str
    ) -> Approval:
        approval = Approval(
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            approval_type=ApprovalType.PRODUCTION,
            decision=ApprovalDecision.PENDING,
            requested_at=datetime.now(UTC),
        )
        return await uow.approvals.add(approval)


# Environments that always require an explicit human approval.
HUMAN_GATED_ENVIRONMENTS = frozenset({DeploymentEnvironment.PRODUCTION})
