"""Framework-agnostic Discord interaction routing.

Maps a Discord interaction (slash command / button / modal) to an application
use-case, enforcing the security policy first. This is the piece we unit-test;
``client.py`` merely translates discord.py objects into
:class:`InboundInteraction` values.

User-supplied text is always treated as DATA. It is never evaluated, executed
as a shell command, or fed back as instructions to an agent's system prompt.
"""

from __future__ import annotations

from dataclasses import dataclass

from adf.application.container import Container
from adf.application.services.feature_service import FeatureService
from adf.application.services.pull_request_service import PullRequestService
from adf.discord_bot.security import DiscordSecurityPolicy, RateLimiter
from adf.domain.enums import FeatureSource, Priority
from adf.domain.errors import DomainError
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger

logger = get_logger("adf.discord")


@dataclass(slots=True)
class InboundInteraction:
    user_id: str
    action: str
    guild_id: str | None = None
    channel_id: str | None = None
    target_id: str | None = None
    value: str | None = None
    extra: dict[str, str] | None = None


@dataclass(slots=True)
class InteractionResult:
    ok: bool
    message: str
    ephemeral: bool = False


class InteractionRouter:
    def __init__(
        self,
        container: Container,
        policy: DiscordSecurityPolicy,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._c = container
        self._policy = policy
        self._rate = rate_limiter or RateLimiter()
        self._features = FeatureService(container)
        self._prs = PullRequestService(container)

    async def handle(self, interaction: InboundInteraction) -> InteractionResult:
        # 1. Authorization (deny by default).
        if not self._policy.authorize(
            user_id=interaction.user_id,
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
        ):
            logger.warning(
                "discord_unauthorized",
                user=interaction.user_id,
                action=interaction.action,
            )
            return InteractionResult(
                ok=False,
                message="Vous n'êtes pas autorisé à effectuer cette action.",
                ephemeral=True,
            )

        # 2. Rate limiting.
        if not self._rate.allow(interaction.user_id):
            return InteractionResult(
                ok=False, message="Trop de requêtes, réessayez plus tard.", ephemeral=True
            )

        try:
            return await self._route(interaction)
        except DomainError as exc:
            return InteractionResult(ok=False, message=f"Action refusée: {exc}", ephemeral=True)

    async def _route(self, interaction: InboundInteraction) -> InteractionResult:
        action = interaction.action
        if action == "create_feature":
            return await self._create_feature(interaction)
        if action == "answer":
            return await self._answer(interaction)
        if action == "approve_scope":
            return await self._approve_scope(interaction)
        if action == "request_changes":
            return await self._request_changes(interaction)
        if action == "cancel":
            return await self._cancel(interaction)
        if action == "approve_staging":
            return await self._approve_staging(interaction)
        return InteractionResult(ok=False, message=f"Action inconnue: {action}", ephemeral=True)

    async def _create_feature(self, interaction: InboundInteraction) -> InteractionResult:
        extra = interaction.extra or {}
        async with SqlAlchemyUnitOfWork() as uow:
            projects = await uow.projects.list(slug=extra.get("project", "demo-app"), limit=1)
            if not projects:
                projects = await uow.projects.list(limit=1)
            if not projects:
                return InteractionResult(
                    ok=False, message="Aucun projet configuré.", ephemeral=True
                )
            feature = await self._features.create_feature(
                uow,
                project_id=projects[0].id,
                title=extra.get("title", "Nouvelle demande"),
                raw_request=extra.get("need", ""),
                source=FeatureSource.DISCORD,
                requester_id=interaction.user_id,
                priority=_priority(extra.get("priority")),
            )
            await self._features.analyze(uow, feature.id)
            await uow.commit()
            return InteractionResult(
                ok=True,
                message=f"Demande enregistrée et analysée (id {feature.id[:8]}).",
            )

    async def _answer(self, interaction: InboundInteraction) -> InteractionResult:
        if not interaction.target_id or interaction.value is None:
            return InteractionResult(ok=False, message="Réponse invalide.", ephemeral=True)
        async with SqlAlchemyUnitOfWork() as uow:
            # target_id binds the answer to the exact question — no ambiguity.
            await self._features.answer_question(
                uow, interaction.target_id, interaction.value, actor_id=interaction.user_id
            )
            await uow.commit()
        return InteractionResult(ok=True, message="Réponse enregistrée. Merci.")

    async def _approve_scope(self, interaction: InboundInteraction) -> InteractionResult:
        async with SqlAlchemyUnitOfWork() as uow:
            await self._features.approve_scope(
                uow, interaction.target_id or "", actor_id=interaction.user_id
            )
            await uow.commit()
        return InteractionResult(ok=True, message="Périmètre approuvé, issues en création.")

    async def _request_changes(self, interaction: InboundInteraction) -> InteractionResult:
        async with SqlAlchemyUnitOfWork() as uow:
            await self._features.request_changes(
                uow,
                interaction.target_id or "",
                interaction.value or "Modifications demandées.",
                actor_id=interaction.user_id,
            )
            await uow.commit()
        return InteractionResult(ok=True, message="Demande de modification enregistrée.")

    async def _cancel(self, interaction: InboundInteraction) -> InteractionResult:
        async with SqlAlchemyUnitOfWork() as uow:
            await self._features.cancel(
                uow, interaction.target_id or "", actor_id=interaction.user_id
            )
            await uow.commit()
        return InteractionResult(ok=True, message="Demande annulée.")

    async def _approve_staging(self, interaction: InboundInteraction) -> InteractionResult:
        async with SqlAlchemyUnitOfWork() as uow:
            deployment = await self._prs.approve_staging(
                uow, interaction.target_id or "", actor_id=interaction.user_id
            )
            await uow.commit()
        return InteractionResult(
            ok=True, message=f"Staging validé: {deployment.url or 'déploiement lancé'}."
        )


def _priority(value: str | None) -> Priority:
    try:
        return Priority(value) if value else Priority.MEDIUM
    except ValueError:
        return Priority.MEDIUM
