"""OpenAI-compatible agent runtime.

Works with any endpoint implementing the Chat Completions API (OpenAI, Azure
OpenAI, Ollama, vLLM, ...). Disabled unless ``AGENT_RUNTIME=openai_compatible``
and ``LLM_API_KEY`` is set. Output is JSON, validated by Pydantic — malformed
output raises rather than being persisted.
"""

from __future__ import annotations

import json

import httpx

from adf.agent_runtime.prompt_loader import UNTRUSTED_CONTENT_GUARD, wrap_untrusted
from adf.config import get_settings
from adf.infrastructure.logging import get_logger
from adf.ports.agent_runtime import AgentRequest, AgentResult, TOutput

logger = get_logger(__name__)


class OpenAICompatibleAgentRuntime:
    provider = "openai_compatible"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.llm_base_url).rstrip("/")
        self._api_key = api_key or settings.llm_api_key
        self._model = model or settings.llm_model
        if not self._api_key:
            raise ValueError("LLM_API_KEY is required for OpenAICompatibleAgentRuntime")

    async def run(
        self,
        request: AgentRequest,
        output_model: type[TOutput],
    ) -> tuple[TOutput, AgentResult]:
        system = request.instructions + UNTRUSTED_CONTENT_GUARD
        schema = json.dumps(output_model.model_json_schema())
        user = (
            f"{wrap_untrusted(request.context)}\n\n"
            f"Respond with ONLY valid JSON matching this JSON schema:\n{schema}"
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        last_exc: Exception | None = None
        for attempt in range(request.retry.max_attempts):
            try:
                async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self._api_key}"},
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                content = data["choices"][0]["message"]["content"]
                output = output_model.model_validate_json(content)
                usage = data.get("usage", {})
                result = AgentResult(
                    output_summary=f"{output_model.__name__} produced",
                    provider=self.provider,
                    model=self._model,
                    tokens_input=usage.get("prompt_tokens"),
                    tokens_output=usage.get("completion_tokens"),
                    raw={"attempt": attempt + 1},
                )
                return output, result
            except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
                last_exc = exc
                logger.warning(
                    "agent_runtime_retry",
                    attempt=attempt + 1,
                    error=type(exc).__name__,
                )
        raise RuntimeError(
            f"OpenAICompatibleAgentRuntime failed after "
            f"{request.retry.max_attempts} attempts"
        ) from last_exc
