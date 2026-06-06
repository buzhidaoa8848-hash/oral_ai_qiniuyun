"""Test API endpoints."""

from fastapi.testclient import TestClient


def test_api_health(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_create_and_get_scene_card(client: TestClient):
    # Create
    payload = {
        "title": "Ordering Coffee",
        "difficulty": "A2",
        "topic": "Food",
        "prompt": "You are at a café. Order a latte.",
        "character_role": "Customer",
        "model_answer": "你好，我要一杯拿铁。",
        "hints": ["拿铁 = latte"],
        "tags": ["café", "ordering"],
    }
    resp = client.post("/api/scenes", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    scene_id = data["id"]
    assert data["title"] == "Ordering Coffee"
    assert data["hints"] == ["拿铁 = latte"]

    # Retrieve
    resp = client.get(f"/api/scenes/{scene_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == scene_id


def test_list_scene_cards_seeded(client: TestClient):
    """After auto-seed, there should be 4 built-in scene cards."""
    resp = client.get("/api/scenes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    titles = {s["title"] for s in data}
    assert titles == {
        "Internship Interview",
        "Restaurant Ordering",
        "Work Meeting",
        "Project Pitch Q&A",
    }


def test_create_and_get_profile(client: TestClient):
    payload = {"name": "Test User", "email": "test@example.com", "proficiency_level": "B1"}
    resp = client.post("/api/profiles", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test User"
    assert data["proficiency_level"] == "B1"


def test_profile_404(client: TestClient):
    resp = client.get("/api/profiles/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_scene_card_404(client: TestClient):
    resp = client.get("/api/scenes/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
