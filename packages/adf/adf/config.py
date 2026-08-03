"""Application configuration loaded from the environment.

Secrets are never hardcoded. All values come from environment variables (see
``.env.example``). This module is the single place that reads configuration so
the rest of the code depends on typed settings, not on ``os.environ``.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentRuntimeKind(StrEnum):
    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai_compatible"
    GITHUB_AGENTIC = "github_agentic"


class NotificationGatewayKind(StrEnum):
    MOCK = "mock"
    DISCORD = "discord"
    DISCORD_WEBHOOK = "discord_webhook"


class DeploymentMode(StrEnum):
    MOCK = "mock"
    LOCAL = "local"
    WEBHOOK = "webhook"


class CopilotDispatchMode(StrEnum):
    AGENT_TASKS_API = "agent_tasks_api"
    ISSUE_ASSIGNMENT = "issue_assignment"
    MANUAL = "manual"


class Settings(BaseSettings):
    """Typed application settings.

    The defaults keep the *mock* mode fully functional without any external
    account, which is what powers ``make demo`` and the test-suite.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # Application
    app_env: str = "local"
    app_base_url: str = "http://localhost:5173"
    api_base_url: str = "http://localhost:8000"
    secret_key: str = "insecure-dev-secret-change-me"

    # Datastores. SQLite is the safe default so tests run with zero services.
    database_url: str = "sqlite+aiosqlite:///./adf.db"
    redis_url: str = "redis://localhost:6379/0"

    # GitHub
    github_owner: str = "acme"
    github_target_repo: str = "demo-repo"
    github_default_branch: str = "main"
    github_webhook_secret: str = "dev-webhook-secret"
    github_app_id: str | None = None
    github_app_private_key_path: str | None = None
    github_installation_id: str | None = None
    github_user_token: str | None = None
    copilot_dispatch_mode: CopilotDispatchMode = CopilotDispatchMode.MANUAL
    copilot_custom_agent: str = "developer"
    copilot_model: str | None = None

    # Discord
    discord_bot_token: str | None = None
    discord_application_id: str | None = None
    discord_guild_id: str | None = None
    discord_channel_id: str | None = None
    discord_allowed_user_ids: str = ""
    discord_webhook_url: str | None = None

    # Agent runtime
    agent_runtime: AgentRuntimeKind = AgentRuntimeKind.MOCK
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"

    # Deployment
    deployment_mode: DeploymentMode = DeploymentMode.MOCK
    staging_base_url: str = "http://localhost:8080"
    staging_deploy_webhook_url: str | None = None

    # n8n
    n8n_base_url: str | None = None
    n8n_webhook_secret: str | None = None

    # Observability
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str | None = None
    metrics_token: str | None = None

    # Notifications
    notification_gateway: NotificationGatewayKind = NotificationGatewayKind.MOCK

    @property
    def discord_allowed_ids(self) -> frozenset[str]:
        return frozenset(x.strip() for x in self.discord_allowed_user_ids.split(",") if x.strip())

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
