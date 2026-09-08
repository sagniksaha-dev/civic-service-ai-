from fastapi.testclient import TestClient


def test_grievance_submission_and_resolution(
    client: TestClient,
    admin_headers: dict,
    officer_headers: dict,
    citizen_headers: dict,
    citizen_2_headers: dict
):
    """Test Grievance complaint submission, isolation, and officer resolution."""
    # Setup Dept
    dept_res = client.post("/api/v1/departments/", headers=admin_headers, json={
        "name": "Electricity & Lighting Dept",
        "code": "ELD",
        "description": "Streetlights and municipal grid"
    })
    dept_id = dept_res.json()["id"]

    # 1. Citizen 1 files grievance
    grv_res = client.post("/api/v1/grievances/", headers=citizen_headers, json={
        "department_id": dept_id,
        "subject": "Streetlight broken on 4th cross",
        "details": "The streetlamp has been flickering and went completely dark."
    })
    assert grv_res.status_code == 201
    grv_id = grv_res.json()["id"]
    assert grv_res.json()["status"] == "submitted"

    # 2. Citizen 1 can view own grievance
    get_res = client.get(f"/api/v1/grievances/{grv_id}", headers=citizen_headers)
    assert get_res.status_code == 200

    # 3. Citizen 2 CANNOT view Citizen 1 grievance
    cross_res = client.get(f"/api/v1/grievances/{grv_id}", headers=citizen_2_headers)
    assert cross_res.status_code == 403

    # 4. Officer responds and resolves
    resp_res = client.put(f"/api/v1/grievances/{grv_id}/respond", headers=officer_headers, json={
        "response": "Maintenance electrician dispatched and bulb fixture replaced.",
        "status": "resolved"
    })
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "resolved"
    assert "bulb fixture replaced" in resp_res.json()["response"]
