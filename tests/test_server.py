"""Tests for the Godot MCP server startup and configuration."""

import pytest
from fastapi.testclient import TestClient

from godot_mcp.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_status_endpoint(client):
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["service"] == "godot-mcp"
    assert "godot" in data


def test_unknown_tool_returns_400(client):
    resp = client.post(
        "/api/v1/control/tool",
        json={"tool": "nonexistent", "arguments": {}},
    )
    assert resp.status_code == 400


def test_known_tool_without_bridge(client):
    resp = client.post(
        "/api/v1/control/tool",
        json={"tool": "godot_status", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
