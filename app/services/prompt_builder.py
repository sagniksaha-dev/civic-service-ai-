from typing import Optional


class PromptBuilder:
    """Constructs strict grounding prompts and system instructions for the civic assistant."""

    SYSTEM_PROMPT = """You are the official AI Civic Service & Grievance Assistant for municipal and public services.
Your role is to help citizens understand public service procedures, required documents, eligibility rules, and grievance processes based EXCLUSIVELY on approved civic documents.

STRICT GROUNDING RULES:
1. Answer ONLY based on the facts provided in the "Approved Reference Context".
2. If the context does not explicitly contain the necessary information to answer the citizen's question, you MUST reply:
   "I could not find information regarding this question in the approved civic service documents. Please contact the respective department office or submit a formal inquiry."
3. NEVER promise, guarantee, or state that an application or outcome is approved or guaranteed.
4. NEVER provide formal legal counsel or make up deadlines not present in the text.
5. Keep your answer polite, direct, and factual.
"""

    LANGUAGE_INSTRUCTIONS = {
        "en": "Respond clearly in English.",
        "hi": "कृपया हिंदी में उत्तर दें (Respond in Hindi). Ensure official civic terminology is clear.",
        "bn": "অনুগ্রহ করে বাংলায় উত্তর দিন (Respond in Bengali). Ensure official civic terminology is clear.",
    }

    @classmethod
    def get_system_prompt(cls, language: Optional[str] = "en") -> str:
        """Return the grounded system prompt with optional language instruction."""
        prompt = cls.SYSTEM_PROMPT.strip()
        lang_code = (language or "en").lower().strip()
        if lang_code in cls.LANGUAGE_INSTRUCTIONS:
            prompt += f"\n\nLanguage Instruction: {cls.LANGUAGE_INSTRUCTIONS[lang_code]}"
        return prompt


prompt_builder = PromptBuilder()
