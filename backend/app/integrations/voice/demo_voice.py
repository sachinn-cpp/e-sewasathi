"""Deterministic demo voice adapters (no models, reproducible output)."""

from __future__ import annotations

import hashlib
import io
import math
import struct
import wave

from app.integrations.voice.base import (
    SpeechToTextClient,
    TextToSpeechClient,
    TranscriptResult,
)

_PHRASES: dict[str, tuple[str, ...]] = {
    "en": (
        "What is the status of my application?",
        "I need help uploading my documents.",
        "Please submit my application.",
        "Can I speak to a human helper?",
    ),
    "hi": (
        "मेरे आवेदन की स्थिति क्या है?",
        "मुझे दस्तावेज़ अपलोड करने में मदद चाहिए।",
        "कृपया मेरा आवेदन जमा करें।",
        "क्या मैं एक मानव सहायक से बात कर सकता हूँ?",
    ),
    "ne": (
        "मेरो आवेदनको स्थिति के हो?",
        "मलाई कागजात अपलोड गर्न मद्दत चाहिए।",
        "कृपया मेरो आवेदन पेश गर्नुहोस्।",
        "के म मानव सहयोगीसँग कुरा गर्न सक्छु?",
    ),
}


class DemoSpeechToText(SpeechToTextClient):
    """Picks a canned phrase deterministically from the audio bytes."""

    provider = "demo"

    async def transcribe(self, audio: bytes, language: str = "en") -> TranscriptResult:
        phrases = _PHRASES.get(language) or _PHRASES["en"]
        digest = hashlib.sha256(audio or b"silent").digest()
        index = digest[0] % len(phrases)
        return TranscriptResult(
            text=phrases[index], provider=self.provider, language=language
        )


class DemoTextToSpeech(TextToSpeechClient):
    """Generates a short deterministic WAV tone pattern (8 kHz mono)."""

    provider = "demo"

    async def synthesize(self, text: str, language: str = "en") -> tuple[bytes, str]:
        digest = hashlib.sha256((text or "hello").encode("utf-8")).digest()
        sample_rate = 8000
        duration = min(2.0, 0.6 + len(text) * 0.02)
        total = int(sample_rate * duration)
        frames = bytearray()
        for i in range(total):
            step = digest[(i // 800) % len(digest)]
            frequency = 220.0 + (step % 12) * 55.0
            envelope = 1.0 - (i / total)
            sample = int(
                12000 * envelope * math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            frames += struct.pack("<h", sample)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(bytes(frames))
        return buffer.getvalue(), "audio/wav"
