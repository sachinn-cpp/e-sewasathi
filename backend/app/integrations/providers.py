"""Integration package: external service adapters and provider registry."""

from __future__ import annotations

from typing import Any

from app.config import get_settings

_overrides: dict[str, Any] = {}

LLM = "llm"
OCR = "ocr"
PORTAL = "portal"
STT = "stt"
TTS = "tts"


def override_provider(name: str, client: Any) -> None:
    """Replace a provider (used by tests and demo tooling)."""
    _overrides[name] = client


def clear_provider_overrides() -> None:
    _overrides.clear()


def _has_override(name: str) -> bool:
    return name in _overrides


def get_llm_client() -> Any:
    if _has_override(LLM):
        return _overrides[LLM]
    settings = get_settings()
    if settings.llm_provider == "ollama":
        from app.integrations.llm.ollama_client import OllamaLLMClient

        return OllamaLLMClient(settings.ollama_base_url, settings.ollama_model)
    from app.integrations.llm.demo_llm_client import DemoLLMClient

    return DemoLLMClient()


def get_ocr_client() -> Any:
    if _has_override(OCR):
        return _overrides[OCR]
    settings = get_settings()
    if settings.ocr_provider == "paddle":
        from app.integrations.ocr.paddle_ocr_client import PaddleOCRClient

        return PaddleOCRClient()
    from app.integrations.ocr.demo_ocr_client import DemoOCRClient

    return DemoOCRClient()


def get_portal_client() -> Any:
    if _has_override(PORTAL):
        return _overrides[PORTAL]
    settings = get_settings()
    from app.integrations.portal.mock_portal_api import MockPortalClient

    return MockPortalClient(
        base_url=settings.portal_base_url,
        timeout=settings.portal_timeout_seconds,
        api_token=settings.portal_api_token,
    )


def get_stt_client() -> Any:
    if _has_override(STT):
        return _overrides[STT]
    from app.integrations.voice.demo_voice import DemoSpeechToText

    return DemoSpeechToText()


def get_tts_client() -> Any:
    if _has_override(TTS):
        return _overrides[TTS]
    from app.integrations.voice.demo_voice import DemoTextToSpeech

    return DemoTextToSpeech()
