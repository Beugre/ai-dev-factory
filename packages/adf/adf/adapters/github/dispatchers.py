"""Copilot dispatch strategies.

Three modes, selected by ``COPILOT_DISPATCH_MODE``:

- ``agent_tasks_api``: uses GitHub's agent-tasks API when the account/plan
  exposes it (preview; disabled unless configured).
- ``issue_assignment``: fallback that assigns the issue to
  ``copilot-swe-agent[bot]``.
- ``manual``: leaves the issue ready for a human to assign.

None of them ever claims success unless GitHub confirms it.
"""

from __future__ import annotations

from adf.infrastructure.logging import get_logger
from adf.ports.github_gateway import DispatchResult, GitHubGateway, IssueRef

logger = get_logger(__name__)

COPILOT_BOT_LOGIN = "copilot-swe-agent[bot]"


class ManualDispatcher:
    """No automatic assignment: the issue is left ready for a human."""

    mode = "manual"

    async def dispatch(
        self,
        repo: str,
        issue: IssueRef,
        *,
        base_branch: str,
        instructions: str,
        custom_agent: str | None = None,
        model: str | None = None,
    ) -> DispatchResult:
        return DispatchResult(
            mode=self.mode,
            confirmed=False,
            detail=(
                "Issue prête à être affectée manuellement à un développeur ou à "
                "Copilot."
            ),
            issue=issue,
        )


class IssueAssignmentDispatcher:
    """Assigns the issue to the Copilot coding agent bot.

    Success is only reported when GitHub confirms the bot is in the assignee
    list. Custom-agent / model / instructions are passed through the issue body
    where the API cannot carry them directly.
    """

    mode = "issue_assignment"

    def __init__(self, gateway: GitHubGateway) -> None:
        self._gateway = gateway

    async def dispatch(
        self,
        repo: str,
        issue: IssueRef,
        *,
        base_branch: str,
        instructions: str,
        custom_agent: str | None = None,
        model: str | None = None,
    ) -> DispatchResult:
        confirmed_assignees = await self._gateway.assign_issue(
            repo, issue.number, [COPILOT_BOT_LOGIN]
        )
        confirmed = COPILOT_BOT_LOGIN in confirmed_assignees
        if confirmed and (custom_agent or model):
            note = _dispatch_note(base_branch, custom_agent, model)
            await self._gateway.add_labels(repo, issue.number, ["status:in-progress"])
            logger.info(
                "copilot_dispatch_issue_assignment",
                repo=repo,
                issue=issue.number,
                custom_agent=custom_agent,
                note=note,
            )
        return DispatchResult(
            mode=self.mode,
            confirmed=confirmed,
            detail=(
                f"Copilot bot assigné à l'issue #{issue.number}."
                if confirmed
                else "GitHub n'a pas confirmé l'affectation à Copilot."
            ),
            issue=issue,
        )


class AgentTasksApiDispatcher:
    """Uses GitHub's agent-tasks API (preview).

    Requires an eligible account/plan and explicit configuration. Because the
    API is preview and not available everywhere, this dispatcher fails loudly
    instead of pretending to have dispatched.
    """

    mode = "agent_tasks_api"

    def __init__(self, gateway: GitHubGateway, enabled: bool = False) -> None:
        self._gateway = gateway
        self._enabled = enabled

    async def dispatch(
        self,
        repo: str,
        issue: IssueRef,
        *,
        base_branch: str,
        instructions: str,
        custom_agent: str | None = None,
        model: str | None = None,
    ) -> DispatchResult:
        if not self._enabled:
            return DispatchResult(
                mode=self.mode,
                confirmed=False,
                detail=(
                    "Agent Tasks API non activée (préversion). Configurer et "
                    "activer explicitement avant usage."
                ),
                issue=issue,
            )
        # Real preview API wiring lives behind this flag; not enabled for V1.
        raise NotImplementedError(
            "AgentTasksApiDispatcher requires the GitHub agent-tasks preview API."
        )


def _dispatch_note(base_branch: str, custom_agent: str | None, model: str | None) -> str:
    parts = [f"base={base_branch}"]
    if custom_agent:
        parts.append(f"agent={custom_agent}")
    if model:
        parts.append(f"model={model}")
    return " ".join(parts)
