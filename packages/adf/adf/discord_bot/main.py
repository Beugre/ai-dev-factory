"""Discord bot entrypoint."""

from __future__ import annotations

from adf.config import get_settings
from adf.infrastructure.logging import get_logger

logger = get_logger("adf.discord")


def main() -> None:
    settings = get_settings()
    if not settings.discord_bot_token:
        logger.warning(
            "discord_disabled",
            reason="DISCORD_BOT_TOKEN non configuré; le bot reste inactif.",
        )
        return
    from adf.discord_bot.client import run

    run()


if __name__ == "__main__":
    main()
