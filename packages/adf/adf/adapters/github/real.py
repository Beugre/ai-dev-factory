"""Real GitHub REST gateway (httpx).

Enabled only when a token is configured. Handles rate limits with retry and
never logs secrets. Used in production; the demo/tests use the mock gateway.
"""

from __future__ import annotations

import asyncio

import httpx

from adf.infrastructure.logging import get_logger
from adf.ports.github_gateway import IssueRef, PullRequestInfo

logger = get_logger(__name__)

_API = "https://api.github.com"


class GitHubApiError(RuntimeError):
    pass


class RealGitHubGateway:
    def __init__(
        self,
        token: str,
        *,
        owner: str,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self._token = token
        self._owner = owner
        self._max_retries = max_retries
        self._backoff = backoff_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _slug(self, repo: str) -> str:
        return repo if "/" in repo else f"{self._owner}/{repo}"

    async def _request(
        self, method: str, path: str, json: dict[str, object] | None = None
    ) -> httpx.Response:
        url = f"{_API}{path}"
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.request(
                        method, url, headers=self._headers(), json=json
                    )
                if resp.status_code == 403 and _is_rate_limited(resp):
                    wait = _rate_limit_wait(resp, self._backoff * (2**attempt))
                    logger.warning("github_rate_limited", path=path, wait=wait)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    await asyncio.sleep(self._backoff * (2**attempt))
                    continue
                resp.raise_for_status()
                # Log without secrets: only method/path/status.
                logger.info("github_call", method=method, path=path, status=resp.status_code)
                return resp
            except httpx.HTTPStatusError as exc:
                raise GitHubApiError(f"{method} {path} -> {exc.response.status_code}") from exc
            except httpx.HTTPError as exc:
                last_exc = exc
                await asyncio.sleep(self._backoff * (2**attempt))
        raise GitHubApiError(f"{method} {path} failed after retries") from last_exc

    async def create_issue(
        self, repo: str, title: str, body: str, labels: list[str] | None = None
    ) -> IssueRef:
        resp = await self._request(
            "POST",
            f"/repos/{self._slug(repo)}/issues",
            {"title": title, "body": body, "labels": labels or []},
        )
        data = resp.json()
        return IssueRef(number=data["number"], url=data["html_url"], node_id=data.get("node_id"))

    async def update_issue(
        self,
        repo: str,
        number: int,
        *,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> IssueRef:
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        resp = await self._request(
            "PATCH", f"/repos/{self._slug(repo)}/issues/{number}", payload
        )
        data = resp.json()
        return IssueRef(number=data["number"], url=data["html_url"])

    async def add_labels(self, repo: str, number: int, labels: list[str]) -> None:
        await self._request(
            "POST",
            f"/repos/{self._slug(repo)}/issues/{number}/labels",
            {"labels": labels},
        )

    async def assign_issue(
        self, repo: str, number: int, assignees: list[str]
    ) -> list[str]:
        resp = await self._request(
            "POST",
            f"/repos/{self._slug(repo)}/issues/{number}/assignees",
            {"assignees": assignees},
        )
        data = resp.json()
        return [a["login"] for a in data.get("assignees", [])]

    async def get_issue(self, repo: str, number: int) -> dict[str, object]:
        resp = await self._request("GET", f"/repos/{self._slug(repo)}/issues/{number}")
        return dict(resp.json())

    async def get_pull_request(self, repo: str, number: int) -> PullRequestInfo:
        resp = await self._request("GET", f"/repos/{self._slug(repo)}/pulls/{number}")
        data = resp.json()
        return PullRequestInfo(
            number=data["number"],
            url=data["html_url"],
            title=data["title"],
            branch=data["head"]["ref"],
            state=data["state"],
            ci_state="unknown",
            review_state="pending",
            mergeable=data.get("mergeable"),
        )

    async def comment_on_pull_request(self, repo: str, number: int, body: str) -> None:
        await self._request(
            "POST",
            f"/repos/{self._slug(repo)}/issues/{number}/comments",
            {"body": body},
        )

    async def get_check_runs(self, repo: str, ref: str) -> list[dict[str, object]]:
        resp = await self._request(
            "GET", f"/repos/{self._slug(repo)}/commits/{ref}/check-runs"
        )
        return list(resp.json().get("check_runs", []))


def _is_rate_limited(resp: httpx.Response) -> bool:
    return resp.headers.get("X-RateLimit-Remaining") == "0"


def _rate_limit_wait(resp: httpx.Response, default: float) -> float:
    retry_after = resp.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return float(retry_after)
    return default
