"""Real GitHub gateway: retry, rate-limit handling and secret-free logging."""

from __future__ import annotations

import httpx
import respx
from adf.adapters.github.real import RealGitHubGateway


@respx.mock
async def test_retry_after_rate_limit() -> None:
    route = respx.post("https://api.github.com/repos/acme/demo-repo/issues")
    route.side_effect = [
        httpx.Response(
            403,
            headers={"X-RateLimit-Remaining": "0", "Retry-After": "0"},
            json={"message": "rate limited"},
        ),
        httpx.Response(
            201,
            json={
                "number": 7,
                "html_url": "https://github.com/acme/demo-repo/issues/7",
                "node_id": "I_7",
            },
        ),
    ]
    gateway = RealGitHubGateway("token", owner="acme", backoff_seconds=0.0)
    issue = await gateway.create_issue("demo-repo", "Title", "Body")
    assert issue.number == 7
    assert route.call_count == 2


@respx.mock
async def test_retry_on_server_error() -> None:
    route = respx.post("https://api.github.com/repos/acme/demo-repo/issues")
    route.side_effect = [
        httpx.Response(500, json={"message": "boom"}),
        httpx.Response(
            201,
            json={"number": 8, "html_url": "https://x/8", "node_id": "I_8"},
        ),
    ]
    gateway = RealGitHubGateway("token", owner="acme", backoff_seconds=0.0)
    issue = await gateway.create_issue("demo-repo", "T", "B")
    assert issue.number == 8


@respx.mock
async def test_token_never_logged(capsys) -> None:  # type: ignore[no-untyped-def]
    respx.post("https://api.github.com/repos/acme/demo-repo/issues").mock(
        return_value=httpx.Response(
            201, json={"number": 1, "html_url": "https://x/1", "node_id": "I_1"}
        )
    )
    secret = "ghp_supersecrettoken"
    gateway = RealGitHubGateway(secret, owner="acme", backoff_seconds=0.0)
    await gateway.create_issue("demo-repo", "T", "B")
    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err
