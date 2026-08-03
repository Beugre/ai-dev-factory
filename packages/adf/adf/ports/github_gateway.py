"""Port for GitHub interactions (issues, PRs, checks, dispatch, webhooks)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class IssueRef:
    number: int
    url: str
    node_id: str | None = None


@dataclass(slots=True)
class PullRequestInfo:
    number: int
    url: str
    title: str
    branch: str
    state: str
    ci_state: str
    review_state: str
    mergeable: bool | None
    preview_url: str | None = None


@dataclass(slots=True)
class DispatchResult:
    """Outcome of dispatching a story to a coding agent.

    ``confirmed`` is only ``True`` when GitHub actually acknowledged the
    assignment. We never claim success otherwise.
    """

    mode: str
    confirmed: bool
    detail: str
    issue: IssueRef | None = None


class GitHubGateway(Protocol):
    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> IssueRef: ...

    async def update_issue(
        self,
        repo: str,
        number: int,
        *,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> IssueRef: ...

    async def add_labels(self, repo: str, number: int, labels: list[str]) -> None: ...

    async def assign_issue(
        self, repo: str, number: int, assignees: list[str]
    ) -> list[str]:
        """Assign users/bots to an issue. Returns the confirmed assignee list."""
        ...

    async def get_issue(self, repo: str, number: int) -> dict[str, object]: ...

    async def get_pull_request(self, repo: str, number: int) -> PullRequestInfo: ...

    async def comment_on_pull_request(
        self, repo: str, number: int, body: str
    ) -> None: ...

    async def get_check_runs(self, repo: str, ref: str) -> list[dict[str, object]]: ...


class CopilotDispatcher(Protocol):
    """Strategy that assigns development of a story to a coding agent."""

    mode: str

    async def dispatch(
        self,
        repo: str,
        issue: IssueRef,
        *,
        base_branch: str,
        instructions: str,
        custom_agent: str | None = None,
        model: str | None = None,
    ) -> DispatchResult: ...


class WebhookVerifier(Protocol):
    def verify(self, payload: bytes, signature: str | None) -> bool: ...
