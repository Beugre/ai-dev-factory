"""Experimental GitHub agentic runtime (feature-flagged, off by default).

GitHub's agentic task APIs are, at the time of writing, in preview and not
universally available. This adapter is intentionally a thin, clearly-guarded
stub: it must be explicitly enabled and it never silently pretends to work.
Local development and the demo NEVER depend on it.

See docs/architecture/github-integration.md for activation details.
"""

from __future__ import annotations

from adf.ports.agent_runtime import AgentRequest, AgentResult, TOutput


class GitHubAgenticRuntime:
    provider = "github_agentic"

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    async def run(
        self,
        request: AgentRequest,
        output_model: type[TOutput],
    ) -> tuple[TOutput, AgentResult]:
        raise NotImplementedError(
            "GitHubAgenticRuntime is an experimental, preview-only integration. "
            "It is disabled by default and not implemented for V1. Use "
            "AGENT_RUNTIME=mock or openai_compatible. See "
            "docs/architecture/github-integration.md."
        )
