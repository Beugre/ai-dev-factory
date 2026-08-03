"""Composition root: selects adapter implementations from configuration.

This is the only place that decides mock vs real. The rest of the code depends
on ports, never on concrete adapters.
"""

from __future__ import annotations

from dataclasses import dataclass

from adf.adapters.agent_runtime.mock import MockAgentRuntime
from adf.adapters.deployment.gateways import build_deployment_gateway
from adf.adapters.github.dispatchers import (
    AgentTasksApiDispatcher,
    IssueAssignmentDispatcher,
    ManualDispatcher,
)
from adf.adapters.github.mock import MockGitHubGateway
from adf.adapters.github.webhooks import GitHubWebhookVerifier
from adf.adapters.notification.mock import MockNotificationGateway
from adf.config import (
    AgentRuntimeKind,
    CopilotDispatchMode,
    NotificationGatewayKind,
    Settings,
    get_settings,
)
from adf.ports.agent_runtime import AgentRuntime
from adf.ports.deployment_gateway import DeploymentGateway
from adf.ports.github_gateway import CopilotDispatcher, GitHubGateway, WebhookVerifier
from adf.ports.notification_gateway import NotificationGateway


@dataclass(slots=True)
class Container:
    settings: Settings
    agent_runtime: AgentRuntime
    github: GitHubGateway
    dispatcher: CopilotDispatcher
    notifications: NotificationGateway
    deployment: DeploymentGateway
    webhook_verifier: WebhookVerifier


def _build_agent_runtime(settings: Settings) -> AgentRuntime:
    if settings.agent_runtime == AgentRuntimeKind.OPENAI_COMPATIBLE and settings.llm_api_key:
        from adf.adapters.agent_runtime.openai_compatible import (
            OpenAICompatibleAgentRuntime,
        )

        return OpenAICompatibleAgentRuntime()
    if settings.agent_runtime == AgentRuntimeKind.GITHUB_AGENTIC:
        from adf.adapters.agent_runtime.github_agentic import GitHubAgenticRuntime

        return GitHubAgenticRuntime(enabled=False)
    return MockAgentRuntime()


def _build_github(settings: Settings) -> GitHubGateway:
    if settings.github_user_token:
        from adf.adapters.github.real import RealGitHubGateway

        return RealGitHubGateway(settings.github_user_token, owner=settings.github_owner)
    return MockGitHubGateway(owner=settings.github_owner, repo=settings.github_target_repo)


def _build_dispatcher(settings: Settings, github: GitHubGateway) -> CopilotDispatcher:
    mode = settings.copilot_dispatch_mode
    if mode == CopilotDispatchMode.ISSUE_ASSIGNMENT:
        return IssueAssignmentDispatcher(github)
    if mode == CopilotDispatchMode.AGENT_TASKS_API:
        return AgentTasksApiDispatcher(github, enabled=False)
    return ManualDispatcher()


def _build_notifications(settings: Settings) -> NotificationGateway:
    if (
        settings.notification_gateway == NotificationGatewayKind.DISCORD_WEBHOOK
        and settings.discord_webhook_url
    ):
        from adf.adapters.notification.discord import DiscordWebhookNotificationGateway

        return DiscordWebhookNotificationGateway(settings.discord_webhook_url)
    if (
        settings.notification_gateway == NotificationGatewayKind.DISCORD
        and settings.discord_bot_token
    ):
        from adf.adapters.notification.discord import DiscordNotificationGateway

        return DiscordNotificationGateway(
            settings.discord_bot_token, settings.discord_channel_id
        )
    return MockNotificationGateway()


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()
    github = _build_github(settings)
    return Container(
        settings=settings,
        agent_runtime=_build_agent_runtime(settings),
        github=github,
        dispatcher=_build_dispatcher(settings, github),
        notifications=_build_notifications(settings),
        deployment=build_deployment_gateway(),
        webhook_verifier=GitHubWebhookVerifier(settings.github_webhook_secret),
    )


def build_mock_container(settings: Settings | None = None) -> Container:
    """A fully mock container, used by the demo and tests."""
    settings = settings or get_settings()
    github = MockGitHubGateway(owner=settings.github_owner, repo=settings.github_target_repo)
    from adf.adapters.deployment.gateways import MockDeploymentGateway

    return Container(
        settings=settings,
        agent_runtime=MockAgentRuntime(),
        github=github,
        dispatcher=IssueAssignmentDispatcher(github),
        notifications=MockNotificationGateway(),
        deployment=MockDeploymentGateway(settings.staging_base_url),
        webhook_verifier=GitHubWebhookVerifier(settings.github_webhook_secret),
    )
