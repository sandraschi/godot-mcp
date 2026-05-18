"""Tests for the GodotBridge TCP client."""

from unittest.mock import patch

import pytest

from godot_mcp.services.godot_bridge import GodotBridge


@pytest.fixture
def bridge():
    return GodotBridge()


def test_disconnect_when_not_connected(bridge):
    result = bridge.disconnect()
    assert result["success"] is True
    assert result["message"] == "Not connected"


@patch("godot_mcp.services.godot_bridge.socket.socket")
def test_connect_refused(mock_socket, bridge):
    mock_socket.return_value.connect.side_effect = ConnectionRefusedError
    result = bridge.connect()
    assert result["success"] is False
    assert "Connection refused" in result["error"]
