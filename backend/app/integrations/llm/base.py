"""LLM adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable


@dataclass
class LLMReply:
    """Result of one chat completion."""

    text: str
    intent: str = "fallback"
    provider: str = "demo"
    model: str = ""
    safe: bool = True
    meta: dict[str, Any] = field(default_factory=dict)


class LLMClient(ABC):
    """Chat completion adapter. Implementations must never leak secrets."""

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        language: str = "en",
        context: dict[str, Any] | None = None,
    ) -> LLMReply | Awaitable[LLMReply]:
        """Return a reply (implementations may be sync or async)."""
