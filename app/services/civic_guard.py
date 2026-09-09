import re
from typing import Tuple


class CivicGuardrailService:
    """Enforces civic compliance, privacy safeguards, and mandatory liability disclaimers."""

    DISCLAIMER_TEXT = (
        "Disclaimer: This guidance is automatically generated from approved civic service guidelines "
        "and is for informational purposes only. It does not constitute formal legal advice, "
        "official administrative adjudication, or a guarantee of application approval."
    )

    NO_ANSWER_TEXT = (
        "I could not find information regarding this question in the approved civic service documents. "
        "Please check the respective department office or submit a formal inquiry."
    )

    SENSITIVE_PATTERNS = [
        r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b",  # 12-digit format (Aadhaar-like)
        r"\b\d{3}[ -]?\d{2}[ -]?\d{4}\b",  # SSN-like
    ]

    @classmethod
    def sanitize_input(cls, user_text: str) -> Tuple[str, bool]:
        """
        Scan input text for sensitive numbers and redact them.
        Returns (sanitized_text, contains_sensitive_data).
        """
        sanitized = user_text
        found_sensitive = False

        # Keyword checks
        if any(kw in user_text.lower() for kw in ["aadhaar", "aadhar"]):
            found_sensitive = True

        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, sanitized):
                found_sensitive = True
                sanitized = re.sub(pattern, "[REDACTED-IDENTIFIER]", sanitized)

        return sanitized, found_sensitive

    GREETINGS_PATTERN = r"^(hi|hello|hey|help|namaste|greetings|good morning|good afternoon|good evening|who are you|what can you do|start)\b[!?.]*$"

    ALL_SERVICES_PATTERN = (
        r"(all\s+services?|every\s+service|list\s+(of\s+)?(all\s+)?services?|available\s+services?|"
        r"what\s+(are\s+)?(all\s+)?(the\s+)?services?|which\s+services?|service\s+catalogue?|service\s+catalog|"
        r"services\s+list|say\s+about\s+(all\s+)?services?|tell\s+(me\s+)?(about\s+)?(all\s+)?services?|"
        r"services?\s+available|services?\s+offered|about\s+all\s+services|sob\s+service|shob\s+service|"
        r"সকল\s+সার্ভিস|সব\s+সার্ভিস|সকল\s+সেবা|সব\s+সেবা|সকল\s+সার্ভিসগুলো|সকল\s+সেবাগুলো|सभी\s+सेवा|सारी\s+सेवा|all\s+available\s+services)"
    )

    ALL_DEPARTMENTS_PATTERN = (
        r"(all\s+departments?|every\s+department|list\s+(of\s+)?(all\s+)?departments?|available\s+departments?|"
        r"what\s+(are\s+)?(all\s+)?(the\s+)?departments?|which\s+departments?|departments?\s+list|department\s+directory|"
        r"say\s+about\s+(all\s+)?departments?|tell\s+(me\s+)?(about\s+)?(all\s+)?departments?|about\s+all\s+departments|"
        r"show\s+(all\s+)?departments?|sob\s+department|shob\s+department|"
        r"সকল\s+ডিপার্টমেন্ট|সব\s+ডিপার্টমেন্ট|সকল\s+দপ্তর|সব\s+দপ্তর|সকল\s+বিভাগ|সব\s+বিভাগ|सभी\s+विभाग|सारे\s+विभाग)"
    )

    GREETING_HELP_TEXT = (
        "Hello! Welcome to the AI-Powered Civic Service & Grievance Assistant. 🏛️\n\n"
        "I am an automated assistant grounded in approved municipal guidelines and citizen charters.\n\n"
        "📋 **How I can assist you:**\n"
        "* **Urban Water Supply**: Application requirements, meter fees, and connection policies\n"
        "* **Property Tax & Revenue**: Mutation procedures, assessment rules, and rebate timelines\n"
        "* **Trade Licensing**: Commercial permit clearances, fire safety rules, and renewal guidelines\n"
        "* **Civil Registration**: Birth & Death certificate statutory timelines (21 days) and requirements\n"
        "* **Building Plan Sanction**: Architectural drawings and NOC requirements\n"
        "* **Grievance Redressal**: Step-by-step SOP for lodging municipal complaints\n\n"
        "💡 **Sample questions to ask:**\n"
        "- *What mandatory documents are required for a new domestic water connection?*\n"
        "- *What is the property tax rebate for early payment?*\n"
        "- *What are the rules for birth certificate registration within 21 days?*\n\n"
        "Please ask your specific procedural or documentation inquiry!"
    )

    @classmethod
    def is_greeting(cls, user_text: str) -> bool:
        """Check if user message is a general greeting or help request."""
        clean = user_text.strip().lower()
        return bool(re.match(cls.GREETINGS_PATTERN, clean))

    @classmethod
    def is_all_services_query(cls, user_text: str) -> bool:
        """Check if user message is an inquiry asking for an overview/list of all services."""
        clean = user_text.strip().lower()
        return bool(re.search(cls.ALL_SERVICES_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_all_departments_query(cls, user_text: str) -> bool:
        """Check if user message is an inquiry asking for an overview/list of all departments."""
        clean = user_text.strip().lower()
        return bool(re.search(cls.ALL_DEPARTMENTS_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def get_greeting_help_text(cls) -> str:
        """Return structured civic guide and capabilities."""
        return cls.GREETING_HELP_TEXT

    @classmethod
    def get_standard_disclaimer(cls) -> str:
        """Return the official mandatory civic disclaimer."""
        return cls.DISCLAIMER_TEXT

    @classmethod
    def get_no_answer_text(cls) -> str:
        """Return standard no-answer response when query falls outside knowledge base."""
        return cls.NO_ANSWER_TEXT


civic_guard = CivicGuardrailService()

