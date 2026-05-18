"""Integration-level tests for the godot-mcp server.

These test deep integration between components.
"""


def test_status_endpoint_with_real_server(client):
    """Status endpoint returns correct schema regardless of bridge state."""
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "godot" in data
    assert "version" in data


def test_known_tool_returns_json(client):
    """Known tool returns structured JSON even if bridge is offline."""
    resp = client.post(
        "/api/v1/control/tool",
        json={"tool": "godot_status", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    assert "tool" in data
    assert data["tool"] == "godot_status"
