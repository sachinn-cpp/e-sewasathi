"""Voice adapter package."""

from app.integrations.voice.base import (
    SpeechToTextClient,
    TextToSpeechClient,
    TranscriptResult,
)

__all__ = ["SpeechToTextClient", "TextToSpeechClient", "TranscriptResult"]
