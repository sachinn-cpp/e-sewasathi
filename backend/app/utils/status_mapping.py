"""Portal status to application status mapping and status messages."""

from __future__ import annotations

# Portal statuses returned by the mock government portal.
PORTAL_SUBMITTED = "submitted"
PORTAL_UNDER_REVIEW = "under_review"
PORTAL_ACTION_REQUIRED = "action_required"
PORTAL_APPROVED = "approved"
PORTAL_REJECTED = "rejected"

PORTAL_TO_APPLICATION: dict[str, str] = {
    PORTAL_SUBMITTED: "submitted",
    PORTAL_UNDER_REVIEW: "under_government_review",
    PORTAL_ACTION_REQUIRED: "action_required",
    PORTAL_APPROVED: "completed",
    PORTAL_REJECTED: "action_required",
}

# Progress and step for Phase 2 statuses (Phase 1 statuses keep legacy logic).
PROGRESS_BY_STATUS: dict[str, int] = {
    "documents_under_review": 85,
    "awaiting_consent": 88,
    "submitting": 90,
    "submitted": 93,
    "under_government_review": 96,
    "action_required": 96,
    "escalated": 96,
    "completed": 100,
    "failed": 96,
}

STEP_BY_STATUS: dict[str, str] = {
    "documents_under_review": "documents",
    "awaiting_consent": "consent",
    "submitting": "submit",
    "submitted": "submit",
    "under_government_review": "tracking",
    "action_required": "action",
    "escalated": "escalated",
    "completed": "completed",
    "failed": "action",
}

PHASE2_STATUSES: frozenset[str] = frozenset(PROGRESS_BY_STATUS)

STATUS_MESSAGES: dict[str, dict[str, str]] = {
    "draft": {
        "en": "Draft application. Fill in your form details.",
        "hi": "मसौदा आवेदन। अपना फ़ॉर्म भरें।",
        "ne": "कार्यरत मसौदा। आफ्नो फारम भर्नुहोस्।",
    },
    "documents_pending": {
        "en": "Waiting for your documents.",
        "hi": "आपके दस्तावेज़ों की प्रतीक्षा है।",
        "ne": "तपाईंका कागजातहरूको पर्खाइ छ।",
    },
    "awaiting_user_review": {
        "en": "Please review your application before submission.",
        "hi": "जमा करने से पहले कृपया अपने आवेदन की समीक्षा करें।",
        "ne": "पेश गर्नु अघि कृपया आफ्नो आवेदन समीक्षा गर्नुहोस्।",
    },
    "documents_under_review": {
        "en": "Reviewing your documents.",
        "hi": "आपके दस्तावेज़ों की समीक्षा हो रही है।",
        "ne": "तपाईंका कागजात समीक्षा भइरहेको छ।",
    },
    "awaiting_consent": {
        "en": "Your consent is required to continue.",
        "hi": "आगे बढ़ने के लिए आपकी सहमति आवश्यक है।",
        "ne": "अघि बढ्न तपाईंको सहमति आवश्यक छ।",
    },
    "submitting": {
        "en": "Submitting your application to the portal.",
        "hi": "पोर्टल पर आपका आवेदन जमा किया जा रहा है।",
        "ne": "पोर्टलमा तपाईंको आवेदन पेश गरिँदैछ।",
    },
    "submitted": {
        "en": "Application submitted successfully.",
        "hi": "आवेदन सफलतापूर्वक जमा हो गया।",
        "ne": "आवेदन सफलतापूर्वक पेश भयो।",
    },
    "under_government_review": {
        "en": "Your application is under government review.",
        "hi": "आपका आवेदन सरकारी समीक्षा में है।",
        "ne": "तपाईंको आवेदन सरकारी समीक्षामा छ।",
    },
    "action_required": {
        "en": "Action is required on your application.",
        "hi": "आपके आवेदन पर कार्रवाई आवश्यक है।",
        "ne": "तपाईंको आवेदनमा कारबाही आवश्यक छ।",
    },
    "escalated": {
        "en": "A human assistant has been assigned to help you.",
        "hi": "एक मानव सहायक आपकी मदद के लिए नियुक्त किया गया है।",
        "ne": "मानव सहयोगीले तपाईंलाई मद्दत गर्न नियुक्त गरिएको छ।",
    },
    "completed": {
        "en": "Application completed successfully.",
        "hi": "आवेदन सफलतापूर्वक पूरा हो गया।",
        "ne": "आवेदन सफलतापूर्वक पूरा भयो।",
    },
    "failed": {
        "en": "The submission failed. A human assistant can help.",
        "hi": "जमा करना विफल रहा। एक मानव सहायक मदद कर सकता है।",
        "ne": "पेश गर्न असफल भयो। मानव सहयोगीले मद्दत गर्न सक्छ।",
    },
    "cancelled": {
        "en": "Application cancelled.",
        "hi": "आवेदन रद्द कर दिया गया।",
        "ne": "आवेदन रद्द गरियो।",
    },
}


def map_portal_status(portal_status: str) -> str:
    """Map a portal status onto an application status."""
    return PORTAL_TO_APPLICATION.get(portal_status, "under_government_review")


def status_message(status: str, language: str = "en") -> str:
    """Localized user-facing message for an application status."""
    entry = STATUS_MESSAGES.get(status, {})
    return entry.get(language) or entry.get("en") or "Status updated."


def progress_for_status(status: str) -> int | None:
    return PROGRESS_BY_STATUS.get(status)


def step_for_status(status: str) -> str | None:
    return STEP_BY_STATUS.get(status)
