from fastapi.testclient import TestClient


def test_notification_feed_and_read_status(
    client: TestClient,
    admin_headers: dict,
    officer_headers: dict,
    citizen_headers: dict
):
    """Test that notifications are created on application submission and can be marked as read."""
    # Setup Dept & Service
    dept_res = client.post("/api/v1/departments/", headers=admin_headers, json={
        "name": "Social Welfare Department",
        "code": "SWD",
        "description": "Pensions and benefits"
    })
    dept_id = dept_res.json()["id"]

    srv_res = client.post("/api/v1/services/", headers=officer_headers, json={
        "department_id": dept_id,
        "name": "Senior Citizen Welfare Scheme",
        "code": "SWD-SC-01",
        "requirements": {"required_documents": ["Age Proof Certificate"]},
        "eligibility_criteria": {"min_age": 60},
        "processing_time_days": 10,
        "status": "active"
    })
    srv_id = srv_res.json()["id"]

    # 1. Citizen submits application -> triggers notification
    app_res = client.post("/api/v1/applications/", headers=citizen_headers, json={
        "service_id": srv_id,
        "payload": {"applicant": "Senior Citizen Demo"}
    })
    assert app_res.status_code == 201

    # 2. Citizen checks notifications feed
    notif_res = client.get("/api/v1/notifications/me", headers=citizen_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert len(notifs) >= 1
    first_notif = notifs[0]
    assert first_notif["is_read"] is False

    # 3. Mark notification as read
    read_res = client.put(f"/api/v1/notifications/{first_notif['id']}/read", headers=citizen_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True
