from app.services.civic_guard import civic_guard


def test_sanitize_sensitive_numbers():
    """Verify Aadhaar-like 12-digit numbers are redacted."""
    text = "My identity number is 1234 5678 9012 and please process fast."
    sanitized, had_sensitive = civic_guard.sanitize_input(text)

    assert had_sensitive is True
    assert "1234 5678 9012" not in sanitized
    assert "[REDACTED-IDENTIFIER]" in sanitized


def test_sanitize_clean_input():
    """Verify clean inquiry text passes without modification."""
    text = "What is the fee for residential water connection?"
    sanitized, had_sensitive = civic_guard.sanitize_input(text)

    assert had_sensitive is False
    assert sanitized == text


def test_disclaimer_and_no_answer_strings():
    """Verify standard disclaimer and no-answer strings are populated."""
    disclaimer = civic_guard.get_standard_disclaimer()
    assert "Disclaimer" in disclaimer
    assert "legal advice" in disclaimer

    no_answer = civic_guard.get_no_answer_text()
    assert "could not find" in no_answer.lower()
