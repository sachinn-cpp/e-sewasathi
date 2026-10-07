"""Voice adapter interfaces (STT/TTS) for future Whisper and TTS backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptResult:
    """Result of speech-to-text conversion."""

    text: str
    provider: str = "demo"
    language: str = "en"


class SpeechToTextClient(ABC):
    """Converts uploaded audio into text."""

    @abstractmethod
    async def transcribe(self, audio: bytes, language: str = "en") -> TranscriptResult:
        """Transcribe audio bytes (demo adapter is deterministic)."""


class TextToSpeechClient(ABC):
    """Converts text into playable audio."""

    @abstractmethod
    async def synthesize(self, text: str, language: str = "en") -> tuple[bytes, str]:
        """Return (audio_bytes, mime_type)."""
