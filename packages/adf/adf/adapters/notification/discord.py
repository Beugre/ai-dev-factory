"""Discord notification gateways.

Two implementations:
- ``DiscordWebhookNotificationGateway``: uses a Discord incoming webhook URL
  (simpler, no bot setup required). Configure ``NOTIFICATION_GATEWAY=discord_webhook``
  and ``DISCORD_WEBHOOK_URL``.
- ``DiscordNotificationGateway``: uses a bot token + channel id. Configure
  ``NOTIFICATION_GATEWAY=discord`` and ``DISCORD_BOT_TOKEN``.
"""

from __future__ import annotations

import httpx

from adf.infrastructure.logging import get_logger
from adf.ports.notification_gateway import NotificationMessage, NotificationResult

logger = get_logger(__name__)

_API = "https://discord.com/api/v10"


class DiscordWebhookNotificationGateway:
    """Send notifications via a Discord incoming webhook URL.

    This is the recommended approach for simple notification use-cases: no bot
    registration or guild permissions required — just paste the webhook URL.
    """

    channel = "discord_webhook"

    def __init__(self, webhook_url: str) -> None:
        self._url = webhook_url

    async def send(self, message: NotificationMessage) -> NotificationResult:
        # Build a concise, mobile-readable Discord embed.
        embed = {
            "title": message.title[:256],
            "description": message.body[:4096],
            "color": _color_for_type(message.type),
        }
        if message.buttons:
            # Buttons are Discord components — not supported on webhooks.
            # Flatten them into the description so the user knows what to do.
            actions = " · ".join(f"`{b.label}`" for b in message.buttons)
            embed["footer"] = {"text": f"Actions disponibles : {actions}"}

        payload: dict[str, object] = {"embeds": [embed]}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._url, json=payload)
                resp.raise_for_status()
            logger.info("discord_webhook_sent", type=message.type)
            # Discord webhooks return 204 No Content on success
            external_id = resp.text.strip() or "sent"
            return NotificationResult(delivered=True, external_id=external_id)
        except httpx.HTTPError as exc:
            logger.warning("discord_webhook_failed", error=type(exc).__name__)
            return NotificationResult(delivered=False, error=type(exc).__name__)


class DiscordNotificationGateway:
    """Send notifications via the Discord REST API (bot token).

    Requires ``DISCORD_BOT_TOKEN`` and a target ``DISCORD_CHANNEL_ID``.
    """

    channel = "discord"

    def __init__(self, bot_token: str, default_channel_id: str | None = None) -> None:
        self._token = bot_token
        self._default_channel = default_channel_id

    async def send(self, message: NotificationMessage) -> NotificationResult:
        channel_id = message.recipient or self._default_channel
        if not channel_id:
            return NotificationResult(delivered=False, error="no channel id")
        content = f"**{message.title}**\n{message.body}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{_API}/channels/{channel_id}/messages",
                    headers={"Authorization": f"Bot {self._token}"},
                    json={"content": content[:1900]},
                )
                resp.raise_for_status()
            logger.info("discord_notification_sent", type=message.type)
            return NotificationResult(delivered=True, external_id=resp.json().get("id"))
        except httpx.HTTPError as exc:
            logger.warning("discord_notification_failed", error=type(exc).__name__)
            return NotificationResult(delivered=False, error=type(exc).__name__)


def _color_for_type(notification_type: str) -> int:
    """Return a Discord embed color integer for a notification type."""
    colors = {
        "clarification.needed": 0xF5B544,   # amber
        "scope.review": 0x5B8CFF,           # blue
        "pr.ready": 0x2FD47B,               # green
        "staging.deployed": 0x2FD47B,       # green
        "changes.requested": 0xF2555A,      # red
        "error": 0xF2555A,                  # red
    }
    return colors.get(notification_type, 0x5B8CFF)
