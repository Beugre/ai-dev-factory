"""discord.py transport wiring the slash commands to the InteractionRouter.

Imported lazily so the rest of the package (and the tests) do not require
``discord.py`` to be installed.
"""

from __future__ import annotations

from adf.application.container import build_container
from adf.config import get_settings
from adf.discord_bot.interactions import (
    InboundInteraction,
    InteractionRouter,
)
from adf.discord_bot.security import DiscordSecurityPolicy, RateLimiter
from adf.infrastructure.logging import get_logger

logger = get_logger("adf.discord")


def build_router() -> InteractionRouter:
    settings = get_settings()
    policy = DiscordSecurityPolicy(
        allowed_user_ids=settings.discord_allowed_ids,
        allowed_guild_id=settings.discord_guild_id,
        allowed_channel_id=settings.discord_channel_id,
    )
    return InteractionRouter(build_container(), policy, RateLimiter())


def run() -> None:  # pragma: no cover - requires a real token + gateway
    import discord
    from discord import app_commands

    settings = get_settings()
    if not settings.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN manquant: le bot ne peut pas démarrer.")

    router = build_router()
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    def _ctx(interaction: discord.Interaction) -> InboundInteraction:
        return InboundInteraction(
            action="",
            user_id=str(interaction.user.id),
            guild_id=str(interaction.guild_id) if interaction.guild_id else None,
            channel_id=str(interaction.channel_id) if interaction.channel_id else None,
        )

    @tree.command(name="help", description="Afficher l'aide")
    async def help_cmd(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "Commandes: /feature /status /approve /request-changes /pause /resume",
            ephemeral=True,
        )

    @tree.command(name="feature", description="Créer une nouvelle demande")
    @app_commands.describe(titre="Titre", besoin="Besoin", priorite="Priorité")
    async def feature_cmd(
        interaction: discord.Interaction,
        titre: str,
        besoin: str,
        priorite: str = "medium",
    ) -> None:
        base = _ctx(interaction)
        base.action = "create_feature"
        base.extra = {"title": titre, "need": besoin, "priority": priorite}
        result = await router.handle(base)
        await interaction.response.send_message(result.message, ephemeral=result.ephemeral)

    @tree.command(name="approve", description="Approuver un périmètre")
    async def approve_cmd(interaction: discord.Interaction, feature_id: str) -> None:
        base = _ctx(interaction)
        base.action = "approve_scope"
        base.target_id = feature_id
        result = await router.handle(base)
        await interaction.response.send_message(result.message, ephemeral=result.ephemeral)

    @client.event
    async def on_ready() -> None:
        await tree.sync()
        logger.info("discord_ready", user=str(client.user))

    client.run(settings.discord_bot_token)
