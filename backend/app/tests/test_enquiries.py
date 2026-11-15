from app.models import Enquiry


def test_valid_submission_saved(client, valid_payload, db_session):
    r = client.post("/api/enquiries", json=valid_payload)
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["status"] == "New"
    assert body["data"]["ai_status"] in ("pending", "processing", "completed")
    assert body["data"]["phone"] == "+919876543210"  # normalised
    saved = db_session.get(Enquiry, body["data"]["id"])
    assert saved.message == valid_payload["message"]  # original preserved


def test_missing_customer_name(client, valid_payload):
    del valid_payload["customer_name"]
    r = client.post("/api/enquiries", json=valid_payload)
    assert r.status_code == 422
    assert r.json()["success"] is False


def test_invalid_email(client, valid_payload):
    valid_payload["email"] = "not-an-email"
    assert client.post("/api/enquiries", json=valid_payload).status_code == 422


def test_invalid_phone(client, valid_payload):
    valid_payload["phone"] = "abc123"
    assert client.post("/api/enquiries", json=valid_payload).status_code == 422


def test_empty_message(client, valid_payload):
    valid_payload["message"] = "   "
    assert client.post("/api/enquiries", json=valid_payload).status_code == 422


def test_requires_email_or_phone(client, valid_payload):
    del valid_payload["email"], valid_payload["phone"]
    assert client.post("/api/enquiries", json=valid_payload).status_code == 422


def test_get_and_not_found(client, valid_payload):
    eid = client.post("/api/enquiries", json=valid_payload).json()["data"]["id"]
    assert client.get(f"/api/enquiries/{eid}").status_code == 200
    r = client.get("/api/enquiries/9999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_status_update(client, valid_payload):
    eid = client.post("/api/enquiries", json=valid_payload).json()["data"]["id"]
    r = client.put(f"/api/enquiries/{eid}/status", json={"status": "Converted"})
    assert r.status_code == 200 and r.json()["data"]["status"] == "Converted"
    assert client.put(f"/api/enquiries/{eid}/status", json={"status": "Bogus"}).status_code == 422


def test_list_pagination_search_filter(client, valid_payload):
    for i in range(3):
        p = dict(valid_payload, customer_name=f"Customer {i}", email=f"c{i}@example.com")
        client.post("/api/enquiries", json=p)
    r = client.get("/api/enquiries?page=1&page_size=2").json()
    assert len(r["data"]) == 2 and r["meta"]["total"] == 3 and r["meta"]["total_pages"] == 2
    assert client.get("/api/enquiries?search=Customer 1").json()["meta"]["total"] == 1
    assert client.get("/api/enquiries?status=Closed").json()["meta"]["total"] == 0
