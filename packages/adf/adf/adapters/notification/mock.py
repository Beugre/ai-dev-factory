"""In-memory notification gateway for demo and tests."""

from __future__ import annotations

from adf.ports.notification_gateway import (
    NotificationMessage,
    NotificationResult,
)


class MockNotificationGateway:
    channel = "mock"

    def __init__(self) -> None:
        self.sent: list[NotificationMessage] = []

    async def send(self, message: NotificationMessage) -> NotificationResult:
        self.sent.append(message)
        return NotificationResult(delivered=True, external_id=f"mock-{len(self.sent)}")
