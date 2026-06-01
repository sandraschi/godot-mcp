"""Tests for game_builder REST routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from godot_mcp.server import app


def test_game_builder_design_route():
    client = TestClient(app)
    mock_plan = {"title": "Test", "worlds": [], "scenes": [], "scripts": []}
    with patch(
        "godot_mcp.game_builder.service.service_design_game",
        new=AsyncMock(return_value={"success": True, "plan": mock_plan}),
    ):
        resp = client.post("/api/v1/game-builder/design", json={"game_concept": "pong clone"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_build_game_tool_dispatch():
    client = TestClient(app)
    with patch(
        "godot_mcp.game_builder.service.service_build_game",
        new=AsyncMock(return_value={"success": True, "summary": "ok"}),
    ):
        resp = client.post(
            "/api/v1/control/tool",
            json={"tool": "build_game", "arguments": {"game_concept": "runner"}},
        )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
