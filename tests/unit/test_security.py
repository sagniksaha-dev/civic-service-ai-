from datetime import timedelta
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    """Verify that password hashing produces valid hashes and verifies correctly."""
    plain = "SuperSecretPassword123!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decoding():
    """Verify that JWT tokens encode subject, role, and decode cleanly."""
    subject = "42"
    role = "citizen"
    token = create_access_token(subject=subject, role=role, extra_claims={"name": "John"})

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "42"
    assert payload.get("role") == "citizen"
    assert payload.get("name") == "John"


def test_expired_jwt_token():
    """Verify that expired JWT tokens fail to decode."""
    token = create_access_token(
        subject="42",
        role="citizen",
        expires_delta=timedelta(seconds=-10)
    )
    payload = decode_access_token(token)
    assert payload is None
