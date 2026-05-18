"""Shared fixtures for godot-mcp tests."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from godot_mcp.server import app

    return TestClient(app)


@pytest.fixture
def mock_bridge():
    with patch("godot_mcp.services.godot_bridge.GodotBridge") as mock:
        instance = mock.return_value
        instance.connected = True
        instance.send.return_value = {"success": True, "data": {"status": "ok"}}
        instance.connect.return_value = {"success": True, "data": {"godot_version": "4.4.0"}}
        yield instance


@pytest.fixture
def mock_bridge_disconnected():
    with patch("godot_mcp.services.godot_bridge.GodotBridge") as mock:
        instance = mock.return_value
        instance.connected = False
        instance.connect.return_value = {"success": False, "error": "Connection refused"}
        yield instance
