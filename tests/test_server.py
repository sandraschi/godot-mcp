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
    assert "itch" in data
    assert data["itch"]["success"] is True
    assert "fleet" in data
    assert data["fleet"]["success"] is True
    assert data["fleet"]["godot_mesh_import"] is True
    assert data["fleet"]["godot_splat_import"] is False


def test_fleet_status_route(client):
    resp = client.get("/api/v1/fleet/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "exchange_root" in data


def test_fleet_exchange_status_tool(client):
    resp = client.post(
        "/api/v1/control/tool",
        json={"tool": "fleet_exchange_status", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "exchange_root" in data["data"]


def test_itch_status_route(client):
    resp = client.get("/api/v1/itch/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "butler" in data
    assert "auth" in data


def test_itch_status_tool(client):
    resp = client.post(
        "/api/v1/control/tool",
        json={"tool": "itch_status", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "butler" in data["data"]


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
