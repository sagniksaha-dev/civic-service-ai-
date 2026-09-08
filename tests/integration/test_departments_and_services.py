from fastapi.testclient import TestClient


def test_department_and_service_lifecycle(
    client: TestClient,
    admin_headers: dict,
    officer_headers: dict,
    citizen_headers: dict
):
    """Test Department and Service Catalogue creation, listing, updates, and SLA dashboard."""
    # 1. Citizen cannot create department
    cit_dept_res = client.post("/api/v1/departments/", headers=citizen_headers, json={
        "name": "Unauthorized Dept",
        "code": "UNAUTH",
        "description": "Should fail"
    })
    assert cit_dept_res.status_code == 403

    # 2. Admin creates department
    admin_dept_res = client.post("/api/v1/departments/", headers=admin_headers, json={
        "name": "Health and Sanitation Department",
        "code": "HSD",
        "description": "Municipal sanitation, health clearances and food inspections"
    })
    assert admin_dept_res.status_code == 201
    dept_id = admin_dept_res.json()["id"]

    # 3. Public lists departments
    list_dept_res = client.get("/api/v1/departments/")
    assert list_dept_res.status_code == 200
    assert any(d["code"] == "HSD" for d in list_dept_res.json())

    # 4. Officer creates Service under Department
    srv_res = client.post("/api/v1/services/", headers=officer_headers, json={
        "department_id": dept_id,
        "name": "Food Hygiene Clearance Certificate",
        "code": "HSD-FOOD-01",
        "description": "Annual hygiene inspection and clearance for restaurants",
        "requirements": {
            "required_documents": ["Kitchen Layout Plan", "Staff Medical Certificates"],
            "instructions": ["Apply online", "Pay inspection fee"],
            "fee_amount": 1200.0
        },
        "eligibility_criteria": {"min_age": 18, "residency_required": True},
        "processing_time_days": 10,
        "status": "active"
    })
    assert srv_res.status_code == 201
    srv_id = srv_res.json()["id"]

    # 5. Public reads Service details
    get_srv_res = client.get(f"/api/v1/services/{srv_id}")
    assert get_srv_res.status_code == 200
    assert get_srv_res.json()["name"] == "Food Hygiene Clearance Certificate"
    assert "Kitchen Layout Plan" in get_srv_res.json()["requirements"]["required_documents"]

    # 6. Officer SLA Dashboard Metrics
    sla_res = client.get("/api/v1/services/stats/sla-dashboard", headers=officer_headers)
    assert sla_res.status_code == 200
    sla_data = sla_res.json()
    assert sla_data["total_services"] >= 1
    assert "applications_by_status" in sla_data
    assert "application_resolution_rate_pct" in sla_data
