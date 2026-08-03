"""In-memory GitHub gateway for demo and tests.

Deterministic issue/PR numbers, no network. Fully implements the
:class:`GitHubGateway` protocol.
"""

from __future__ import annotations

import itertools
from typing import cast

from adf.ports.github_gateway import IssueRef, PullRequestInfo


class MockGitHubGateway:
    def __init__(self, owner: str = "acme", repo: str = "demo-repo") -> None:
        self._owner = owner
        self._repo = repo
        self._issue_seq = itertools.count(1)
        self._pr_seq = itertools.count(1)
        self.issues: dict[int, dict[str, object]] = {}
        self.pull_requests: dict[int, PullRequestInfo] = {}
        self.comments: dict[int, list[str]] = {}

    def _repo_slug(self, repo: str) -> str:
        return repo if "/" in repo else f"{self._owner}/{repo}"

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> IssueRef:
        number = next(self._issue_seq)
        slug = self._repo_slug(repo)
        self.issues[number] = {
            "number": number,
            "title": title,
            "body": body,
            "labels": list(labels or []),
            "state": "open",
            "assignees": [],
        }
        return IssueRef(
            number=number,
            url=f"https://github.com/{slug}/issues/{number}",
            node_id=f"I_mock_{number}",
        )

    async def update_issue(
        self,
        repo: str,
        number: int,
        *,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> IssueRef:
        issue = self.issues.setdefault(number, {"number": number, "labels": []})
        if title is not None:
            issue["title"] = title
        if body is not None:
            issue["body"] = body
        if state is not None:
            issue["state"] = state
        slug = self._repo_slug(repo)
        return IssueRef(number=number, url=f"https://github.com/{slug}/issues/{number}")

    async def add_labels(self, repo: str, number: int, labels: list[str]) -> None:
        issue = self.issues.setdefault(number, {"number": number, "labels": []})
        existing = set(cast(list[str], issue.get("labels", [])))
        issue["labels"] = sorted(existing | set(labels))

    async def assign_issue(
        self, repo: str, number: int, assignees: list[str]
    ) -> list[str]:
        issue = self.issues.setdefault(number, {"number": number, "assignees": []})
        current = set(cast(list[str], issue.get("assignees", [])))
        current |= set(assignees)
        confirmed = sorted(current)
        issue["assignees"] = confirmed
        return confirmed

    async def get_issue(self, repo: str, number: int) -> dict[str, object]:
        return self.issues.get(number, {"number": number, "state": "unknown"})

    async def get_pull_request(self, repo: str, number: int) -> PullRequestInfo:
        return self.pull_requests[number]

    async def comment_on_pull_request(self, repo: str, number: int, body: str) -> None:
        self.comments.setdefault(number, []).append(body)

    async def get_check_runs(self, repo: str, ref: str) -> list[dict[str, object]]:
        return [{"name": "ci", "status": "completed", "conclusion": "success"}]

    # --- test/demo helpers (not part of the port) ------------------------
    def open_pull_request(
        self,
        *,
        title: str,
        branch: str,
        story_number: int,
        ci_state: str = "success",
        review_state: str = "pending",
        preview_url: str | None = None,
    ) -> PullRequestInfo:
        number = next(self._pr_seq)
        slug = self._repo_slug(self._repo)
        info = PullRequestInfo(
            number=number,
            url=f"https://github.com/{slug}/pull/{number}",
            title=title,
            branch=branch,
            state="open",
            ci_state=ci_state,
            review_state=review_state,
            mergeable=ci_state == "success",
            preview_url=preview_url,
        )
        self.pull_requests[number] = info
        return info

    def assign_issue_sync(self, number: int, login: str) -> None:
        issue = self.issues.setdefault(number, {"number": number, "assignees": []})
        assignees = set(cast(list[str], issue.get("assignees", [])))
        assignees.add(login)
        issue["assignees"] = sorted(assignees)
