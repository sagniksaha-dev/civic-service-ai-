import io
from fastapi.testclient import TestClient


def test_document_upload_and_reindexing(client: TestClient, officer_headers: dict, admin_headers: dict):
    """Test document upload, metadata indexing, reindexing, and vector cleanup."""
    doc_content = b"# Emergency Water Tanker Protocol\n\nCitizens may request emergency potable water tanker during pipeline repairs. Processing SLA is 4 hours."
    file_payload = ("emergency_water.md", io.BytesIO(doc_content), "text/markdown")

    # 1. Upload Document
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=officer_headers,
        data={"title": "Emergency Water Tanker Protocol", "category": "emergency_guideline"},
        files={"file": file_payload}
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["chunk_count"] >= 1

    # 2. List documents
    list_res = client.get("/api/v1/documents/")
    assert list_res.status_code == 200
    assert any(d["id"] == doc_id for d in list_res.json())

    # 3. Single Document Re-indexing
    reindex_res = client.post(f"/api/v1/documents/{doc_id}/reindex", headers=officer_headers)
    assert reindex_res.status_code == 200
    assert reindex_res.json()["id"] == doc_id

    # 4. Bulk Re-indexing (Admin)
    bulk_res = client.post("/api/v1/documents/reindex-all", headers=admin_headers)
    assert bulk_res.status_code == 200
    assert "reindexed_count" in bulk_res.json()

    # 5. Delete document
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=officer_headers)
    assert del_res.status_code == 200
