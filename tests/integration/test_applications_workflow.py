from fastapi.testclient import TestClient


def test_service_application_workflow_and_isolation(
    client: TestClient,
    admin_headers: dict,
    officer_headers: dict,
    citizen_headers: dict,
    citizen_2_headers: dict
):
    """Test Application submission, reference generation, workflow transitions, and cross-citizen isolation."""
    # Setup Dept & Service
    dept_res = client.post("/api/v1/departments/", headers=admin_headers, json={
        "name": "Revenue Department",
        "code": "REV",
        "description": "Tax and mutation"
    })
    dept_id = dept_res.json()["id"]

    srv_res = client.post("/api/v1/services/", headers=officer_headers, json={
        "department_id": dept_id,
        "name": "Property Mutation Certificate",
        "code": "REV-MUT-01",
        "requirements": {"required_documents": ["Sale Deed Copy"]},
        "eligibility_criteria": {"min_age": 18},
        "processing_time_days": 14,
        "status": "active"
    })
    srv_id = srv_res.json()["id"]

    # 1. Citizen 1 submits Application
    app_res = client.post("/api/v1/applications/", headers=citizen_headers, json={
        "service_id": srv_id,
        "payload": {"property_id": "PLOT-9910", "applicant": "Test Citizen"}
    })
    assert app_res.status_code == 201
    app_data = app_res.json()
    app_id = app_data["id"]
    ref_no = app_data["reference_no"]

    assert ref_no.startswith("APP-")
    assert app_data["status"] == "submitted"

    # 2. Citizen 1 can access own application
    own_res = client.get(f"/api/v1/applications/{app_id}", headers=citizen_headers)
    assert own_res.status_code == 200

    # 3. Citizen 2 CANNOT access Citizen 1 application -> Forbidden 403
    cross_res = client.get(f"/api/v1/applications/{app_id}", headers=citizen_2_headers)
    assert cross_res.status_code == 403

    # 4. Privacy Guardrail: Aadhaar payload rejected
    bad_res = client.post("/api/v1/applications/", headers=citizen_headers, json={
        "service_id": srv_id,
        "payload": {"aadhaar_number": "1234-5678-9012"}
    })
    assert bad_res.status_code == 400

    # 5. Officer reviews and updates status: SUBMITTED -> UNDER_REVIEW -> APPROVED
    rev_res = client.put(f"/api/v1/applications/{app_id}/status", headers=officer_headers, json={
        "status": "under_review",
        "officer_remarks": "Verification in progress."
    })
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "under_review"

    appr_res = client.put(f"/api/v1/applications/{app_id}/status", headers=officer_headers, json={
        "status": "approved",
        "officer_remarks": "Mutation approved."
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"
