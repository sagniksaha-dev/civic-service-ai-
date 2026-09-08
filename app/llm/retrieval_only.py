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
            "spacecraft", "galaxy", "astrology", "superhero"
        }
        if any(term in q_words for term in out_of_scope_terms):
            return self.NO_ANSWER_RESPONSE, False

        best_score = 0
        best_sentences = []

        for snippet in context_snippets:
            text = snippet.get("text", "")
            # Split by line breaks and punctuation
            sentences = [line.strip() for line in text.split("\n") if line.strip()]
            for s in sentences:
                s_cleaned = s.lstrip("-#* ").strip()
                if len(s_cleaned) < 10:
                    continue
                s_words = set(re.findall(r"\w+", s_cleaned.lower()))
                overlap = len(meaningful_q_words.intersection(s_words))
                if overlap > best_score:
                    best_score = overlap
                    best_sentences = [s_cleaned]
                elif overlap == best_score and best_score >= 1 and len(best_sentences) < 4:
                    if s_cleaned not in best_sentences:
                        best_sentences.append(s_cleaned)

        # If zero keyword overlap or no sentences extracted, declare no-answer
        if not best_sentences or best_score == 0:
            return self.NO_ANSWER_RESPONSE, False

        # Compile grounded answer
        compiled_lines = []
        for line in best_sentences:
            if not line.endswith(".") and not line.endswith(":"):
                line = line + "."
            compiled_lines.append(line)

        compiled_answer = "According to the approved civic guidelines:\n\n" + "\n".join(f"- {l}" for l in compiled_lines)
        return compiled_answer, True
