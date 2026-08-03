"""Port for executing agents with structured, validated output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from pydantic import BaseModel

from adf.domain.enums import AgentType

TOutput = TypeVar("TOutput", bound=BaseModel)


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.5


@dataclass(slots=True)
class AgentRequest:
    """A single agent invocation.

    ``context`` carries untrusted content (issue bodies, comments, user text).
    Implementations MUST treat it as data, never as instructions that can
    override ``instructions`` / role.
    """

    role: AgentType
    instructions: str
    context: dict[str, object]
    correlation_id: str
    timeout_seconds: float = 60.0
    retry: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass(slots=True)
class AgentResult:
    output_summary: str
    provider: str
    model: str
    tokens_input: int | None = None
    tokens_output: int | None = None
    raw: dict[str, object] = field(default_factory=dict)


class AgentRuntime(Protocol):
    """Executes an agent request and returns validated structured output."""

    provider: str

    async def run(
        self,
        request: AgentRequest,
        output_model: type[TOutput],
    ) -> tuple[TOutput, AgentResult]:
        """Run the agent and parse the result into ``output_model``.

        Raises on validation failure so callers never persist malformed output.
        """
        ...
