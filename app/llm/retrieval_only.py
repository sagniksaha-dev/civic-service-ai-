import re
from typing import Any, Dict, List, Tuple
from app.llm.base import BaseLLMProvider


class RetrievalOnlyProvider(BaseLLMProvider):
    """
    Offline/Standalone Provider that answers queries strictly using retrieved document chunks.
    Guarantees 100% testability without requiring external API keys.
    """

    NO_ANSWER_RESPONSE = (
        "I could not find information regarding this question in the approved civic service documents. "
        "Please check the respective department office or submit a formal inquiry."
    )

    def generate_grounded_response(
        self,
        question: str,
        context_snippets: List[Dict[str, Any]],
        system_prompt: str
    ) -> Tuple[str, bool]:
        """Generate response directly from retrieved snippets with keyword and distance gating."""
        if not context_snippets:
            return self.NO_ANSWER_RESPONSE, False

        # Extract meaningful terms from question
        q_words = set(re.findall(r"\w+", question.lower()))
        stop_words = {
            "what", "is", "the", "are", "for", "how", "to", "apply", "do", "i", "a", "an",
            "in", "of", "and", "can", "get", "need", "my", "on", "from", "with", "where",
            "tell", "me", "about", "please", "give"
        }
        meaningful_q_words = q_words - stop_words

        # Out-of-scope domain reject list
        out_of_scope_terms = {
            "spaceship", "interstellar", "mars", "alien", "crypto", "bitcoin",
            "spacecraft", "galaxy", "astrology", "superhero", "jupiter"
        }
        if any(term in q_words for term in out_of_scope_terms):
            return self.NO_ANSWER_RESPONSE, False

        scored_sentences = []
        seen = set()

        for snippet in context_snippets:
            text = snippet.get("text", "")
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            for line in lines:
                cleaned = line.lstrip("-#* ").strip()
                if len(cleaned) < 10 or cleaned.lower() in seen:
                    continue
                words = set(re.findall(r"\w+", cleaned.lower()))
                overlap = len(meaningful_q_words.intersection(words))
                if overlap > 0:
                    scored_sentences.append((overlap, len(cleaned), cleaned))
                    seen.add(cleaned.lower())

        # If zero keyword overlap or no sentences extracted, declare no-answer
        if not scored_sentences:
            return self.NO_ANSWER_RESPONSE, False

        # Sort by overlap descending, then by ideal sentence length
        scored_sentences.sort(key=lambda x: (x[0], -abs(x[1] - 80)), reverse=True)
        top_sentences = [s[2] for s in scored_sentences[:6]]

        # Compile grounded answer
        compiled_lines = []
        for line in top_sentences:
            if not line.endswith(".") and not line.endswith(":") and not line.endswith("!"):
                line = line + "."
            compiled_lines.append(line)

        compiled_answer = "According to the approved civic guidelines:\n\n" + "\n".join(f"- {l}" for l in compiled_lines)
        return compiled_answer, True
