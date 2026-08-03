"""Copilot dispatch strategies: mock confirmation and manual fallback."""

from __future__ import annotations

from adf.adapters.github.dispatchers import (
    COPILOT_BOT_LOGIN,
    IssueAssignmentDispatcher,
    ManualDispatcher,
)
from adf.adapters.github.mock import MockGitHubGateway
from adf.ports.github_gateway import IssueRef


async def test_issue_assignment_confirmed() -> None:
    gateway = MockGitHubGateway()
    issue = await gateway.create_issue("demo-repo", "Story", "body")
    dispatcher = IssueAssignmentDispatcher(gateway)
    result = await dispatcher.dispatch(
        "demo-repo",
        issue,
        base_branch="main",
        instructions="do it",
        custom_agent="developer",
    )
    assert result.confirmed is True
    assert result.mode == "issue_assignment"
    assert COPILOT_BOT_LOGIN in gateway.issues[issue.number]["assignees"]


async def test_manual_dispatcher_never_claims_success() -> None:
    dispatcher = ManualDispatcher()
    result = await dispatcher.dispatch(
        "demo-repo",
        IssueRef(number=1, url="https://x/1"),
        base_branch="main",
        instructions="",
    )
    assert result.confirmed is False
    assert result.mode == "manual"


async def test_agent_tasks_api_disabled_by_default() -> None:
    from adf.adapters.github.dispatchers import AgentTasksApiDispatcher

    gateway = MockGitHubGateway()
    dispatcher = AgentTasksApiDispatcher(gateway, enabled=False)
    result = await dispatcher.dispatch(
        "demo-repo",
        IssueRef(number=1, url="https://x/1"),
        base_branch="main",
        instructions="",
    )
    assert result.confirmed is False
