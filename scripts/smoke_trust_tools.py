#!/usr/bin/env python3
"""
Smoke test: Trust Layer + Tools Registry.
Run with server up: python scripts/smoke_trust_tools.py
Calls: capture_thought -> search_memories -> set_visibility -> audit -> tools list -> tools call.
"""

import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"


def req(method: str, path: str, body: dict = None) -> dict:
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main():
    print("1. Tools list...")
    data = req("GET", "/api/tools")
    print("   ", [t["name"] for t in data["tools"]])
    assert "capture_thought" in [t["name"] for t in data["tools"]]

    print("2. capture_thought...")
    data = req("POST", "/api/tools/call", {"name": "capture_thought", "payload": {"text": "Smoke test thought", "source": "script"}})
    assert data.get("ok") and data.get("result", {}).get("saved")
    memory_id = data["result"]["id"]
    print("   memory_id =", memory_id)

    print("3. search_memories...")
    data = req("POST", "/api/tools/call", {"name": "search_memories", "payload": {"limit": 5}})
    assert data.get("ok")
    print("   entries =", len(data["result"]["entries"]))

    print("4. set_visibility pinned...")
    data = req("POST", f"/api/memory/{memory_id}/visibility", {"visibility": "pinned"})
    assert data.get("visibility") == "pinned"

    print("5. audit...")
    data = req("GET", f"/api/memory/{memory_id}/audit?limit=50")
    assert "events" in data
    print("   events =", [e["event_type"] for e in data["events"]])

    print("6. tools call reflect (may fail if no LLM)...")
    try:
        data = req("POST", "/api/tools/call", {"name": "reflect", "payload": {"prompt": "What matters?"}})
        print("   ", "ok" if data.get("ok") else data)
    except Exception as e:
        print("   (skipped)", e)

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
