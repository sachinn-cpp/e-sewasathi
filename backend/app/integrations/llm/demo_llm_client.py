"""Deterministic demo LLM used when DEMO_MODE is on (no model downloads)."""

from __future__ import annotations

import re
from typing import Any

from app.integrations.llm.base import LLMClient, LLMReply

_INTENT_PATTERNS: list[tuple[str, str]] = [
    ("greeting", r"\b(hello|hi|namaste|namaskar|hey|greetings)\b"),
    ("status", r"\b(status|progress|update|where|kaha|kahani)\b"),
    ("documents", r"\b(document|doc|paper|upload|file|praman|पत्र)\b"),
    ("consent", r"\b(consent|permission|allow|agree|sahamati|सहमत)\b"),
    ("submission", r"\b(submit|submitting|application sent|portal|पेश)\b"),
    ("escalation", r"\b(human|agent|assistant|helper|escalate|support|help me)\b"),
    ("privacy", r"\b(privacy|data|delete|erase|security|गोपनीय)\b"),
    ("thanks", r"\b(thank|thanks|dhanyabad|dhanyavad|thanks? a lot)\b"),
    ("help", r"\b(help|how|what|guide|guide me|bata|बताउ)\b"),
]

_REPLIES: dict[str, dict[str, str]] = {
    "greeting": {
        "en": "Namaste! I am e-SewaSathi. Tell me what you would like to do, or ask about your application status.",
        "hi": "नमस्ते! मैं e-SewaSathi हूँ। बताइए आप क्या करना चाहेंगे, या अपने आवेदन की स्थिति पूछिए।",
        "ne": "नमस्ते! म e-SewaSathi हुँ। भन्नुहोस् के गर्न चाहनुहुन्छ, वा आफ्नो आवेदनको स्थिति सोध्नुहोस्।",
    },
    "status": {
        "en": "You can see your live application status on this page. The status timeline shows every change, and I will notify you through a real-time update whenever the portal reports a new status.",
        "hi": "आप इस पेज पर अपनी आवेदन की वर्तमान स्थिति देख सकते हैं। स्थिति टाइमलाइन हरि बदलाव दिखाती है, और पोर्टल से नई स्थिति मिलते ही आपको रीयल-टाइम अपडेट मिलेगा।",
        "ne": "तपाईं यहाँ आफ्नो आवेदनको वास्तविक स्थिति हेर्न सक्नुहुन्छ। स्थिति टाइमलाइनले हरेक परिवर्तन देखाउँछ, र पोर्टलबाट नयाँ स्थिति आएमा तपाईंलाई रियल-टाइम सूचना मिल्नेछ।",
    },
    "documents": {
        "en": "You need four documents: identity proof, address proof, income proof and a photograph. Upload them on the Documents section. Supported formats are PDF, JPEG and PNG up to 5 MB.",
        "hi": "आपको चार दस्तावेज़ चाहिए: पहचान प्रमाण, पता प्रमाण, आय प्रमाण और एक फ़ोटो। दस्तावेज़ अनुभाग में अपलोड करें। समर्थित प्रारूप PDF, JPEG और PNG हैं, अधिकतम 5 MB।",
        "ne": "तपाईंलाई चार कागजात चाहिन्छ: पहिचान प्रमाण, ठेगाना प्रमाण, आय प्रमाण र एउटा फोटो। कागजात खण्डमा अपलोड गर्नुहोस्। समर्थित ढाँचा PDF, JPEG र PNG हुन्, अधिकतम 5 MB।",
    },
    "consent": {
        "en": "Consent is requested only when it is needed, and it is recorded on our servers. Every sensitive step (reading documents, extracting data, filling the form, sharing with the portal, submitting) requires your approval. You can revoke consent any time by changing your data.",
        "hi": "सहमति केवल आवश्यकता पड़ने पर माँगी जाती है और हमारे सर्वर पर दर्ज की जाती है। हर संवेदनशील चरण (दस्तावेज़ पढ़ना, डेटा निकालना, फ़ॉर्म भरना, पोर्टल के साथ साझा करना, जमा करना) के लिए आपकी अनुमति चाहिए। आप कभी भी सहमति वापस ले सकते हैं।",
        "ne": "सहमति आवश्यक परेमा मात्र मागिन्छ र हाम्रो सर्भरमा दर्ता हुन्छ। हरेक संवेदनशील चरण (कागजात पढ्ने, तथ्यांक निकाल्ने, फारम भर्ने, पोर्टलसँग साझा गर्ने, पेश गर्ने) का लागि तपाईंको अनुमति चाहिन्छ। तपाईं जुनसुकै बेला सहमति फिर्ता लिन सक्नुहुन्छ।",
    },
    "submission": {
        "en": "When everything is ready I will ask for two confirmations: one to share your data with the portal and one to submit. Submission only happens after your approval is verified on the server.",
        "hi": "जब सब कुछ तैयार होगा मैं दो पुष्टियाँ माँगूँगा: एक पोर्टल के साथ डेटा साझा करने के लिए और एक जमा करने के लिए। आपकी अनुमति सर्वर पर सत्यापित होने के बाद ही जमा होता है।",
        "ne": "जब सबै तयार हुन्छ म दुई पुष्टि माग्नेछु: एउटा पोर्टलसँग तथ्यांक साझा गर्न, अर्को पेश गर्न। तपाईंको अनुमति सर्भरमा प्रमाणित भएपछि मात्र पेश हुन्छ।",
    },
    "escalation": {
        "en": "If something goes wrong, I will escalate your case to a human helper. You can also ask me to escalate; a helper will be assigned and you will see their note here.",
        "hi": "यदि कुछ गलत होता है तो मैं आपका मामला एक मानव सहायक को भेजूँगा। आप मुझसे एस्केलेट करने भी कह सकते हैं; एक सहायक नियुक्त होगा और उसका नोट यहाँ दिखेगा।",
        "ne": "केही गडबड भएमा म तपाईंको मामिला मानव सहयोगीलाई पठाउनेछु। तपाईं मलाई एस्केलेट गर्न भन्न पनि सक्नुहुन्छ; सहयोगी नियुक्त हुनेछ र उनको नोट यहाँ देखिनेछ।",
    },
    "privacy": {
        "en": "Your documents stay in private storage, are never put in URLs or logs, and can be deleted from your profile. Use Delete my data to remove or anonymise everything; audit records keep only minimal, non-identifying history.",
        "hi": "आपके दस्तावेज़ निजी स्टोरेज में रहते हैं, कभी URL या लॉग में नहीं जाते, और आपके प्रोफ़ाइल से हटाए जा सकते हैं। 'मेरा डेटा हटाएँ' से सब कुछ हटाएँ या गुमनाम करें; ऑडिट रिकॉर्ड में केवल न्यूनतम, गैर-पहचान इतिहास रहता है।",
        "ne": "तपाईंका कागजात निजी भण्डारमा रहन्छन्, कहिल्यै URL वा लगमा जाँदैनन्, र प्रोफाइलबाट मेटाउन सकिन्छ। 'मेरो तथ्यांक मेटाउनुहोस्' बाट सबै मेटाउनुहोस् वा गुमनाम बनाउनुहोस्; अडिट रेकर्डमा न्यूनतम, गैर-पहिचान इतिहास मात्र रहन्छ।",
    },
    "thanks": {
        "en": "You are welcome! I am here whenever you need help with your application.",
        "hi": "आपका स्वागत है! आवेदन में मदद के लिए मैं यहाँ हूँ।",
        "ne": "स्वागत छ! आवेदनमा मद्दतका लागि म यहाँ छु।",
    },
    "help": {
        "en": "Here is the flow: create the application, complete the form, upload four documents, review the extracted information, approve the consents, then submit. I guide you at every step.",
        "hi": "प्रवाह यह है: आवेदन बनाएँ, फ़ॉर्म पूरा करें, चार दस्तावेज़ अपलोड करें, निकाली गई जानकारी की समीक्षा करें, सहमतियाँ स्वीकार करें, फिर जमा करें। मैं हर चरण पर आपका मार्गदर्शन करता हूँ।",
        "ne": "प्रवाह यो हो: आवेदन बनाउनुहोस्, फारम पूरा गर्नुहोस्, चार कागजात अपलोड गर्नुहोस्, निकालिएको जानकारी समीक्षा गर्नुहोस्, सहमति स्वीकार गर्नुहोस्, अनि पेश गर्नुहोस्। म हरेक चरणमा मार्गदर्शन गर्छु।",
    },
    "fallback": {
        "en": "I can help with your application: status, documents, consent, submission or talking to a human helper. What would you like to do?",
        "hi": "मैं आपके आवेदन में मदद कर सकता हूँ: स्थिति, दस्तावेज़, सहमति, जमा करना, या मानव सहायक से बात करना। आप क्या करना चाहेंगे?",
        "ne": "म तपाईंको आवेदनमा मद्दत गर्न सक्छु: स्थिति, कागजात, सहमति, पेश गर्ने, वा मानव सहयोगीसँग कुरा गर्ने। के गर्न चाहनुहुन्छ?",
    },
}


def detect_intent(text: str) -> str:
    lowered = (text or "").lower()
    for intent, pattern in _INTENT_PATTERNS:
        if re.search(pattern, lowered):
            return intent
    return "fallback"


class DemoLLMClient(LLMClient):
    """Rule-based, fully deterministic replies for demo and tests."""

    provider = "demo"

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        language: str = "en",
        context: dict[str, Any] | None = None,
    ) -> LLMReply:
        last_user = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user = message.get("content", "")
                break
        intent = detect_intent(last_user)
        table = _REPLIES.get(intent, _REPLIES["fallback"])
        text = table.get(language) or table["en"]
        return LLMReply(text=text, intent=intent, provider="demo", model="rules-v1")
