"""Discord authorization: allowlists, channel/guild checks, rate limiting."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class DiscordSecurityPolicy:
    allowed_user_ids: frozenset[str]
    allowed_guild_id: str | None = None
    allowed_channel_id: str | None = None

    def is_user_allowed(self, user_id: str) -> bool:
        # Empty allowlist => deny everyone (secure default).
        return user_id in self.allowed_user_ids

    def is_guild_allowed(self, guild_id: str | None) -> bool:
        if self.allowed_guild_id is None:
            return True
        return guild_id == self.allowed_guild_id

    def is_channel_allowed(self, channel_id: str | None) -> bool:
        if self.allowed_channel_id is None:
            return True
        return channel_id == self.allowed_channel_id

    def authorize(
        self, *, user_id: str, guild_id: str | None, channel_id: str | None
    ) -> bool:
        return (
            self.is_user_allowed(user_id)
            and self.is_guild_allowed(guild_id)
            and self.is_channel_allowed(channel_id)
        )


@dataclass
class RateLimiter:
    """Simple fixed-window per-user rate limiter."""

    max_calls: int = 5
    window_seconds: float = 10.0
    _calls: dict[str, list[float]] = field(default_factory=dict)

    def allow(self, user_id: str, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        window_start = now - self.window_seconds
        calls = [t for t in self._calls.get(user_id, []) if t >= window_start]
        if len(calls) >= self.max_calls:
            self._calls[user_id] = calls
            return False
        calls.append(now)
        self._calls[user_id] = calls
        return True
