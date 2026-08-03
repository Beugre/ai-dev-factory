"""Port for outbound notifications (Discord, etc.)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class NotificationButton:
    label: str
    action: str
    value: str
    style: str = "primary"


@dataclass(slots=True)
class NotificationMessage:
    channel: str
    recipient: str
    type: str
    title: str
    body: str
    ephemeral: bool = False
    buttons: list[NotificationButton] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class NotificationResult:
    delivered: bool
    external_id: str | None = None
    error: str | None = None


class NotificationGateway(Protocol):
    channel: str

    async def send(self, message: NotificationMessage) -> NotificationResult: ...
