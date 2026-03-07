"""
Smoke test: Trust Layer (memory permissions + audit) and Tools Registry.
Runs against the FastAPI app (TestClient) so no server needed.
Flow: capture_thought -> search_memories -> set_visibility -> audit read -> tools list -> tools call.
"""

import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.core.main import app
    # App startup (on first request) inits memory DB to data/whisperleaf_memory.db
    with TestClient(app) as c:
        yield c


def test_tools_list(client):
    r = client.get("/api/tools")
    assert r.status_code == 200
    data = r.json()
    assert "tools" in data
    names = [t["name"] for t in data["tools"]]
    assert "capture_thought" in names
    assert "search_memories" in names
    assert "reflect" in names


def test_capture_thought_search_set_visibility_audit(client):
    # 1) capture_thought
    r = client.post(
        "/api/tools/call",
        json={"name": "capture_thought", "payload": {"text": "Smoke test thought", "source": "test"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    result = body.get("result", {})
    assert result.get("saved") is True
    memory_id = result.get("id")
    assert memory_id is not None

    # 2) search_memories
    r = client.post(
        "/api/tools/call",
        json={"name": "search_memories", "payload": {"limit": 5}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    entries = body.get("result", {}).get("entries", [])
    assert any(e.get("content") == "Smoke test thought" for e in entries)

    # 3) set_visibility
    r = client.post(
        f"/api/memory/{memory_id}/visibility",
        json={"visibility": "pinned"},
    )
    assert r.status_code == 200
    assert r.json().get("visibility") == "pinned"

    # 4) audit read
    r = client.get(f"/api/memory/{memory_id}/audit", params={"limit": 50})
    assert r.status_code == 200
    data = r.json()
    assert data.get("memory_id") == memory_id
    events = data.get("events", [])
    event_types = [e.get("event_type") for e in events]
    assert "created" in event_types
    assert "searched" in event_types
    assert "pinned" in event_types or "updated" in event_types

    # 5) tools list (already tested above, just ensure still works)
    r = client.get("/api/tools")
    assert r.status_code == 200
    assert len(r.json().get("tools", [])) >= 3
