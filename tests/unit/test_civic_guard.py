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


def test_is_all_departments_query():
    """Verify natural variations for asking about departments are detected."""
    assert civic_guard.is_all_departments_query("say about all existing departments") is True
    assert civic_guard.is_all_departments_query("what are all existing departments") is True
    assert civic_guard.is_all_departments_query("list of departments") is True
    assert civic_guard.is_all_departments_query("tell me about available departments") is True
    assert civic_guard.is_all_departments_query("সব ডিপার্টমেন্ট") is True


def test_is_all_services_query():
    """Verify natural variations for asking about services are detected."""
    assert civic_guard.is_all_services_query("say about all existing services") is True
    assert civic_guard.is_all_services_query("what are all available services") is True
    assert civic_guard.is_all_services_query("service catalogue") is True
    assert civic_guard.is_all_services_query("সকল সার্ভিসগুলো") is True


def test_is_how_to_apply_and_procedural_queries():
    """Verify generic procedural questions are properly identified."""
    assert civic_guard.is_how_to_apply_query("how I apply") is True
    assert civic_guard.is_how_to_apply_query("how to apply") is True
    assert civic_guard.is_how_to_apply_query("how do i apply") is True
    assert civic_guard.is_how_to_apply_query("application process") is True
    assert civic_guard.is_how_to_apply_query("কীভাবে আবেদন করব") is True

    assert civic_guard.is_how_to_grievance_query("how to file a grievance") is True
    assert civic_guard.is_how_to_grievance_query("how do i complain") is True
    assert civic_guard.is_how_to_grievance_query("lodge a complaint") is True

    assert civic_guard.is_how_to_track_query("how to track") is True
    assert civic_guard.is_how_to_track_query("check application status") is True

    assert civic_guard.is_find_service_or_dept_query("How to find a service that I need or the department that will be best for me for that service") is True
    assert civic_guard.is_find_service_or_dept_query("which department is best for me") is True
    assert civic_guard.is_find_service_or_dept_query("how to find a service") is True


def test_civic_problem_queries():
    """Verify specific civic complaints and issues are correctly identified."""
    assert civic_guard.is_drainage_problem_query("There is a problem of Locality drain what service we need apply") is True
    assert civic_guard.is_drainage_problem_query("clogged sewer and drainage overflow") is True
    assert civic_guard.is_drainage_problem_query("এলাকার নালা বন্ধ") is True

    assert civic_guard.is_garbage_problem_query("garbage accumulation on street") is True
    assert civic_guard.is_road_light_problem_query("potholes in the road") is True
    assert civic_guard.is_water_problem_query("water leakage from main pipe") is True




