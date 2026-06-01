"""Tests for fleet-standard activity log API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from godot_mcp.server import app


def test_logs_api_query_export_clear():
    client = TestClient(app)
    from godot_mcp.services.activity_log import clear_logs, log_activity

    clear_logs()
    log_activity("tool_call", "godot_status (ok)", level="INFO", meta={"tool": "godot_status"})
    log_activity("server", "test boot", level="INFO")

    logs = client.get("/api/logs?limit=10&kind=tool_call").json()
    assert logs["total"] >= 1
    assert logs["entries"][0]["kind"] == "tool_call"

    stats = client.get("/api/logs/stats").json()
    assert stats["rotation"] == "ring_buffer"
    assert stats["total"] >= 2

    export = client.get("/api/logs/export?format=json&kind=tool_call")
    assert export.status_code == 200
    assert "tool_call" in export.text

    cleared = client.delete("/api/logs")
    assert cleared.json()["success"] is True
    assert client.get("/api/logs/stats").json()["total"] == 1
