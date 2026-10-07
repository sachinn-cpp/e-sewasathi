"""Language detection and normalization for multilingual support."""

from __future__ import annotations

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "hi", "ne")
DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "ne": "नेपाली",
}

# Common Nepali words used to separate Nepali from Hindi in Devanagari text.
_NEPALI_MARKERS: tuple[str, ...] = (
    "होइन",
    "हो",
    "छ",
    "छन्",
    "म",
    "हामी",
    "तपाईं",
    "तिमी",
    "गर्न",
    "गर्छ",
    "भन्न",
    "चाहन्छ",
    "नेपाल",
    "नेपाली",
    "धन्यवाद",
    "कस्तो",
    "कहाँ",
    "किन",
)

_HI_MARKERS: tuple[str, ...] = (
    "है",
    "हैं",
    "मैं",
    "हम",
    "आप",
    "कर",
    "रहा",
    "रही",
    "भारत",
    "हिंदी",
    "नमस्ते",
)


def normalize_language(code: str | None) -> str:
    """Map a language tag to a supported code, defaulting to English."""
    if not code:
        return DEFAULT_LANGUAGE
    base = code.strip().lower().replace("_", "-").split("-")[0]
    if base in SUPPORTED_LANGUAGES:
        return base
    return DEFAULT_LANGUAGE


def is_supported(code: str | None) -> bool:
    return normalize_language(code) in SUPPORTED_LANGUAGES


def _count_hits(text: str, markers: tuple[str, ...]) -> int:
    return sum(1 for marker in markers if marker in text)


def detect_language(text: str) -> str:
    """Detect en/hi/ne from raw user text (script plus keyword heuristics)."""
    sample = (text or "").strip()
    if not sample:
        return DEFAULT_LANGUAGE

    devanagari_chars = sum(1 for ch in sample if "\u0900" <= ch <= "\u097F")
    if devanagari_chars > 0 and devanagari_chars >= len(sample) * 0.25:
        ne_score = _count_hits(sample, _NEPALI_MARKERS)
        hi_score = _count_hits(sample, _HI_MARKERS)
        if ne_score > hi_score:
            return "ne"
        if hi_score > ne_score:
            return "hi"
        return "ne" if "नेपाल" in sample else "hi"

    latin = sum(1 for ch in sample if ch.isascii() and ch.isalpha())
    if latin >= len(sample) * 0.5:
        return "en"
    return DEFAULT_LANGUAGE


def detect_or_normalize(preferred: str | None, text: str) -> str:
    """Use an explicit language when valid, otherwise detect from text."""
    if preferred and is_supported(preferred):
        return normalize_language(preferred)
    return detect_language(text)
