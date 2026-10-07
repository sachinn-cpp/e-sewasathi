"""Ollama chat completion adapter (optional, disabled in demo tests)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.integrations.llm.base import LLMClient, LLMReply
from app.integrations.llm.demo_llm_client import DemoLLMClient, detect_intent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are e-SewaSathi, a helpful assistant that guides citizens through "
    "government service applications. Be concise, safe and honest. Never claim "
    "an action was performed unless the application state says so. Reply in "
    "the user's language (English, Hindi or Nepali)."
)


class OllamaLLMClient(LLMClient):
    """Talks to a local Ollama server with a short timeout and safe fallback."""

    provider = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        language: str = "en",
        context: dict[str, Any] | None = None,
    ) -> LLMReply:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": _SYSTEM_PROMPT}]
            + [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in messages[-20:]
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
            text = str(body.get("message", {}).get("content", "")).strip()
            if not text:
                raise ValueError("empty completion")
            return LLMReply(
                text=text, intent="assistant", provider="ollama", model=self.model
            )
        except Exception as exc:  # noqa: BLE001 - fall back to safe demo replies
            logger.warning("Ollama completion failed: %s", type(exc).__name__)
            reply = DemoLLMClient().complete(
                messages, language=language, context=context
            )
            reply.meta["fallback"] = "ollama_unavailable"
            return reply
