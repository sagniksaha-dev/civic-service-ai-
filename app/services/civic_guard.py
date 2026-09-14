import re
from typing import Optional, Tuple


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
        r"(\b(all\s+([a-z]+\s+)?services?|every\s+service|list\s+(of\s+)?(all\s+)?(existing\s+|available\s+)?services?|"
        r"available\s+services?|existing\s+services?|municipal\s+services?\s+(list|directory|catalogue|catalog)|"
        r"what\s+are\s+(all\s+)?(the\s+)?(existing\s+|available\s+)?services?|which\s+services\s+are\s+(all\s+)?(existing\s+|available)|"
        r"services?\s+(catalogue|catalog|list|directory|overview)|service\s+(catalogue|catalog)|"
        r"say\s+about\s+(all\s+)?(existing\s+|available\s+)?services?|tell\s+(me\s+)?(about\s+)?(all\s+)?(existing\s+|available\s+)?services?|"
        r"about\s+all\s+(existing\s+|available\s+)?services?|show\s+(me\s+)?all\s+(existing\s+|available\s+)?services?|"
        r"how\s+many\s+services?|all\s+services?\s+in\s+(this\s+|the\s+)?portal|"
        r"sob\s+service|shob\s+service)\b|"
        r"(সকল\s+সার্ভিস|সব\s+সার্ভিস|সকল\s+সেবা|সব\s+সেবা|সকল\s+সার্ভিসগুলো|সকল\s+সেবাগুলো|सभी\s+सेवा|सारी\s+सेवा))"
    )

    ALL_DEPARTMENTS_PATTERN = (
        r"(\b(all\s+([a-z]+\s+)?departments?|every\s+department|list\s+(of\s+)?(all\s+)?(existing\s+|available\s+)?departments?|"
        r"available\s+departments?|existing\s+departments?|municipal\s+departments?\s+(list|directory|catalogue|catalog)|"
        r"what\s+are\s+(all\s+)?(the\s+)?(existing\s+|available\s+)?departments?|which\s+departments\s+are\s+(all\s+)?(existing\s+|available)|"
        r"departments?\s+(list|directory|catalogue|catalog|overview)|"
        r"say\s+about\s+(all\s+)?(existing\s+|available\s+)?departments?|tell\s+(me\s+)?(about\s+)?(all\s+)?(existing\s+|available\s+)?departments?|"
        r"about\s+all\s+(existing\s+|available\s+)?departments?|show\s+(me\s+)?all\s+(existing\s+|available\s+)?departments?|"
        r"how\s+many\s+departments?|all\s+departments?\s+in\s+(this\s+|the\s+)?portal|"
        r"sob\s+department|shob\s+department)\b|"
        r"(সকল\s+ডিপার্টমেন্ট|সব\s+ডিপার্টমেন্ট|সকল\s+দপ্তর|সব\s+দপ্তর|সকল\s+বিভাগ|সব\s+বিভাগ|সকল\s+বিভাগগুলো|সকল\s+দপ্তরগুলো|सभी\s+विभाग|सारे\s+विभाग))"
    )

    DRAINAGE_PROBLEM_PATTERN = (
        r"\b(drain|drainage|sewer|sewerage|locality\s+drain|clogged\s+drain|drain\s+overflow|overflowing\s+drain|"
        r"waterlogging|drain\s+blockage|desilting|unclog\s+drain|ড্রেন|ড্রেনেজ|নালা|নর্দমা|জলবদ্ধতা|নালা\s*নর্দমা|নালা\s*পরিষ্কার|নালা\s*নর্দমার|নালা\s*নর্দমার\s*সমস্যা|নালা\s*সমস্যা|ড্রেন\s*সমস্যা|নালা\s*ভাঙা|ড্রেন\s*ভাঙা|নালা\s*উপচে|ড্রেন\s*উপচে|নালা\s*বন্ধ|ড্রেন\s*বন্ধ|নালা\s*নর্দমার\s*জল|নালা\s*নর্দমার\s*পানি|নালা\s*নর্দমার\s*ময়লা|নালা\s*নর্দমার\s*বর্জ্য|নালা\s*নর্দমার\s*দুর্গন্ধ|নালা\s*নর্দমার\s*কাদা|নালা\s*নর্দমার\s*পলি|নালা\s*নর্দমার\s*আবর্জনা|নালা\s*নর্দমার\s*কচড়া|নালা\s*নর্দমার\s*কচড়া|নালা\s*নর্দমার\s*कूड़ा|নালা\s*নর্দমার\s*सफाई|নালা\s*নর্দমার\s*कचरा|নালা\s*নর্দমার\s*नाली|নালা\s*নর্দমার\s*জলভराव|নালা\s*নর্দমার\s*पानी|নালা\s*নর্দমার\s*लीकेज|নালা\s*নর্দমার\s*समस्या|নালা\s*নর্দমার\s*सीवर|নালা\s*নর্দমার\s*जलजमाव|নালা\s*নর্দমার\s*जलभराव|নালা\s*নর্দমার\s*নালা|নালা\s*নর্দমার\s*নর্দমা|নালা\s*নর্দমার\s*ড্রেন|নালা\s*নর্দমার\s*ড্রেনেজ|নালা\s*নর্দমার\s*জলবদ্ধতা|নালা\s*নর্দমার\s*পানির\s*সমস্যা|নালা\s*নর্দমার\s*পানি\s*নেই|নালা\s*নর্দমার\s*পানির\s*পাইপ\s*ভাঙা|নালা\s*নর্দমার\s*পানি\s*লিকেজ|নালা\s*নর্দমার\s*पानी\s*की\s*समस्या|নালা\s*নর্দমার\s*पानी\s*का\s*लीकेज|नाली|जलभराव|सीवर)\b"
    )

    GARBAGE_PROBLEM_PATTERN = (
        r"\b(garbage|trash|waste\s+dump|rubbish|dustbin|dead\s+animal|street\s+cleaning|litter|solid\s+waste|"
        r"আবর্জনা|ময়লা|কচড়া|বর্জ্য|কচড়া|कचरा|सफाई|कूड़ा)\b"
    )

    ROAD_LIGHT_PROBLEM_PATTERN = (
        r"\b(pothole|potholes|broken\s+road|damaged\s+road|street\s+light|broken\s+light|dark\s+street|lamp\s+post|"
        r"রাস্তা\s+ভাঙা|রাস্তা\s+মেরামত|স্ট্রিট\s+লাইট|সড়কবাতি|সড়কবাতি|सड़क|गड्ढे|स्ट्रीट\s+लाइट)\b"
    )

    WATER_LEAK_PROBLEM_PATTERN = (
        r"\b(water\s+leakage|pipeline\s+leak|pipe\s+burst|dirty\s+water|contaminated\s+water|no\s+water\s+supply|low\s+water\s+pressure|"
        r"পানির\s+সমস্যা|পানি\s+নেই|পানির\s+পাইপ\s+ভাঙা|পানি\s+লিকেজ|पानी\s+की\s+समस्या|पानी\s+का\s+लीकेज)\b"
    )

    OUT_OF_SCOPE_TERMS = {
        "spaceship", "interstellar", "mars", "alien", "crypto", "bitcoin",
        "spacecraft", "galaxy", "astrology", "superhero", "jupiter", "starship"
    }

    HOW_TO_APPLY_PATTERN = (
        r"\b(how\s+(can\s+|do\s+|i\s+|to\s+|we\s+)*(apply|submit\s+an?\s+application|file\s+an?\s+application|register\s+for\s+(a\s+)?service)|"
        r"application\s+process|application\s+procedure|steps\s+to\s+apply|procedure\s+to\s+apply|"
        r"where\s+to\s+apply|how\s+to\s+apply|how\s+i\s+apply|"
        r"kivabe\s+apply\s+korbo|kivabe\s+abedon\s+korbo|abedon\s+poddhoti|abedon\s+korar\s+niyom|"
        r"কীভাবে\s+আবেদন\s+করব|আবেদন\s+পদ্ধতি|আবেদনের\s+নিয়ম|आवेदन\s+कैसे\s+करें|आवेदन\s+प्रक्रिया)\b"
    )

    HOW_TO_GRIEVANCE_PATTERN = (
        r"\b(how\s+(can\s+|do\s+|i\s+|to\s+|we\s+)*(complain|file\s+(a\s+)?grievance|submit\s+(a\s+)?complaint|lodge\s+(a\s+)?complaint|lodge\s+(a\s+)?grievance|report\s+an?\s*issue)|"
        r"lodge\s+(a\s+)?complaint|file\s+(a\s+)?grievance|submit\s+(a\s+)?grievance|"
        r"grievance\s+process|grievance\s+procedure|complaint\s+procedure|steps\s+to\s+complain|"
        r"how\s+to\s+grievance|how\s+to\s+complain|"
        r"kivabe\s+complaint\s+korbo|kivabe\s+ovijog\s+korbo|অভিযোগ\s+পদ্ধতি|অভিযোগ\s+কীভাবে\s+করব|शिकायत\s+कैसे\s+दर्ज\s+करें)\b"
    )

    HOW_TO_TRACK_PATTERN = (
        r"\b(how\s+(can\s+|do\s+|i\s+|to\s+|we\s+)*(track|check\s+(application\s+)?status)|"
        r"track\s+application|tracking\s+process|check\s+application\s+status|how\s+to\s+track|"
        r"kivabe\s+track\s+korbo|status\s+check\s+korbo|ট্র্যাকিং|স্ট্যাটাস\s+চেক|स्थिति\s+कैसे\s+जांचें)\b"
    )

    FIND_SERVICE_OR_DEPT_PATTERN = (
        r"\b((how\s+(can\s+|do\s+|i\s+|to\s+|we\s+)*find\s+(a\s+)?(service|department))|"
        r"(find\s+a?\s*service\s+that\s+i\s+need)|"
        r"(which\s+department\s+(is|will\s+be)\s+best)|"
        r"(department\s+that\s+will\s+be\s+best)|"
        r"(how\s+to\s+choose\s+(a\s+)?(service|department))|"
        r"(how\s+to\s+know\s+which\s+department)|"
        r"(which\s+service\s+do\s+i\s+need)|"
        r"(which\s+department\s+(should\s+i|do\s+i\s+contact|provides))|"
        r"(department\s+finder|service\s+finder)|"
        r"(kivabe\s+(service|department)\s+khujbo)|"
        r"(কোন\s+ডিপার্টমেন্ট|কীভাবে\s+সার্ভিস\s+খুঁজব)|"
        r"(विभाग\s+कैसे\s+खोजें|सेवा\s+कैसे\s+खोजें))\b"
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

    GUARANTEE_PATTERN = (
        r"(guarantee|promise|guaranteed|100%|surely approve|can you approve|instant approval|confirm approval|"
        r"will my application be approved|can i get guaranteed|approve right now|promise approval|guarantee approval)"
    )

    ANTI_GUARANTEE_TEXT = (
        "No. The AI Civic Assistant cannot guarantee or promise application approval under any circumstances.\n\n"
        "Official decisions on civic service applications are strictly subject to:\n"
        "* **Statutory Document Verification**: Scrutiny of all submitted documents by designated department officials.\n"
        "* **Eligibility & Field Inspection**: Compliance with municipal bylaws, site inspections, and statutory rules.\n"
        "* **Administrative Adjudication**: Final decisions (approval, rejection, or additional info requests) rest exclusively with authorized municipal officers.\n\n"
        "Please review the official eligibility guidelines and ensure all required documents are complete and valid before submitting."
    )

    @classmethod
    def is_greeting(cls, user_text: str) -> bool:
        """Check if user message is a general greeting or help request."""
        clean = user_text.strip().lower()
        return bool(re.match(cls.GREETINGS_PATTERN, clean))

    @classmethod
    def is_guarantee_query(cls, user_text: str) -> bool:
        """Check if user is asking for guaranteed approval, promises, or immediate adjudication."""
        clean = user_text.strip().lower()
        return bool(re.search(cls.GUARANTEE_PATTERN, clean, re.IGNORECASE))

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
    def is_out_of_scope(cls, user_text: str) -> bool:
        """Check if user message mentions clear out-of-scope/extraterrestrial/crypto terms."""
        clean = user_text.lower()
        return any(term in clean for term in cls.OUT_OF_SCOPE_TERMS)

    @classmethod
    def is_how_to_apply_query(cls, user_text: str) -> bool:
        """Check if user is asking how to apply or for general application procedure."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.HOW_TO_APPLY_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_how_to_grievance_query(cls, user_text: str) -> bool:
        """Check if user is asking how to submit or file a civic grievance."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.HOW_TO_GRIEVANCE_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_how_to_track_query(cls, user_text: str) -> bool:
        """Check if user is asking how to track submitted applications."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.HOW_TO_TRACK_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_find_service_or_dept_query(cls, user_text: str) -> bool:
        """Check if user is asking how to find a service or which department is best for their needs."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.FIND_SERVICE_OR_DEPT_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_drainage_problem_query(cls, user_text: str) -> bool:
        """Check if inquiry relates to locality drain, drainage blockage, waterlogging, or desilting."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.DRAINAGE_PROBLEM_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_garbage_problem_query(cls, user_text: str) -> bool:
        """Check if inquiry relates to garbage accumulation, street waste, or sanitation."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.GARBAGE_PROBLEM_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_road_light_problem_query(cls, user_text: str) -> bool:
        """Check if inquiry relates to broken roads, potholes, or street lighting."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.ROAD_LIGHT_PROBLEM_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def is_water_problem_query(cls, user_text: str) -> bool:
        """Check if inquiry relates to water supply contamination, leaks, or low pressure."""
        if cls.is_out_of_scope(user_text):
            return False
        clean = user_text.strip().lower()
        return bool(re.search(cls.WATER_LEAK_PROBLEM_PATTERN, clean, re.IGNORECASE))

    @classmethod
    def get_drainage_problem_text(cls, language: Optional[str] = "en") -> str:
        """Return official municipal guidance for locality drainage issues."""
        lang = (language or "en").lower().strip()
        if lang == "bn":
            return (
                "এলাকার নালা/নর্দমার সমস্যা (ড্রেন বন্ধ, উপচে পড়া ময়লা বা জলবদ্ধতা)-র জন্য সমাধান নির্দেশিকা:\n\n"
                "📢 **১. প্রধান পদক্ষেপ: মিউনিসিপ্যাল গ্রিভ্যান্স (অভিযোগ) দাখিল করুন (পরিষ্কার ও মেরামতের জন্য)**\n"
                "- এলাকার নালা পরিষ্কার, ড্রেন আনব্লক বা জলবদ্ধতার তাৎক্ষণিক সমাধানের জন্য নতুন পেইড সার্ভিসের বদলে **Grievance (অভিযোগ)** দাখিল করতে হবে।\n"
                "- **দায়িত্বপ্রাপ্ত বিভাগ**: **Solid Waste Management & Sanitation (`DEPT-SWM`)** অথবা **Public Works & Roads (`DEPT-PWR`)**।\n"
                "- **দাখিল করার নিয়ম**:\n"
                "  ১. সাইডবার থেকে **Grievance Redressal** (`/static/grievances.html`) পেজে যান।\n"
                "  ২. ডিপার্টমেন্ট নির্বাচন করুন: **Solid Waste Management & Sanitation** (বা Public Works)।\n"
                "  ৩. বিষয়: *Locality Drain Blockage / Cleaning Request*।\n"
                "  ৪. বিবরণীতে আপনার এলাকার সঠিক ঠিকানা, রাস্তা বা ল্যান্ডমার্ক উল্লেখ করুন।\n"
                "  ৫. সাবমিট করে ট্র্যাকিং টিকিট নম্বর (যেমন: `GRV-2026-XXXX`) সংগ্রহ করুন।\n"
                "- **SLA সমাধান সময়**: ২৪ থেকে ৪৮ ঘণ্টার মধ্যে পরিচ্ছন্নতাকর্মী দল পাঠিয়ে ড্রেন পরিষ্কার করা হয়।\n\n"
                "🏗️ **২. স্থায়ী পাইপলাইন সংযোগের জন্য আবেদন:**\n"
                "- নতুন বাড়ি বা প্রতিষ্ঠানের জন্য স্থায়ী নর্দমা/ড্রেনেজ পাইপ সংযোগের প্রয়োজন হলে **Urban Water Supply (`DEPT-WS`)** থেকে **Residential Pipeline Installation (`WAT-INST-01`)** সার্ভিসের জন্য আবেদন করুন।"
            )
        return (
            "For locality drainage problems (overflow, clogged drains, waterlogging, or broken sewer lines), here is the official municipal course of action:\n\n"
            "📢 **1. Primary Action: Lodge a Municipal Grievance (Recommended for cleaning & repairs)**\n"
            "- For immediate cleaning, unclogging, or desilting of your locality drain, you should file a **Grievance Complaint** rather than applying for a paid commercial service.\n"
            "- **Responsible Department**: **Solid Waste Management & Sanitation Department (`DEPT-SWM`)** or **Public Works & Roads (`DEPT-PWR`)**.\n"
            "- **How to submit**:\n"
            "  1. Go to **Grievance Redressal** (`/static/grievances.html`) from the sidebar navigation.\n"
            "  2. Select Department: **Solid Waste Management & Sanitation** (or Public Works & Roads).\n"
            "  3. Subject: *Locality Drain Cleaning / Unclogging Request*.\n"
            "  4. Description: Mention the specific locality, street name, and landmark.\n"
            "  5. Submit to get your tracking ticket (e.g., `GRV-2026-XXXX`).\n"
            "- **SLA Resolution**: Field sanitation teams are dispatched within **24 to 48 hours** for on-site desilting and clearance.\n\n"
            "🏗️ **2. When to Apply for a Civic Service:**\n"
            "- If you are building a new residential/commercial structure and need a permanent connection to the municipal stormwater/drain network, apply for:\n"
            "  - **Residential Pipeline Installation (`WAT-INST-01`)** under **Urban Water Supply & Drainage (`DEPT-WS`)**.\n"
            "  - **Commercial Waste Disposal Clearance (`SAN-CLEAR-01`)** under **Solid Waste Management (`DEPT-SWM`)**."
        )

    @classmethod
    def get_garbage_problem_text(cls, language: Optional[str] = "en") -> str:
        """Return official municipal guidance for garbage accumulation."""
        return (
            "For locality garbage accumulation or uncollected street waste:\n\n"
            "📢 **Primary Action: Lodge a Municipal Grievance**\n"
            "- File a grievance under **Solid Waste Management & Sanitation (`DEPT-SWM`)**.\n"
            "- Go to **Grievance Redressal** (`/static/grievances.html`), select `DEPT-SWM`, and enter your locality location.\n"
            "- Municipal sanitation squads will clear the garbage within **24 hours**."
        )

    @classmethod
    def get_road_light_problem_text(cls, language: Optional[str] = "en") -> str:
        """Return official municipal guidance for broken roads and streetlights."""
        return (
            "For broken roads, potholes, or faulty streetlights:\n\n"
            "📢 **Primary Action: Lodge a Municipal Grievance**\n"
            "- File a grievance under **Public Works & Roads Department (`DEPT-PWR`)**.\n"
            "- Go to **Grievance Redressal** (`/static/grievances.html`), select `DEPT-PWR`, and describe the road or streetlight issue with location details."
        )

    @classmethod
    def get_water_problem_text(cls, language: Optional[str] = "en") -> str:
        """Return official municipal guidance for water supply problems."""
        return (
            "For water supply disruptions, pipeline leaks, or contaminated water:\n\n"
            "📢 **1. For Repairs / Supply Issues:**\n"
            "- File a complaint under **Urban Water Supply Department (`DEPT-WS`)** at **Grievance Redressal** (`/static/grievances.html`).\n\n"
            "🚰 **2. For New Connection:**\n"
            "- Apply for **New Domestic Water Connection (`UWSD-WTR-01`)** from the **Service Catalogue** (`/static/services.html`)."
        )

    @classmethod
    def get_find_service_or_dept_text(cls, language: Optional[str] = "en") -> str:
        """Return comprehensive guide on locating services and identifying the best department."""
        lang = (language or "en").lower().strip()
        if lang == "bn":
            return (
                "আপনার প্রয়োজনীয় সেবা এবং সঠিক মিউনিসিপ্যাল ডিপার্টমেন্ট খুঁজে নেওয়ার নিয়মাবলী:\n\n"
                "🧭 **১. সার্ভিস ক্যাটালগ অনুসন্ধান ও ফিল্টার:**\n"
                "- বামপাশের মেনু থেকে **Service Catalogue** (`/static/services.html`) পেজে যান।\n"
                "- সার্চ বক্সে আপনার প্রয়োজনীয় কি-ওয়ার্ড লিখুন (যেমন: *water, tax, mutation, trade license, birth certificate, solid waste*)।\n"
                "- ডিপার্টমেন্ট অনুযায়ী ফিল্টার করে সেবার বিবরণ, ফি ও নথিপত্রের তালিকা দেখুন।\n\n"
                "🏛️ **২. ডিপার্টমেন্ট ও প্রধান সেবাসমূহের তালিকা:**\n"
                "- 💧 **Urban Water Supply (`DEPT-WS`)**: নতুন পানির সংযোগ, মিটার স্থাপন ও পাইপলাইন মেরামত।\n"
                "- 🏠 **Property Tax & Revenue (`DEPT-PTR`)**: মিউটেশন, অ্যাসেসমেন্ট ও কর প্রদান।\n"
                "- 🏪 **Trade Licensing & Health (`DEPT-TLH`)**: ট্রেড লাইসেন্স ইস্যু ও নবায়ন, স্বাস্থ্য ছাড়পত্র।\n"
                "- 📜 **Civil Registration (`DEPT-CR`)**: জন্ম ও মৃত্যু নিবন্ধন সার্টিফিকেট।\n"
                "- 🏗️ **Building Plan Sanction (`DEPT-BPS`)**: বাড়ি ও বাণিজ্যিক ভবনের নকশা অনুমোদন।\n"
                "- 🚛 **Solid Waste Management (`DEPT-SWM`)**: বর্জ্য অপসারণ ও স্যানিটেশন।\n"
                "- 🚧 **Public Works & Roads (`DEPT-PWR`)**: রাস্তা মেরামত ও সড়কবাতি রক্ষণাবেক্ষণ।\n"
                "- 🚒 **Fire Safety & Emergency (`DEPT-FSE`)**: অগ্নিনির্বাপণ ছাড়পত্র ও নিরাপত্তা অডিট।\n"
                "- 🌳 **Parks, Gardens & Environment (`DEPT-PGE`)**: পার্ক ও পরিবেশ রক্ষণাবেক্ষণ।\n"
                "- ⚖️ **Legal & Public Grievance (`DEPT-LPG`)**: প্রশাসনিক আপিল ও অভিযোগ নিষ্পত্তি।\n\n"
                "🤖 **৩. সরাসরি AI অ্যাসিস্ট্যান্টকে জিজ্ঞাসা করুন:**\n"
                "- আপনি আপনার প্রয়োজনটি সাধারণ ভাষায় এই চ্যাটে লিখুন (যেমন: *'আমি দোকান খুলতে চাই, কি লাইসেন্স লাগবে?'* বা *'বাড়ির নাম পরিবর্তন করব কিভাবে?'*) — AI সাথে সাথে সঠিক ডিপার্টমেন্ট ও সেবার গাইডলাইন বলে দেবে!"
            )
        return (
            "Here is how to find the right civic service and municipal department for your needs:\n\n"
            "🧭 **1. Explore the Service Catalogue (Search & Filter):**\n"
            "- Navigate to **Service Catalogue** (`/static/services.html`) from the sidebar.\n"
            "- Use the real-time search bar to type keywords related to your need (e.g., *water, tax, mutation, trade license, birth certificate, building plan*).\n"
            "- Filter by department or browse service cards displaying SLAs, fees, and requirements.\n\n"
            "🏛️ **2. Department-to-Service Mapping Directory:**\n"
            "- 💧 **Urban Water Supply (`DEPT-WS`)**: Domestic & commercial water connection, meter installation, reconnection, pipeline repair.\n"
            "- 🏠 **Property Tax & Revenue (`DEPT-PTR`)**: Property mutation, self-assessment, tax calculation, rebate settlement.\n"
            "- 🏪 **Trade Licensing & Health (`DEPT-TLH`)**: New trade license, annual renewal, food sanitation NOC, health permits.\n"
            "- 📜 **Civil Registration (`DEPT-CR`)**: Birth & Death certificate issuance, corrections, statutory 21-day timeline.\n"
            "- 🏗️ **Building Plan Sanction (`DEPT-BPS`)**: Blueprint approvals, structural stability sanction, completion certificates.\n"
            "- 🚛 **Solid Waste Management (`DEPT-SWM`)**: Commercial waste collection, bulk debris clearance, sanitation.\n"
            "- 🚧 **Public Works & Roads (`DEPT-PWR`)**: Pothole repairs, street lighting maintenance, road resurfacing.\n"
            "- 🚒 **Fire Safety & Emergency (`DEPT-FSE`)**: Fire NOC, commercial premise safety clearance, hazard inspections.\n"
            "- 🌳 **Parks, Gardens & Environment (`DEPT-PGE`)**: Tree trimming, park maintenance, public green space clearances.\n"
            "- ⚖️ **Legal & Public Grievance (`DEPT-LPG`)**: Escalated complaints, administrative appeals, and legal inquiries.\n\n"
            "🤖 **3. Ask the AI Assistant Directly:**\n"
            "- You can simply describe what you need in this chat (e.g., *'I want to open a shop, what license do I need?'* or *'How do I transfer ownership of my house?'*).\n"
            "- The Civic AI Assistant will immediately identify the exact department, required documents, and step-by-step application instructions!"
        )

    @classmethod
    def get_how_to_apply_text(cls, language: Optional[str] = "en") -> str:
        """Return structured step-by-step SOP on how to apply for civic services."""
        lang = (language or "en").lower().strip()
        if lang == "bn":
            return (
                "পৌর পোর্টালের মাধ্যমে নাগরিক পরিষেবার জন্য আবেদন করার ধাপসমূহ:\n\n"
                "📋 **ধাপ ১: সার্ভিস ক্যাটালগ দেখুন**\n"
                "- বামপাশের মেনু থেকে **Service Catalogue** (`/static/services.html`) পেজে যান।\n"
                "- আপনার প্রয়োজনীয় সেবা নির্বাচন করুন (যেমন: *New Water Connection, Property Tax Mutation, Trade License Renewal, Birth/Death Certificate* ইত্যাদি)।\n\n"
                "📑 **ধাপ ২: প্রয়োজনীয় নথিপত্র ও ফি যাচাই করুন**\n"
                "- পরিষেবার বিস্তারিত কার্ডে আবশ্যক নথি (JSONB), প্রক্রিয়াকরণ সময় (SLA) ও আবেদন ফি দেখে নিন।\n\n"
                "📝 **ধাপ ৩: অনলাইন আবেদন ফর্ম পূরণ করুন**\n"
                "- **'Apply Now'** বাটনে ক্লিক করে ফর্ম পূরণ করুন এবং প্রয়োজনীয় নথিপত্র আপলোড করুন।\n\n"
                "🔖 **ধাপ ৪: ট্র্যাকিং রেফারেন্স কোড সংগ্রহ করুন**\n"
                "- সাবমিট করার সাথে সাথে একটি ইউনিক ট্র্যাকিং কোড পাবেন (যেমন: `APP-2026-XXXX`)।\n\n"
                "🔍 **ধাপ ৫: স্ট্যাটাস ট্র্যাক করুন**\n"
                "- **Applications Tracker** (`/static/applications.html`) থেকে রিয়েল-টাইম অগ্রগতি পর্যবেক্ষণ করুন।"
            )
        return (
            "Here is the step-by-step procedure to apply for civic services through the CivicAI Portal:\n\n"
            "📋 **Step 1: Explore Service Catalogue**\n"
            "- Navigate to **Service Catalogue** (`/static/services.html`) from the sidebar.\n"
            "- Select your required municipal service (e.g., *New Water Connection, Property Tax Mutation, Trade License Renewal, Civil Registration, Building Plan Sanction*).\n\n"
            "📑 **Step 2: Review Eligibility & Document Requirements**\n"
            "- Review the official eligibility criteria, standard processing timeline (SLA), fees, and mandatory documents.\n\n"
            "📝 **Step 3: Complete Online Application Form**\n"
            "- Click **'Apply Now'** on the service card.\n"
            "- Enter required applicant particulars and upload mandatory verification documents.\n\n"
            "🔖 **Step 4: Receive Unique Tracking Reference**\n"
            "- Upon successful submission, you will instantly receive an alphanumeric reference code (e.g., `APP-2026-XXXX`).\n\n"
            "🔍 **Step 5: Track Application Progress**\n"
            "- Monitor real-time status and verification remarks on the **Applications Tracker** (`/static/applications.html`) page.\n\n"
            "💡 *Tip: If you want specific documentation guidelines for a particular service, ask directly (e.g., 'What documents are required for water connection?').*"
        )

    @classmethod
    def get_how_to_grievance_text(cls, language: Optional[str] = "en") -> str:
        """Return structured step-by-step SOP on how to file a grievance."""
        lang = (language or "en").lower().strip()
        if lang == "bn":
            return (
                "পৌর দপ্তরে অভিযোগ (Grievance) দায়ের করার নিয়মাবলী:\n\n"
                "📢 **ধাপ ১: গ্রিভ্যান্স পেজে যান**\n"
                "- সাইডবার থেকে **Grievance Redressal** (`/static/grievances.html`) সেকশনে যান।\n\n"
                "🏢 **ধাপ ২: সংশ্লিষ্ট বিভাগ ও বিবরণ নির্বাচন করুন**\n"
                "- অভিযোগের সাথে সম্পর্কিত মিউনিসিপ্যাল ডিপার্টমেন্ট নির্বাচন করুন এবং স্পষ্ট বিবরণ লিখুন।\n\n"
                "🎫 **ধাপ ৩: সাবমিট করে ট্র্যাকিং টিকিট নিন**\n"
                "- সাবমিট করার পর একটি ইউনিক গ্রিভ্যান্স টিকিট নম্বর পাবেন (যেমন: `GRV-2026-XXXX`)।\n\n"
                "⏳ **ধাপ ৪: নিষ্পত্তির অগ্রগতি পর্যবেক্ষণ করুন**\n"
                "- দায়িত্বপ্রাপ্ত আধিকারিক নির্দিষ্ট সময়ের মধ্যে তদন্ত করে সমাধানমূলক মন্তব্য প্রদান করবেন।"
            )
        return (
            "Here is the procedure to submit a municipal grievance or complaint:\n\n"
            "📢 **Step 1: Open Grievance Redressal**\n"
            "- Navigate to **Grievance Redressal** (`/static/grievances.html`) from the sidebar.\n\n"
            "🏢 **Step 2: Select Department & Enter Complaint**\n"
            "- Choose the responsible municipal department (e.g., *Water Supply, Solid Waste, Public Works*).\n"
            "- Enter a descriptive subject and detailed complaint particulars.\n\n"
            "🎫 **Step 3: Submit & Receive Grievance Ticket**\n"
            "- Submit the form to generate a unique tracking ticket (e.g., `GRV-2026-XXXX`).\n\n"
            "⏳ **Step 4: Department Officer Review & SLA Resolution**\n"
            "- Department officials will investigate and provide official resolution updates within the SLA timeline."
        )

    @classmethod
    def get_how_to_track_text(cls, language: Optional[str] = "en") -> str:
        """Return structured instructions on application tracking."""
        return (
            "Here is how you can track your submitted civic service applications:\n\n"
            "🔍 **Tracking Instructions:**\n"
            "1. Open **Applications Tracker** (`/static/applications.html`) from the sidebar.\n"
            "2. View all submitted applications with their real-time workflow statuses:\n"
            "   - 🟡 **Submitted / Under Review**: Scrutiny underway by municipal officers.\n"
            "   - 🟢 **Approved**: Sanction granted.\n"
            "   - 🔴 **Rejected / Clarification Needed**: Officer remarks will explain reasons.\n"
            "3. Use the search bar to look up by your unique Reference Code (e.g., `APP-2026-XXXX`)."
        )

    @classmethod
    def get_greeting_help_text(cls) -> str:
        """Return structured civic guide and capabilities."""
        return cls.GREETING_HELP_TEXT

    @classmethod
    def get_anti_guarantee_text(cls, language: Optional[str] = "en") -> str:
        """Return official guardrail anti-guarantee statement."""
        lang = (language or "en").lower().strip()
        if lang == "hi":
            return (
                "नहीं। एआई नागरिक सहायक किसी भी परिस्थिति में आवेदन स्वीकृति की गारंटी या वादा नहीं दे सकता।\n\n"
                "नागरिक सेवाओं पर आधिकारिक निर्णय निम्नलिखित के अधीन हैं:\n"
                "* **दस्तावेज़ सत्यापन**: नामित विभागीय अधिकारियों द्वारा सभी दस्तावेजों की विधिवत जांच।\n"
                "* **पात्रता एवं निरीक्षण**: नगर निगम के नियमों और स्थलीय निरीक्षण का अनुपालन।\n"
                "* **प्रशासनिक निर्णय**: अंतिम स्वीकृति या अस्वीकृति का अधिकार केवल सक्षम अधिकारियों के पास है।"
            )
        elif lang == "bn":
            return (
                "না। এআই নাগরিক সহায়ক কোনো অবস্থাতেই আবেদন মঞ্জুর বা অনুমোদনের গ্যারান্টি বা প্রতিশ্রুতি দিতে পারে না।\n\n"
                "নাগরিক পরিষেবার সিদ্ধান্তসমূহ নিম্নরূপ বিষয়ের ওপর নির্ভরশীল:\n"
                "* **নথি যাচাইকরণ**: সংশ্লিষ্ট বিভাগীয় আধিকারিকদের দ্বারা নথিপত্র পরীক্ষা।\n"
                "* **যোগ্যতা ও ক্ষেত্র পরিদর্শন**: পৌর নিয়মাবলী এবং ফিল্ড ইন্সপেকশনের সম্মতি।\n"
                "* **প্রশাসনিক সিদ্ধান্ত**: চূড়ান্ত অনুমোদন বা বাতিলের সিদ্ধান্ত কেবলমাত্র অনুমোদিত আধিকারিকদের এখতিয়ারভুক্ত।"
            )
        return cls.ANTI_GUARANTEE_TEXT

    @classmethod
    def get_standard_disclaimer(cls) -> str:
        """Return the official mandatory civic disclaimer."""
        return cls.DISCLAIMER_TEXT

    @classmethod
    def get_no_answer_text(cls) -> str:
        """Return standard no-answer response when query falls outside knowledge base."""
        return cls.NO_ANSWER_TEXT


civic_guard = CivicGuardrailService()

