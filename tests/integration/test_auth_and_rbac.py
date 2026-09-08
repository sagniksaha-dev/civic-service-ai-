from fastapi.testclient import TestClient


def test_user_registration_and_login(client: TestClient):
    """Test public citizen registration and token authentication."""
    # Register
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Integration Citizen",
        "email": "integration_citizen@civic.local",
        "password": "Password123!",
        "role": "citizen"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == "integration_citizen@civic.local"

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "integration_citizen@civic.local",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["role"] == "citizen"

    # Profile fetch /auth/me
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Integration Citizen"


def test_rbac_admin_routes(client: TestClient, admin_headers: dict, citizen_headers: dict):
    """Test that Admin routes are accessible to Admin and forbidden (403) to Citizens."""
    # Admin accesses /users
    admin_res = client.get("/api/v1/users/", headers=admin_headers)
    assert admin_res.status_code == 200

    # Citizen accesses /users -> Forbidden
    cit_res = client.get("/api/v1/users/", headers=citizen_headers)
    assert cit_res.status_code == 403
