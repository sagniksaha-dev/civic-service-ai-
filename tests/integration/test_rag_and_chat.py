from fastapi.testclient import TestClient


def test_rag_grounding_and_chat_sessions(client: TestClient, citizen_headers: dict):
    """Test RAG query answering, citation metadata, disclaimers, and WebSocket interaction."""
    # 1. Ask a supported inquiry
    res1 = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "What documents are required for a water connection?"
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert "answer" in data1
    assert "disclaimer" in data1
    assert "session_id" in data1
    assert data1["is_grounded"] is True
    assert len(data1["sources"]) > 0

    # 2. Ask a greeting / help inquiry
    res_greet = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "hi"
    })
    assert res_greet.status_code == 200
    greet_data = res_greet.json()
    assert "Civic Service & Grievance Assistant" in greet_data["answer"]
    assert "disclaimer" in greet_data

    # 2b. Ask about all existing departments
    res_depts = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "say about all existing departments"
    })
    assert res_depts.status_code == 200
    dept_data = res_depts.json()
    assert dept_data["is_grounded"] is True
    assert "directory of all" in dept_data["answer"].lower()
    assert len(dept_data["sources"]) > 0

    # 2c. Ask how to apply
    res_apply = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "how I apply"
    })
    assert res_apply.status_code == 200
    apply_data = res_apply.json()
    assert apply_data["is_grounded"] is True
    assert "step-by-step procedure" in apply_data["answer"].lower()
    assert len(apply_data["sources"]) > 0

    # 2d. Ask how to find a service or department
    res_find = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "How to find a service that I need or the department that will be best for me for that service"
    })
    assert res_find.status_code == 200
    find_data = res_find.json()
    assert find_data["is_grounded"] is True
    assert "find the right civic service" in find_data["answer"].lower()
    assert len(find_data["sources"]) > 0

    # 2e. Ask about a specific locality drain problem
    res_drain = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "There is a problem of Locality drain what service we need apply"
    })
    assert res_drain.status_code == 200
    drain_data = res_drain.json()
    assert drain_data["is_grounded"] is True
    assert "drainage problem" in drain_data["answer"].lower() or "grievance" in drain_data["answer"].lower()
    assert len(drain_data["sources"]) > 0





    # 3. Ask an unindexed inquiry
    res2 = client.post("/api/v1/chat/query", headers=citizen_headers, json={
        "question": "How do I register a galactic starship on Jupiter?"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_grounded"] is False
    assert "could not find" in data2["answer"].lower() or "no information" in data2["answer"].lower()

    # 3. Test Session message lookup
    session_id = data1["session_id"]
    sess_res = client.get(f"/api/v1/chat/sessions/{session_id}", headers=citizen_headers)
    assert sess_res.status_code == 200
    assert len(sess_res.json()["messages"]) >= 1

    # 4. WebSocket test
    with client.websocket_connect("/ws/chat") as ws:
        init_evt = ws.receive_json()
        assert init_evt["type"] == "connected"

        ws.send_json({
            "type": "message",
            "question": "What is the processing time for water connection?"
        })

        t_evt = ws.receive_json()
        assert t_evt["type"] == "typing"

        ans_evt = ws.receive_json()
        assert ans_evt["type"] == "answer"
        assert "answer" in ans_evt
        assert len(ans_evt.get("sources", [])) > 0
